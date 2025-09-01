from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
from typing import Any

from django.core.management import call_command

from pgclone import exceptions, logging


def _is_pipefail_supported() -> bool:
    """Check if the current shell supports pipefail."""
    if sys.platform == "win32":  # pragma: no cover
        return False

    try:
        current_shell = os.environ.get("SHELL", "/bin/sh")
        subprocess.check_call([current_shell, "-c", "set -o pipefail"], stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def shell(
    cmd: str,
    ignore_errors: bool = False,
    env: dict[str, Any] | None = None,
    pipefail: bool = False,
) -> subprocess.Popen:
    """
    Utility for running a command. Ensures that an error
    is raised if it fails.
    """
    executable: str | None = None
    if pipefail and _is_pipefail_supported():  # pragma: no cover
        cmd = f"set -o pipefail; {cmd}"
        # If requested and supported by the user's shell, enable pipefail and
        # execute using that shell rather than the system default /bin/sh to
        # ensure the pipefail is supported.
        executable = os.environ.get("SHELL", "/bin/sh")

    env = env or {}
    logger = logging.get_logger()
    process = subprocess.Popen(
        cmd,
        shell=True,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        executable=executable,
        env=dict(os.environ, **{k: v for k, v in env.items() if v is not None}),
    )
    readline = process.stdout.readline if process.stdout else (lambda: b"")  # pragma: no branch
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
