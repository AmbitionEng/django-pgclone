from __future__ import annotations

import contextlib
import io
import os
import subprocess
from typing import Any

from django.core.management import call_command

from pgclone import exceptions, logging


def shell(
    cmd: str,
    ignore_errors: bool = False,
    env: dict[str, Any] | None = None,
) -> subprocess.Popen:
    """
    Utility for running a command. Ensures that an error
    is raised if it fails.
    """
    env = env or {}
    logger = logging.get_logger()
    process = subprocess.Popen(
        cmd,
        shell=True,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        env=dict(os.environ, **{k: v for k, v in env.items() if v is not None}),
    )
    readline = process.stdout.readline if process.stdout else (lambda: b"")
    for line in iter(readline, b""):
        logger.info(line.decode("utf-8").rstrip())
    process.wait()

    if process.returncode and not ignore_errors:
        # Dont print the command since it might contain
        # sensitive information
        raise exceptions.RuntimeError("Error running command.")

    return process


def management(
    cmd: str,
    *cmd_args: Any,
    **cmd_kwargs: Any,
) -> None:
    logger = logging.get_logger()
    cmd_args = cmd_args or ()
    cmd_kwargs = cmd_kwargs or {}
    output = io.StringIO()
    try:
        with contextlib.redirect_stderr(output):
            with contextlib.redirect_stdout(output):
                call_command(cmd, *cmd_args, **cmd_kwargs)
    except Exception:  # pragma: no cover
        # If an exception happened, be sure to print off any stdout/stderr
        # leading up the error and log the exception.
        logger.info(output.getvalue())
        logger.exception('An exception occurred during "manage.py %s"', cmd)
        raise
    else:
        logger.info(output.getvalue())
