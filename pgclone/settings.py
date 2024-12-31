from __future__ import annotations

import functools
import socket
from typing import Any

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from pgclone import exceptions


def statement_timeout() -> int | None:
    return getattr(settings, "PGCLONE_STATEMENT_TIMEOUT", None)


def lock_timeout() -> int | None:
    return getattr(settings, "PGCLONE_LOCK_TIMEOUT", None)


def s3_config() -> dict[str, Any]:
    return getattr(settings, "PGCLONE_S3_CONFIG", {})


def s3_endpoint_url() -> str | None:
    return getattr(settings, "PGCLONE_S3_ENDPOINT_URL", None)


def storage_location() -> str:
    location = getattr(settings, "PGCLONE_STORAGE_LOCATION", ".pgclone")
    if not location.endswith("/"):  # pragma: no cover
        location += "/"
    return location


def reversible() -> bool:
    return getattr(settings, "PGCLONE_REVERSIBLE", False)


def allow_restore() -> bool:
    return getattr(settings, "PGCLONE_ALLOW_RESTORE", True)


def allow_dump() -> bool:
    return getattr(settings, "PGCLONE_ALLOW_DUMP", True)


def allow_copy() -> bool:
    return getattr(settings, "PGCLONE_ALLOW_COPY", True)


def configs() -> dict[str, Any]:
    return getattr(settings, "PGCLONE_CONFIGS", {})


def validate_dump_keys() -> bool:
    return getattr(settings, "PGCLONE_VALIDATE_DUMP_KEYS", True)


def instance() -> str:
    return getattr(settings, "PGCLONE_INSTANCE", socket.gethostname())


def database() -> str:
    return getattr(settings, "PGCLONE_DATABASE", DEFAULT_DB_ALIAS)


def pre_dump_hooks() -> list[str]:
    return getattr(settings, "PGCLONE_PRE_DUMP_HOOKS", [])


def pre_swap_hooks() -> list[str]:
    return getattr(settings, "PGCLONE_PRE_SWAP_HOOKS", ["migrate"])


def exclude() -> list[str]:
    return getattr(settings, "PGCLONE_EXCLUDE", [])


@functools.lru_cache()
def conn_db() -> str:
    conn_db = getattr(settings, "PGCLONE_CONN_DB", None)
    db_names = [db.get("NAME") for db in settings.DATABASES.values()]

    if not conn_db:
        if "postgres" not in db_names:
            conn_db = "postgres"
        elif "template1" not in db_names:
            conn_db = "template1"

    if not conn_db or conn_db in db_names:
        raise exceptions.RuntimeError(
            "pgclone could not automatically determine a connection database."
            " Configure settings.PGCLONE_CONN_DB with a database name that can"
            " be used when running psql commands."
        )

    return conn_db
