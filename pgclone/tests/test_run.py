import subprocess
from unittest.mock import patch

from pgclone import run


def test_is_pipefail_supported():
    with patch("subprocess.check_call", autospec=True, return_value=0):
        assert run._is_pipefail_supported() is True

    with patch(
        "subprocess.check_call",
        side_effect=subprocess.CalledProcessError(1, "cmd"),
        autospec=True,
    ):
        assert run._is_pipefail_supported() is False
