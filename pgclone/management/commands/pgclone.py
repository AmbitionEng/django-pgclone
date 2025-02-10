import sys
from typing import Any

from django.core.management.base import BaseCommand

from pgclone import copy_cmd, dump_cmd, exceptions, logging, ls_cmd, restore_cmd


class Subcommands(BaseCommand):
    """
    Subcommand class vendored in from
    https://github.com/andrewp-as-is/django-subcommands.py
    because of installation issues
    """

    argv: list[str] = []
    subcommands = {}

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="subcommand", title="subcommands", description="")
        subparsers.required = True

        for command_name, command_class in self.subcommands.items():
            command = command_class()

            subparser = subparsers.add_parser(command_name, help=command_class.help)
            command.add_arguments(subparser)

            command_parser = command.create_parser("manage.py", "pgclone")
            subparser._actions = command_parser._actions

    def run_from_argv(self, argv):  # pragma: no cover
        self.argv = argv
        return super().run_from_argv(argv)

    def handle(self, *args, **options):
        command_name = options["subcommand"]
        self.subcommands.get(command_name)
        if command_name not in self.subcommands:  # pragma: no cover
            raise ValueError(f"unknown subcommand: {command_name}")
        command_class = self.subcommands[command_name]

        if len(self.argv):  # pragma: no cover
            args = [self.argv[0]] + self.argv[2:]
            return command_class().run_from_argv(args)
        return command_class().execute(*args, **options)


class BaseSubcommand(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> Any:
        try:
            logger = logging.new_stdout_logger()
            with logging.set_logger(logger):
                return self.subhandle(*args, **options)  # type: ignore - missing from stubs
        except exceptions.Error as exc:
            self.stderr.write(str(exc))
            sys.exit(1)


class LsCommand(BaseSubcommand):
    def add_arguments(self, parser):
        parser.add_argument("dump_key", nargs="?")
        parser.add_argument("--instances", action="store_true", help="Only list instances.")
        parser.add_argument("--databases", action="store_true", help="Only list databases.")
        parser.add_argument("--configs", action="store_true", help="Only list configs.")
        parser.add_argument("--local", action="store_true", help="Only list local restore keys.")
        parser.add_argument(
            "-d",
            "--database",
            help="The database to use when listing local restore keys.",
        )
        parser.add_argument(
            "-s",
            "--storage-location",
            help="Use this storage location for listing.",
        )
        parser.add_argument(
            "-c",
            "--config",
            help="Use this configuration to supply default option values.",
        )

    def subhandle(self, *args, **options):
        results = ls_cmd.ls(
            dump_key=options["dump_key"],
            instances=options["instances"],
            databases=options["databases"],
            configs=options["configs"],
            local=options["local"],
            database=options["database"],
            storage_location=options["storage_location"],
            config=options["config"],
        )
        for dump_name in results:
            sys.stdout.write(dump_name + "\n")


class DumpCommand(BaseSubcommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "-e", "--exclude", nargs="*", help="Model(s) you wish to exclude when dumping."
        )
        parser.add_argument(
            "--pre-dump-hook",
            nargs="*",
            dest="pre_dump_hooks",
            help=(
                "Management command(s) that will be executed on"
                " the database before it is dumped."
            ),
        )
        parser.add_argument("-i", "--instance", help="Use this instance name in the dump key.")
        parser.add_argument(
            "-d",
            "--database",
            help="Dump this database.",
        )
        parser.add_argument(
            "-s",
            "--storage-location",
            help="Dump to this storage location.",
        )
        parser.add_argument(
            "-c",
            "--config",
            help="Use this configuration to supply default option values.",
        )

    def subhandle(self, *args, **options):
        dump_cmd.dump(
            exclude=options["exclude"],
            pre_dump_hooks=options["pre_dump_hooks"],
            instance=options["instance"],
            database=options["database"],
            storage_location=options["storage_location"],
            config=options["config"],
        )


class RestoreCommand(BaseSubcommand):
    def add_arguments(self, parser):
        parser.add_argument("dump_key", nargs="?", help="The dump key (or prefix) to restore.")
        parser.add_argument(
            "--pre-swap-hook",
            nargs="*",
            dest="pre_swap_hooks",
            help=(
                "Management command(s) that will be executed on"
                " the restored database before it is swapped to the"
                " primary database."
            ),
        )
        parser.add_argument(
            "-r",
            "--reversible",
            default=None,  # Use None so that configs/settings can be used as defaults
            action="store_true",
            help="Keep pre/post restore database copies available for reversion.",
        )
        parser.add_argument(
            "-d",
            "--database",
            help="Restore to this database.",
        )
        parser.add_argument(
            "-s",
            "--storage-location",
            help="Restore from this storage location.",
        )
        parser.add_argument(
            "-c",
            "--config",
            help="Use this configuration to supply default option values.",
        )

    def subhandle(self, *args, **options):
        restore_cmd.restore(
            dump_key=options["dump_key"],
            pre_swap_hooks=options["pre_swap_hooks"],
            reversible=options["reversible"],
            database=options["database"],
            storage_location=options["storage_location"],
            config=options["config"],
        )


class CopyCommand(BaseSubcommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "dump_key",
            help="The database target in the format of a local dump key, e.g. ':db_backup'",
        )
        parser.add_argument(
            "-d",
            "--database",
            help="Copy this database.",
        )
        parser.add_argument(
            "-c",
            "--config",
            help="Use this configuration to supply default option values.",
        )

    def subhandle(self, *args, **options):
        copy_cmd.copy(
            dump_key=options["dump_key"],
            database=options["database"],
            config=options["config"],
        )


class Command(Subcommands):
    subcommands = {
        "ls": LsCommand,
        "dump": DumpCommand,
        "restore": RestoreCommand,
        "copy": CopyCommand,
    }
