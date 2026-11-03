"""Download the optional specification files and verify their recorded hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    manifest = Path(__file__).resolve().parents[1] / "tests" / "sources.json"
    args.destination.mkdir(parents=True, exist_ok=True)
    for source in json.loads(manifest.read_text(encoding="utf-8")):
        with urllib.request.urlopen(source["url"], timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise RuntimeError(f"Source changed: {source['name']}; review the manifest")
        (args.destination / source["name"]).write_bytes(data)
        print(source["name"])


if __name__ == "__main__":
    main()
