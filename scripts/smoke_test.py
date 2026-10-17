"""Bounded readiness polling followed by a real HTTP prediction."""

import argparse
import json
import time
import urllib.error
import urllib.request


def smoke(base_url: str, timeout: float):
    deadline = time.monotonic() + timeout
    while True:
        try:
            with urllib.request.urlopen(base_url + "/health", timeout=2) as response:
                health = json.load(response)
            if health.get("status") == "ok":
                break
        except (OSError, ValueError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("Service did not become healthy before deadline")
        time.sleep(0.5)
    request = urllib.request.Request(
        base_url + "/predict",
        data=json.dumps({"text": "Free prize call now"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        prediction = json.load(response)
    assert prediction["label"] in {"ham", "spam"}
    assert 0 <= prediction["spam_probability"] <= 1
    assert prediction["model_version"] == health["model_version"]
    with urllib.request.urlopen(base_url + "/", timeout=5) as response:
        assert b"SMS" in response.read()
    print(json.dumps({"health": health, "prediction": prediction}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    smoke(args.url.rstrip("/"), args.timeout)
