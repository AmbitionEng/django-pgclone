from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, TypeVar

from pgclone import exceptions, settings

if TYPE_CHECKING:
    from typing_extensions import Unpack

_T = TypeVar("_T")


def _first_non_none(*values: _T | None) -> _T | None:
    return next((value for value in values if value is not None), None)


class _PGCloneOptions(TypedDict, total=False):
    config: str | None
    dump_key: str | None
    reversible: bool | None
    exclude: list[str] | None
    pre_dump_hooks: list[str] | None
    pre_swap_hooks: list[str] | None
    instance: str | None
    database: str | None
    storage_location: str | None


class _Options:
    def __init__(self, **pgclone_options: "Unpack[_PGCloneOptions]") -> None:
        """Parse options for pgclone commands

        Options follow the hierarchy of:

        1. Settings are the default
        2. Any configurations override settings
        3. Any direct parameters override configurations
        """
        config = pgclone_options.get("config")
        reversible = pgclone_options.get("reversible")
        exclude = pgclone_options.get("exclude")
        pre_dump_hooks = pgclone_options.get("pre_dump_hooks")
        pre_swap_hooks = pgclone_options.get("pre_swap_hooks")

        if config and config not in settings.configs():
            raise exceptions.ValueError(
                f'"{config}" is not a valid configuration in settings.PGCLONE_CONFIGS.'
            )

        config_opts = settings.configs()[config] if config else {}

        # exlude and hooks alter the result, so we label this a "none"
        # config even if it starts from a pre-defined config
        if (
            not config
            or exclude is not None
            or pre_dump_hooks is not None
            or pre_swap_hooks is not None
        ):
            config = "none"

        # Generate options based on hierarchy
        self.dump_key = pgclone_options.get("dump_key") or config_opts.get("dump_key")
        self.instance = (
            pgclone_options.get("instance") or config_opts.get("instance") or settings.instance()
        )
        self.database = (
            pgclone_options.get("database") or config_opts.get("database") or settings.database()
        )
        self.storage_location = (
            pgclone_options.get("storage_location")
            or config_opts.get("storage_location")
            or settings.storage_location()
        )
        self.reversible = (
            _first_non_none(reversible, config_opts.get("reversible"), settings.reversible())
            or False
        )
        self.pre_dump_hooks = (
            _first_non_none(
                pre_dump_hooks, config_opts.get("pre_dump_hooks"), settings.pre_dump_hooks()
            )
            or []
        )
        self.pre_swap_hooks = (
            _first_non_none(
                pre_swap_hooks, config_opts.get("pre_swap_hooks"), settings.pre_swap_hooks()
            )
            or []
        )
        self.exclude = (
            _first_non_none(exclude, config_opts.get("exclude"), settings.exclude()) or []
        )
        self.config = config


def get(**kwargs: "Unpack[_PGCloneOptions]") -> _Options:
    return _Options(**kwargs)
