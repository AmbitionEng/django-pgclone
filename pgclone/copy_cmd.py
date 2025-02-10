from __future__ import annotations

from pgclone import db, exceptions, logging, options, settings


def _copy(*, dump_key: str, database: str) -> str:
    """
    Copy implementation
    """
    if not settings.allow_copy():  # pragma: no cover
        raise exceptions.RuntimeError("Copy not allowed.")

    source_db = db.conf(using=database)

    if not dump_key.startswith(":"):  # pragma: no cover
        raise exceptions.ValueError('Copy target must start with ":"')
    elif dump_key in (":pre", ":post"):  # pragma: no cover
        raise exceptions.ValueError(
            ":pre and :post are reserved names. Please use a different copy target name."
        )

    target_db_name = dump_key[1:]
    target_db = db.make(target_db_name, using=database, check=False)

    if source_db == target_db:  # pragma: no cover
        raise exceptions.RuntimeError("Target database cannot be the same as source database.")

    logging.success_msg("Creating copy")
    db.drop(target_db, using=database)
    copy_db_sql = f'CREATE DATABASE "{target_db["NAME"]}" WITH TEMPLATE "{source_db["NAME"]}"'
    db.psql(copy_db_sql, using=database, kill_connections=source_db)

    logging.success_msg(f'Successfully copied database "{database}" to "{dump_key}"')

    return dump_key


def copy(dump_key: str, *, database: str | None = None, config: str | None = None) -> str:
    """
    Copies a database using `CREATE DATABASE <dump_key> TEMPLATE <database>`.

    Note that we use dump keys with the same syntax that `dump` and `restore`
    commands take. Since `copy` only works with local database copies, this
    means the dump keys are always the database name prefixed with `:`.

    Args:
        dump_key: A name to use for the copy. Must be prefixed with `:` and only
            consist of valid database name characters.
        database: The database to copy.
        config: The configuration name from `settings.PGCLONE_CONFIGS`.

    Returns:
        The dump key that was copied.
    """
    opts = options.get(
        dump_key=dump_key,
        config=config,
        database=database,
    )

    return _copy(dump_key=opts.dump_key, database=opts.database)  # type: ignore - TODO address
