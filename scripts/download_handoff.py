"""Interactive read-only retrieval of B's DVC objects, without storing credentials.

Run this yourself in an interactive terminal. The assistant never receives the token.
This bootstrap utility does not replace the required DVC/Azure workflow.
"""

import base64
import getpass
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath

import yaml

REMOTE = "https://dagshub.com/hanss0090/sms-spam-classifier.dvc"


def download():
    username = input("Your DagsHub username: ").strip()
    token = getpass.getpass("DagsHub access token (hidden, not stored): ")
    auth = "Basic " + base64.b64encode(f"{username}:{token}".encode()).decode()

    def read_object(digest):
        if not re.fullmatch(r"[0-9a-f]{32}(?:\.dir)?", digest):
            raise ValueError("Invalid DVC object ID")
        for prefix in ("/files/md5/", "/"):
            url = REMOTE + prefix + digest[:2] + "/" + digest[2:]
            request = urllib.request.Request(url, headers={"Authorization": auth})
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    data = response.read()
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    continue
                raise RuntimeError(f"DVC download rejected (HTTP {exc.code})") from None
            if hashlib.md5(data, usedforsecurity=False).hexdigest() != digest.removesuffix(".dir"):
                raise ValueError("DVC content checksum mismatch")
            return data
        raise RuntimeError("DVC object not found; ask B to verify dvc push")

    plans = [
        ("models/release.dvc", Path("models/release")),
        ("data/v1.dvc", Path("data/v1")),
        ("data/v2.dvc", Path("data/v2")),
    ]
    for pointer, destination in plans:
        descriptor = yaml.safe_load(Path(pointer).read_text(encoding="utf-8"))
        directory_hash = descriptor["outs"][0]["md5"]
        if not directory_hash.endswith(".dir"):
            raise ValueError("Expected directory DVC pointer")
        manifest = json.loads(read_object(directory_hash))
        for entry in manifest:
            relative = PurePosixPath(entry["relpath"])
            if relative.is_absolute() or ".." in relative.parts or "\\" in str(relative):
                raise ValueError("Unsafe path in remote manifest")
            target = destination.joinpath(*relative.parts).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError("Object escapes destination")
            data = read_object(entry["md5"])
            if target.exists() and target.read_bytes() != data:
                raise RuntimeError(f"Refusing to overwrite changed file: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            print("Verified:", target.relative_to(Path.cwd()))
    print("B handoff downloaded and DVC MD5 verified. No credentials were saved.")


if __name__ == "__main__":
    download()
