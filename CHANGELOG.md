# Changelog

## 3.8.0 (2025-11-30)

#### Changes

  - Drop Python 3.9 support, add Python 3.14 support, add Postgres 18 support, add Django 6.0 support by [@wesleykendall](https://github.com/wesleykendall) in [#43](https://github.com/AmbitionEng/django-pgclone/pull/43)

## 3.7.1 (2025-09-02)

#### Fixes

  - Use proper `SHELL` variable when running pgclone commands by [@max-muoto](https://github.com/max-muoto) in [#41](https://github.com/AmbitionEng/django-pgclone/pull/41).

## 3.7.0 (2025-02-11)

#### Changes

  - Add type safety by [@max-muoto](https://github.com/max-muoto) in [#37](https://github.com/AmbitionEng/django-pgclone/pull/37).
  - Avoid hidden failures when dumping by [@max-muoto](https://github.com/max-muoto) in [#38](https://github.com/AmbitionEng/django-pgclone/pull/38).

## 3.6.1 (2024-12-15)

#### Changes

  - Changed project ownership to `AmbitionEng` by [@wesleykendall](https://github.com/wesleykendall) in [#36](https://github.com/AmbitionEng/django-pgclone/pull/36).

## 3.6.0 (2024-11-01)

#### Changes

  - Added Python 3.13 support, dropped Python 3.8. Added Postgres17 support by [@wesleykendall](https://github.com/wesleykendall) in [#35](https://github.com/Opus10/django-pgclone/pull/35).

## 3.5.0 (2024-08-25)

#### Changes

  - Django 5.1 compatibility, dropped Django 3.2 / Postgres 12 support by [@wesleykendall](https://github.com/wesleykendall) in [#34](https://github.com/Opus10/django-pgclone/pull/34).

## 3.4.1 (2024-04-06)

#### Trivial

  - Fix ReadTheDocs builds. [Wesley Kendall, d5eeaed]

## 3.4.0 (2023-12-06)

#### Bug

  - Fix issue quoting URLs [Wesley Kendall, ace6561]

    Ensure that URLs are percent-encoded when running psql commands.

## 3.3.0 (2023-11-26)

#### Feature

  - Django 5.0 compatibility [Wesley Kendall, cd279dd]

    Support and test against Django 5 with psycopg2 and psycopg3.

## 3.2.1 (2023-10-09)

#### Trivial

  - Added Opus10 branding to docs [Wesley Kendall, ba4621f]

## 3.2.0 (2023-10-08)

#### Feature

  - Add Python3.12 support and use Mkdocs for documentation [Wesley Kendall, 97e7d99]

    Python 3.12 and Postgres 16 are supported now, along with having revamped docs using Mkdocs
    and the Material theme.

    Python 3.7 support was dropped.

## 3.1.0 (2023-06-08)

#### Feature

  - Added Python 3.11, Django 4.2, and Psycopg 3 support [Wesley Kendall, d1cf98c]

    Adds Python 3.11, Django 4.2, and Psycopg 3 support along with tests for multiple Postgres versions. Drops support for Django 2.2.

## 3.0.0 (2023-06-01)

#### Api-Break

  - Changed behavior of reversible restores and local copies [Wes Kendall, de428c1]

    Using the ``--reversible`` option for ``pgclone restore`` is now only applicable to
    database dumps and no longer has any effect when executed against a local database.
    The aliases used by reversible restores have also changed from ``previous`` and
    ``current`` to ``pre`` and ``post``.

    In other words, if one uses ``--reversible`` during a ``pgclone restore`` of
    a database dump, one can revert back to the version of data pre-restore using
    ``pgclone restore :pre`` or the version of the data immediately after
    the restore using ``pgclone restore :post``.

    Unlike before, running ``pgclone restore :pre`` or ``pgclone restore :post`` has
    no effect on the copies created when restoring a dump using ``--reversible``.
    The ``:pre`` and ``:post`` aliases are only changed when a new reversible dump
    is restored.

    This same behavior applies to local copies too. ``pclone copy`` now requires
    a target name in the format of a local dump key (``:db_name``), and the special
    ``:pre`` and ``:post`` aliases cannot be used. Users can do
    ``pgclone copy :my_backup`` and ``pgclone restore :my_backup`` without affecting
    the special snapshots related to the last restore from a dump.

## 2.6.0 (2023-06-01)

#### Feature

  - Support overriding Postgres statement timeouts [Wes Kendall, 4ef38f4]

    Use ``settings.PGCLONE_STATEMENT_TIMEOUT`` to override Postgres's
    ``statement_timeout`` setting when running core ``pgclone`` SQL operations such
    as ``CREATE DATABASE``.

    You can also use ``settings.PGCLONE_LOCK_TIMEOUT`` to override Postgres's
    ``lock_timeout`` setting.

## 2.5.0 (2023-05-23)

#### Feature

  - Add ``pgclone copy`` command. [Wes Kendall, 6ad17b9]

    The ``pgclone copy`` command is a shortcut for running ``CREATE DATABASE <target> TEMPLATE <source>``
    for doing quick copies. This command complements local ``pgclone restore`` commands.

    For example, copy the current database with ``pgclone copy``, and quickly restore it with
    ``pgclone restore :current``. Use a custom name with ``pgclone copy :custom_name`` and restore it
    with ``pgclone restore :custom_name``.

    Note that this command takes out an exclusive lock on the source database, meaning it should not be
    executed in production environments.
  - Add ``settings.PGCLONE_ALLOW_DUMP`` setting. [Wes Kendall, 82c90f4]

    Set this setting to ``False`` to prevent the ability to run ``pgclone dump``.

#### Trivial

  - Add ability to specify endpoint url [Jack Linke, 2e1e5f5]

## 2.4.0 (2023-04-28)

#### Bug

  - Quote database connection strings [Wesley Kendall, 31fd3cf]

    Database connection strings are properly quoted to avoid issues when there
    are special characters.

#### Trivial

  - Updated developer utilities with the latest Django library template [Wesley Kendall, 2508920]

## 2.3.3 (2022-09-03)

#### Trivial

  - Implemented a more robust routing method for pre-swap hooks [Wes Kendall, 8f34c40]

## 2.3.2 (2022-08-27)

#### Trivial

  - Local development enhancements [Wes Kendall, 5d62570]
  - Test against Django 4.1 and other CI improvements [Wes Kendall, c11c848]

## 2.3.1 (2022-08-25)

#### Trivial

  - Don't close original connection during routing [Wes Kendall, 93e5c03]

## 2.3.0 (2022-08-25)

#### Bug

  - Fix issue routing connections during restore [Wes Kendall, 2ab5552]

    An issue was fixed that prevented routing hooks during restores from
    functioning properly.

## 2.2.0 (2022-08-25)

#### Bug

  - Restore command properly overrides storage location [Wes Kendall, 15acd90]

    The restore command now properly passes through custom storage locations from the
    command line.

## 2.1.0 (2022-08-24)

#### Bug

  - Allow "reversible" to proliferate through settings and configs. [Wes Kendall, bda7b69]

    The ``pgclone restore`` command was setting ``reversible`` to
    ``False``, negating settings or configs that overrode it. This
    has been fixed.

## 2.0.1 (2022-08-24)

#### Trivial

  - Update with latest Django template [Wes Kendall, c46d7e4]
  - Fix ReadTheDocs builds [Wes Kendall, 7c74338]

## 2.0.0 (2022-08-24)

#### Api-Break

  - Upgrade configuration hierarchy, add multi-db support, and change dump key format [Wes Kendall, 5edeeb8]

    ``django-pgclone`` has ``settings.PGCLONE_CONFIGS`` to support re-usable command
    options. Dump keys were changed to capture the config and also contain a configurable
    database instance to better distinguish different databases.

    Multi-database setups are fully supported.

    Docs were revamped and overview all settings and configuration possibilities.

    Instructions for migrating to version 2 are in the "Frequently Asked Questions" section of
    the docs.

## 1.1.0 (2022-08-21)

#### Feature

  - Removed dependency on ``django-pgconnection`` [Wes Kendall, 5047031]

    The routing functionality of ``django-pgconnection`` was replaced by
    Django's built-in execution hooks.

    Users no longer have to wrap ``settings.DATABASES`` with
    ``django-pgconnection``.

## 1.0.5 (2022-08-20)

#### Trivial

  - Updated with latest Django template [Wes Kendall, 5ab9ddd]

## 1.0.4 (2022-08-20)

#### Trivial

  - Fix release note rendering and don't package tests [Wes Kendall, 5621de7]

## 1.0.3 (2022-07-31)

#### Trivial

  - Updated with latest Django template, fixing doc builds [Wes Kendall, 32a5eea]

## 1.0.2 (2021-06-15)

#### Trivial

  - Updated to latest Django template [Wes Kendall, cf4deaf]

## 1.0.1 (2020-06-28)

#### Trivial

  - Fixed minor documentation typos [Wes Kendall, 68cb863]

## 1.0.0 (2020-06-28)

#### Api-Break

  - Initial release of django-pgclone [Wes Kendall, b8419ce]

    ``django-pgclone`` provides management commands for dumping and restoring
    Postgres databases. Users can configure local or S3 storage backends,
    and users may also configure hooks and other processes that happen during
    the dump/restore process.
