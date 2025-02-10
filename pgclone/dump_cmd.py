from __future__ import annotations

import datetime as dt
import os
import re

from django.apps import apps

from pgclone import db, exceptions, logging, options, run, settings, storage

DT_FORMAT = "%Y-%m-%d-%H-%M-%S-%f"


def _dump_key(*, instance: str, database: str, config: str) -> str:
    """Obtain the key for the db dump"""
    now = dt.datetime.now(dt.timezone.utc).strftime(DT_FORMAT)
    instance = re.sub(r"[^a-zA-Z0-9_-]", "_", instance)
    database = re.sub(r"[^a-zA-Z0-9_-]", "_", database)
    config_name = re.sub(r"[^a-zA-Z0-9_-]", "_", config)
    return os.path.join(instance, database, config_name, f"{now}.dump")


def _dump(
    *,
    exclude: list[str],
    config: str,
    pre_dump_hooks: list[str],
    instance: str,
    database: str,
    storage_location: str,
) -> str:
    """Dump implementation"""
    if not settings.allow_dump():  # pragma: no cover
        raise exceptions.RuntimeError("Dump not allowed.")

    storage_client = storage.client(storage_location)
    dump_db = db.conf(using=database)

    # pre-dump hooks
    with db.route(dump_db):
        for management_command_name in pre_dump_hooks:  # pragma: no cover
            logging.success_msg(f'Running "manage.py {management_command_name}" pre_dump hook')
            run.management(management_command_name)

    # Run the pg dump command that streams to the storage location
    dump_key = _dump_key(config=config, instance=instance, database=database)
    file_path = os.path.join(storage_location, dump_key)

    exclude_tables = [apps.get_model(model)._meta.db_table for model in exclude]
    exclude_args = " ".join(
        [f"--exclude-table-data={table_name}" for table_name in exclude_tables]
    )
    # Note - do note format {db_dump_url} with an `f` string.
    # It will be formatted later when running the command.
    pg_dump_cmd_fmt = "pg_dump -Fc --no-acl --no-owner {db_dump_url} " + exclude_args
    pg_dump_cmd_fmt += " " + storage_client.pg_dump(file_path)

    anon_pg_dump_cmd = pg_dump_cmd_fmt.format(db_dump_url="<DB_URL>")
    logging.success_msg(f"Creating DB copy with cmd: {anon_pg_dump_cmd}")

    pg_dump_cmd = pg_dump_cmd_fmt.format(db_dump_url=db.url(dump_db))
    run.shell(pg_dump_cmd, env=storage_client.env, pipefail=True)

    logging.success_msg(f'Database "{database}" successfully dumped to "{dump_key}"')

    return dump_key


def dump(
    *,
    exclude: list[str] | None = None,
    pre_dump_hooks: list[str] | None = None,
    instance: str | None = None,
    database: str | None = None,
    storage_location: str | None = None,
    config: str | None = None,
) -> str:
    """Dumps a database.

    Args:
        exclude: The models to exclude when dumping the utils.
        pre_dump_hooks: A list of management command names to run before dumping the utils.
        instance: The instance name to use in the dump key.
        database: The database to dump.
        storage_location: The storage location to store dumps.
        config: The configuration name from `settings.PGCLONE_CONFIGS`.

    Returns:
        The dump key associated with the database dump.
    """
    opts = options.get(
        exclude=exclude,
        config=config,
        pre_dump_hooks=pre_dump_hooks,
        instance=instance,
        database=database,
        storage_location=storage_location,
    )

    return _dump(
        exclude=opts.exclude,
        config=opts.config,
        pre_dump_hooks=opts.pre_dump_hooks,
        instance=opts.instance,
        database=opts.database,
        storage_location=opts.storage_location,
    )
