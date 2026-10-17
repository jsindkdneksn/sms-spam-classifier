"""Configure credentials locally in the ephemeral runner, then pull explicit pointers."""

import argparse
import configparser
import os
import subprocess
import sys
from pathlib import Path


def dvc(*args):
    # Storage SDK errors can include signed URLs. Keep raw output out of public CI logs.
    result = subprocess.run([sys.executable, "-m", "dvc", *args], capture_output=True)
    if result.returncode:
        # Never include arguments containing credentials in an exception traceback.
        raise RuntimeError("DVC operation failed; check remote access and configuration")


def pull(include_data=False):
    remote = os.environ.get("DVC_REMOTE", "")
    if not remote:
        raise RuntimeError("Set DVC_REMOTE to the team-approved remote name")
    if not Path(".dvc/config").is_file():
        raise RuntimeError("B must supply the committed .dvc/config")
    config = configparser.ConfigParser(interpolation=None)
    config.read([".dvc/config", ".dvc/config.local"], encoding="utf-8")
    section = next(
        (name for name in config.sections() if name.strip("'") == f'remote "{remote}"'),
        f'remote "{remote}"',
    )
    url = config.get(section, "url", fallback="")
    if not url:
        raise RuntimeError("Selected DVC remote is not configured")
    if url.startswith("azure://"):
        if os.environ.get("AZURE_SAS_TOKEN"):
            account = os.environ.get("AZURE_STORAGE_ACCOUNT")
            if not account:
                raise RuntimeError("AZURE_STORAGE_ACCOUNT is required")
            dvc("remote", "modify", "--local", remote, "account_name", account)
            dvc("remote", "modify", "--local", remote, "sas_token", os.environ["AZURE_SAS_TOKEN"])
    elif url.startswith("https://dagshub.com/") and os.environ.get("DAGSHUB_TOKEN"):
        username = os.environ.get("DAGSHUB_USERNAME")
        if not username:
            raise RuntimeError("DAGSHUB_USERNAME is required")
        dvc("remote", "modify", "--local", remote, "auth", "basic")
        dvc("remote", "modify", "--local", remote, "user", username)
        dvc("remote", "modify", "--local", remote, "password", os.environ["DAGSHUB_TOKEN"])
    pointers = ["models/release.dvc"]
    if include_data:
        pointers += ["data/v1.dvc", "data/v2.dvc"]
    if not all(Path(p).is_file() for p in pointers):
        raise RuntimeError("Missing B handoff DVC pointer files")
    dvc("pull", *pointers, "-r", remote)
    print("DVC artifact download completed from the selected remote.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-data", action="store_true")
    pull(parser.parse_args().include_data)
