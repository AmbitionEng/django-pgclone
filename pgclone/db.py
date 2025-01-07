from __future__ import annotations

import contextlib
import copy
import functools
import shlex
import tempfile
import textwrap
import urllib.parse
from collections.abc import Generator
from typing import Any

from django.conf import settings as django_settings
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.utils import load_backend

from pgclone import exceptions, run, settings


def _no_queries_during_routing(execute, sql, params, many, context):  # pragma: no cover
    alias = context["connection"].alias
    raise RuntimeError(f'Cannot query non-default database "{alias}" during pgclone hooks')


@contextlib.contextmanager
def route(destination: dict[str, Any]) -> Generator[None]:
    """
    Route all connections to another database.

    Args:
        destination (dict): Database configuration dictionary to be routed.
        using (str): The source database to use when
            routing to another database. Defaults to the default database.
    """
    with contextlib.ExitStack() as stack:
        # Protect every connection from being queried
        for alias in connections:
            stack.enter_context(connections[alias].execute_wrapper(_no_queries_during_routing))

        # Swap the default and routed connection. Note: the connections object is thread safe
        default_connection = connections[DEFAULT_DB_ALIAS]
        connections[DEFAULT_DB_ALIAS] = load_backend(destination["ENGINE"]).DatabaseWrapper(
            destination, DEFAULT_DB_ALIAS
        )

        try:
            yield
        finally:
            connections[DEFAULT_DB_ALIAS].close()
            connections[DEFAULT_DB_ALIAS] = default_connection


def conf(*, using: str) -> dict[str, Any]:
    """Obtain a copy of a database configuration"""
    if using not in django_settings.DATABASES:  # pragma: no cover
        raise exceptions.ValueError(
            f'"{using}" is not a valid database. Use one from settings.DATABASES.'
        )

    # Deep copy to ensure the caller doesn't modify this django setting
    database = copy.deepcopy(django_settings.DATABASES[using])

    # Set the same defaults as Django so that it works with routing. This
    # is copied directly from
    # https://github.com/django/django/blob/c8eb9a7c451f7935a9eaafbb195acf2aa9fa867d/django/db/utils.py#L160
    database.setdefault("ATOMIC_REQUESTS", False)
    database.setdefault("AUTOCOMMIT", True)
    database.setdefault("ENGINE", "django.db.backends.dummy")
    if database["ENGINE"] == "django.db.backends." or not database["ENGINE"]:  # pragma: no cover
        database["ENGINE"] = "django.db.backends.dummy"

    database.setdefault("CONN_MAX_AGE", 0)
    database.setdefault("OPTIONS", {})
    database.setdefault("TIME_ZONE", None)
    for setting in ["NAME", "USER", "PASSWORD", "HOST", "PORT"]:
        database.setdefault(setting, "")

    return database


def make(db_name: str, *, using: str, check: bool = True) -> dict[str, Any]:
    """Returns a DB config dict for the database named "db_name"

    Also ensures that no other database are configured with the provided
    database name. This is a sanity check to make sure that no dynamic
    databases used by pgclone collide with any that already exist.

    Note: In a multi-DB setup, this check might produce errors that don't
    need to happen, such as restricting one from using a name on an
    entirely different DB. We can handle this edge case later
    """
    if check:
        for db in django_settings.DATABASES.values():
            if db.get("NAME") == db_name:  # pragma: no cover
                raise exceptions.RuntimeError(
                    f'pgclone cannot use temporary database named "{db_name}"'
                    " since it is already configured in settings.DATABASES."
                )

    db_config = conf(using=using)
    db_config["NAME"] = db_name
    return db_config


@functools.lru_cache()
def conn(*, using: str) -> dict[str, Any]:
    """Return the database used when making connections to psql"""
    return make(settings.conn_db(), using=using)


def url(db_config: dict[str, Any]) -> str:
    """Convert a database dictionary config to a url"""
    user = urllib.parse.quote(db_config["USER"])
    password = urllib.parse.quote(db_config["PASSWORD"])
    host = urllib.parse.quote(db_config["HOST"])
    port = urllib.parse.quote(str(db_config["PORT"]))
    name = urllib.parse.quote(db_config["NAME"])
    return shlex.quote(f"postgresql://{user}:{password}@{host}:{port}/{name}")


def _fmt_psql_sql(sql: str) -> str:
    """Formats SQL for psql execution"""
    sql = textwrap.dedent(sql).strip()
    if not sql.endswith(";"):  # For better debugging output
        sql += ";"

    if settings.statement_timeout() is not None:
        sql = f"SET statement_timeout = {settings.statement_timeout()};\n{sql}"

    if settings.lock_timeout() is not None:
        sql = f"SET lock_timeout = {settings.lock_timeout()};\n{sql}"

    return sql


def _kill_connections(database: dict[str, Any], *, using: str) -> None:
    kill_connections_sql = f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{database["NAME"]}' AND pid <> pg_backend_pid()
    """
    psql(kill_connections_sql, using=using)


def psql(
    sql: str,
    *,
    using: str,
    ignore_errors: bool = False,
    kill_connections: dict[str, Any] | None = None,
):
    """Runs psql -f with properly formatted SQL.

    Ensures PGCLONE_STATEMENT_TIMEOUT and PGCLONE_LOCK_TIMEOUT are set
    if those parameters are defined.
    """
    if kill_connections:
        _kill_connections(kill_connections, using=using)

    db_url = url(conn(using=using))
    sql = _fmt_psql_sql(sql)

    # psql -c will run all statements in one transaction, which causes errors when using
    # setting overrides for some commands that cannot be executed in a transaction. In order
    # to get around this, we use the -f option to read statements from a file. Executing them
    # this way ensures that the statements are executed in the same session and no transaction
    with tempfile.NamedTemporaryFile() as tmp_f:
        tmp_f.write(sql.encode("utf-8"))
        tmp_f.flush()

        return run.shell(
            f"psql {db_url} -o /dev/null -a -v ON_ERROR_STOP=1 -P pager=off -f {tmp_f.name}",
            ignore_errors=ignore_errors,
        )


def drop(database: dict[str, Any], *, using: str) -> None:
    _kill_connections(database, using=using)
    drop_sql = f'DROP DATABASE IF EXISTS "{database["NAME"]}"'
    psql(drop_sql, using=using)
