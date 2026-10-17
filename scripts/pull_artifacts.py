"""Configure credentials locally in the ephemeral runner, then pull explicit pointers."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def dvc(*args):
    result = subprocess.run([sys.executable, "-m", "dvc", *args])
    if result.returncode:
        # Never include arguments containing credentials in an exception traceback.
        raise RuntimeError("DVC operation failed; check remote access and configuration")


def pull(include_data=False):
    remote = os.environ.get("DVC_REMOTE", "")
    if not remote:
        raise RuntimeError("Set DVC_REMOTE to the team-approved remote name")
    if not Path(".dvc/config").is_file():
        raise RuntimeError("B must supply the committed .dvc/config")
    if os.environ.get("DAGSHUB_TOKEN"):
        username = os.environ.get("DAGSHUB_USERNAME")
        if not username:
            raise RuntimeError("DAGSHUB_USERNAME is required")
        dvc("remote", "modify", "--local", remote, "auth", "basic")
        dvc("remote", "modify", "--local", remote, "user", username)
        dvc("remote", "modify", "--local", remote, "password", os.environ["DAGSHUB_TOKEN"])
    elif os.environ.get("AZURE_SAS_TOKEN"):
        account = os.environ.get("AZURE_STORAGE_ACCOUNT")
        if not account:
            raise RuntimeError("AZURE_STORAGE_ACCOUNT is required")
        dvc("remote", "modify", "--local", remote, "account_name", account)
        dvc("remote", "modify", "--local", remote, "sas_token", os.environ["AZURE_SAS_TOKEN"])
    pointers = ["models/release.dvc"]
    if include_data:
        pointers += ["data/v1.dvc", "data/v2.dvc"]
    if not all(Path(p).is_file() for p in pointers):
        raise RuntimeError("Missing B handoff DVC pointer files")
    dvc("pull", *pointers, "-r", remote)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-data", action="store_true")
    pull(parser.parse_args().include_data)
