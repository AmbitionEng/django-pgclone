from __future__ import annotations

import abc
import os
import pathlib
import subprocess
from typing import Any

from pgclone import exceptions, settings


def validate_s3_support() -> None:  # pragma: no cover
    """Verify that pgclone has been installed with the S3 extras"""
    which_aws = subprocess.run(
        "which aws", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if which_aws.returncode != 0:
        raise exceptions.RuntimeError(
            "You must install the AWS command line tool in order to enable S3 support."
            ' Run "pip install awscli" or follow these instructions -'
            " https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        )


class _Storage(abc.ABC):
    def __init__(self, storage_location: str) -> None:
        # Ensure the storage location always has a slash appended
        self.storage_location = os.path.join(storage_location, "")
        self.env = self.get_env()

    def get_env(self) -> dict[str, Any]:
        return {}

    def dump_key(self, path: str) -> str:
        """
        Given an absolute path, return the relative path (i.e. the dump key)
        """
        prefix_len = len(self.storage_location)
        return path[prefix_len:]

    @abc.abstractmethod
    def pg_dump(self, file_path: str) -> str:
        """Given a file path, generates the CLI fragment to append to pg_dump"""
        pass

    @abc.abstractmethod
    def pg_restore(self, file_path: str) -> str:
        """Given a file path, generates the CLI fragment to prepend to pg_restore"""
        pass

    @abc.abstractmethod
    def ls(self, prefix: str | None = None) -> list[str]:
        """Given a prefix, returns a list of dump keys"""
        pass


class S3(_Storage):
    def __init__(self, storage_location: str):
        validate_s3_support()
        self.s3_endpoint_url = (
            f" --endpoint-url {settings.s3_endpoint_url()}"
            if settings.s3_endpoint_url() is not None
            and isinstance(settings.s3_endpoint_url(), str)
            else ""
        )
        super().__init__(storage_location)

    def ls(self, prefix: str | None = None) -> list[str]:  # pragma: no cover
        s3_path = os.path.join(self.storage_location, prefix or "")
        s3_bucket = "s3://" + s3_path[5:].split("/", 1)[0]
        cmd = f"aws s3 ls {s3_path}{self.s3_endpoint_url} --recursive | cut -c32-"
        process = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, check=True, env=dict(os.environ, **self.env)
        )
        abs_paths = [
            os.path.join(s3_bucket, path)
            for path in process.stdout.decode("utf-8").split("\n")
            if path
        ]
        return [self.dump_key(path) for path in abs_paths]

    def get_env(self):
        return settings.s3_config()

    def pg_dump(self, file_path: str) -> str:
        return f"| aws s3 cp - {file_path}{self.s3_endpoint_url}"

    def pg_restore(self, file_path: str) -> str:
        return f"aws s3 cp {file_path} -{self.s3_endpoint_url} |"


class Local(_Storage):
    def ls(self, prefix: str | None = None) -> list[str]:
        abs_paths = [
            os.path.join(dirpath, file_name)
            for dirpath, _, file_names in os.walk(self.storage_location)
            for file_name in file_names
        ]
        dump_keys = [self.dump_key(path) for path in abs_paths]

        if prefix:
            dump_keys = [dump_key for dump_key in dump_keys if dump_key.startswith(prefix)]

        return dump_keys

    def pg_dump(self, file_path: str) -> str:
        pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        return f"> {file_path}"

    def pg_restore(self, file_path: str) -> str:
        return f"cat {file_path} |"


def client(storage_location: str) -> _Storage:
    if storage_location.startswith("s3://"):  # pragma: no cover
        return S3(storage_location)
    else:
        return Local(storage_location)
