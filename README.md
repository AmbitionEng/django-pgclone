# django-pgclone

`django-pgclone` makes it easy to dump and restore Postgres databases.
Here are some key features:

1. Streaming dumps and restores to configurable storage backends like S3. Instances with limited memory aren't a problem for large databases.
2. A restoration process that works behind the scenes, swapping in the restored database when finished.
3. Configurable hooks into the dump and restore process, for example, migrating a restored database before it is swapped.
4. Reversible restores, making it possible to quickly revert to the initial restore or the previous database.
5. Re-usable configurations for instrumenting different types of dumps and restores.

## Quickstart

To dump a database, do:

    python manage.py pgclone dump

To list database dump keys, do:

    python manage.py pgclone ls

To restore a datase, do:

    python manage.py pgclone restore <dump_key>

Database dumps are relative to the storage location, which defaults to the local file system. Dump keys are in the format of `<instance>/<database>/<config>/<timestamp>.dump`.

When listing, use an optional prefix. Restoring supports the same interface, using the latest key that matches the prefix.

## Documentation

[View the django-pgclone docs here](https://django-pgclone.readthedocs.io/) to learn more about:

* The basics and an overview of how it works.
* The core command docs.
* Configuring an S3 storage backend.
* Running management command hooks during dumping or restoring.
* Creating restores that can be quickly reverted.
* Re-using command parameters for different flows.
* All settings.
* Additional details on using AWS RDS databases.

## Compatibility

`django-pgclone` is compatible with Python 3.10 - 3.14, Django 4.2 - 6.0, Psycopg 2 - 3, and Postgres 14 - 18.

## Installation

Install `django-pgclone` with:

    pip3 install django-pgclone

After this, add `pgclone` to the `INSTALLED_APPS` setting of your Django project.

**Note**  Install the AWS CLI to enable the S3 storage backend. Use `pip install awscli` or follow the [installation guide here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

## Contributing Guide

For information on setting up `django-pgclone` for development and contributing changes, view [CONTRIBUTING.md](CONTRIBUTING.md).

## Primary Authors

- @wesleykendall (Wes Kendall)
- @ethanpobrien (Ethan O'Brien)
