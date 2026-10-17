"""Interactive upload and independent download verification of the Azure DVC remote."""

import configparser
import getpass
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

POINTERS = ["data/v1.dvc", "data/v2.dvc", "models/release.dvc"]
FILES = [
    *(
        f"data/{version}/{split}.csv"
        for version in ("v1", "v2")
        for split in ("train", "val", "test")
    ),
    "models/release/model.joblib",
    "models/release/metadata.json",
]


def run_dvc(root, *args):
    # Do not print SDK errors, which can contain signed URLs.
    result = subprocess.run(
        [sys.executable, "-m", "dvc", *args],
        cwd=root,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        env={**os.environ, "DVC_SITE_CACHE_DIR": str(root / ".dvc-site-cache")},
    )
    if result.returncode:
        raise RuntimeError("Azure DVC operation failed; check SAS permissions, expiry and network")


def write_credentials(path, token):
    config = configparser.ConfigParser(interpolation=None)
    if path.exists():
        config.read(path, encoding="utf-8")
    section = next(
        (name for name in config.sections() if name.strip("'") == 'remote "myazure"'),
        'remote "myazure"',
    )
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, "sas_token", token)
    with path.open("w", encoding="utf-8") as stream:
        config.write(stream)


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path.cwd()
    if not all((root / path).is_file() for path in POINTERS + FILES):
        raise RuntimeError("Run from project root after downloading B's complete handoff")
    token = (
        getpass.getpass("Azure SAS token (hidden; local configuration only): ").strip().lstrip("?")
    )
    if not token or "sig=" not in token or "://" in token:
        raise ValueError("Enter the SAS query token, not a URL")
    local = root / ".dvc/config.local"
    write_credentials(local, token)
    print(
        "Local credential configured. Populating DVC cache from verified local files...", flush=True
    )
    pointers_before = {path: (root / path).read_bytes() for path in POINTERS}
    run_dvc(root, "commit", *POINTERS)
    if any((root / path).read_bytes() != value for path, value in pointers_before.items()):
        for path, value in pointers_before.items():
            (root / path).write_bytes(value)
        raise RuntimeError(
            "DVC pointers changed; restored originals. Check the local handoff first"
        )
    print("Uploading both datasets and release model...", flush=True)
    run_dvc(root, "push", *POINTERS, "-r", "myazure")
    print("Upload completed. Checking download with an empty independent cache...", flush=True)
    expected = {path: checksum(root / path) for path in FILES}
    work = root / "work"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="azure-check-", dir=work) as folder:
        clean = Path(folder)
        (clean / ".dvc").mkdir()
        config = configparser.ConfigParser(interpolation=None)
        config.read(root / ".dvc/config", encoding="utf-8")
        if not config.has_section("core"):
            config.add_section("core")
        config.set("core", "no_scm", "true")
        # Never reuse a configured shared cache: this must exercise Azure downloads.
        if config.has_section("cache"):
            config.remove_section("cache")
        with (clean / ".dvc/config").open("w", encoding="utf-8") as stream:
            config.write(stream)
        for pointer in POINTERS:
            target = clean / pointer
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / pointer, target)
        write_credentials(clean / ".dvc/config.local", token)
        try:
            run_dvc(clean, "pull", *POINTERS, "-r", "myazure")
            for path, digest in expected.items():
                if checksum(clean / path) != digest:
                    raise RuntimeError(f"Downloaded content differs: {path}")
                print(f"Verified: {path}", flush=True)
        finally:
            (clean / ".dvc/config.local").unlink(missing_ok=True)
    report = {
        "remote": "myazure",
        "upload": "passed",
        "empty_cache_download": "passed",
        "sha256": expected,
    }
    (work / "azure-verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Azure upload and independent download verified. Report: work/azure-verification.json")
    print("SAS remains only in ignored .dvc/config.local. Never commit or share it.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
