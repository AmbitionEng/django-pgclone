from __future__ import annotations

import re
import subprocess
from typing import Any

from pgclone import db, exceptions, options, settings, storage


def _is_valid_dump_key(dump_key: str) -> bool:
    """
    True if the `dump_key` is in the valid format of
    "database_name/timestamp.dump"
    """
    regexmatch = re.match(
        r"^[\w-]+/[\w-]+/[\w-]+/\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d+\.dump$",
        dump_key,
    )
    return bool(regexmatch) if settings.validate_dump_keys() else True


def _parse_dump_key(dump_key: str) -> dict[str, Any] | None:
    regexmatch = re.match(
        r"^(?P<instance>[\w-]+)/(?P<database>[\w-]+)/(?P<config>[\w-]+)/"
        r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d+\.dump$",
        dump_key,
    )
    return regexmatch.groupdict() if regexmatch else None


def _ls(
    *,
    dump_key: str | None,
    instances: bool,
    databases: bool,
    configs: bool,
    local: bool,
    database: str | None,
    storage_location: str,
    config: str | None,
) -> list[str]:
    """
    Ls implementation
    """
    if sum([local, instances, databases, configs]) > 1:
        raise exceptions.ValueError(
            'Can only use one of "instances", "databases", "configs", or "local".'
        )

    storage_client = storage.client(storage_location)

    if local:
        conn_db_url = db.url(db.conn(using=database))
        cmd = f"psql {conn_db_url} -lqt | cut -d \\| -f 1"
        stdout = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE).stdout.decode()

        return [f":{db_name.strip()}" for db_name in stdout.split("\n") if db_name.strip()]

    dump_keys = [
        dump_key for dump_key in storage_client.ls(prefix=dump_key) if _is_valid_dump_key(dump_key)
    ]

    if instances or databases or configs:
        parsed_dump_keys = [_parse_dump_key(dump_key) for dump_key in dump_keys]
        if instances:
            return sorted({dump_key["instance"] for dump_key in parsed_dump_keys if dump_key})
        elif databases:
            return sorted({dump_key["database"] for dump_key in parsed_dump_keys if dump_key})
        elif configs:
            return sorted({dump_key["config"] for dump_key in parsed_dump_keys if dump_key})
        else:
            raise AssertionError
    else:
        return sorted(dump_keys, reverse=True)


def ls(
    dump_key: str | None = None,
    *,
    instances: bool = False,
    databases: bool = False,
    configs: bool = False,
    local: bool = False,
    database: str | None = None,
    storage_location: str | None = None,
    config: str | None = None,
) -> list[str]:
    """
    Lists dump keys.

    Args:
        dump_key: Filter by this dump key prefix.
        instances: Lists only the unique instances associated with the dump keys.
        databases: Lists only the unique databases associated with the dump keys.
        configs: Lists only the unique configs associated with the dump keys.
        local: Only list local restore keys.
        database: The database to restore.
        storage_location: The storage location to use for the restore.
        config: The configuration name from `settings.PGCLONE_CONFIGS`.

    Returns:
        The list of dump keys.
    """
    opts = options.get(
        dump_key=dump_key, config=config, database=database, storage_location=storage_location
    )

    return _ls(
        dump_key=opts.dump_key,
        config=opts.config,
        database=opts.database,
        storage_location=opts.storage_location,
        instances=instances,
        databases=databases,
        configs=configs,
        local=local,
    )
