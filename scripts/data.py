#!/usr/bin/env python3
"""Import selected measurements from the local test archive and verify them."""

import csv
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "manifest.csv"
FIELDS = ("path", "source", "source_sha256", "sha256", "bytes", "changed")
OMIT = {"hf-tree.json", "tokenize-response.json", "production-v1-models.json",
        "production-final-v1-models.json"}
HOME = re.compile(r"/(?:var/)?home/[^/\s\"']+")
LEAK = re.compile(HOME.pattern + r"|Bearer\s+\S+|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}", re.I)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def selected(path):
    name = path.name
    if name in OMIT or name.endswith(("-request.json", "-prompt.json")):
        # The long-context files also contain a response and are reduced below.
        return name.startswith("context-") and path.parent.name.endswith("longtest")
    return path.suffix in {".json", ".ndjson", ".png", ".sha256"}


def clean(value):
    if isinstance(value, str):
        return HOME.sub("<HOME>", value)
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    return value


def import_data(source):
    source = source.resolve()
    if not source.is_dir() or not (source / "qwen-gsq-mtp-nasone32-20260927").is_dir():
        raise ValueError("Pass the raw/ directory of the consolidated test archive")
    if any(RAW.rglob("*")):
        raise ValueError("data/raw is populated; import is intentionally one-shot")
    rows = []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or not selected(path):
            continue
        relative = path.relative_to(source)
        original = path.read_bytes()
        if path.suffix == ".json":
            obj = json.loads(original)
            if path.parent.name.endswith("longtest") and path.name.endswith("-prompt.json"):
                obj.pop("request", None)
                obj.pop("prompt", None)
            output = json.dumps(clean(obj), ensure_ascii=False, indent=2).encode() + b"\n"
        elif path.suffix in {".ndjson", ".sha256"}:
            output = HOME.sub("<HOME>", original.decode()).encode()
        else:
            output = original
        if path.suffix != ".png" and LEAK.search(output.decode()):
            raise ValueError(f"Possible private data in {relative}")
        target = RAW / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
        rows.append((str(Path("data/raw") / relative), str(relative), digest(original),
                     digest(output), len(output), original != output))
    with MANIFEST.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(FIELDS)
        writer.writerows(rows)
    print(f"Imported {len(rows)} files")


def check():
    with MANIFEST.open(newline="") as file:
        reader = csv.DictReader(file)
        assert tuple(reader.fieldnames) == FIELDS
        rows = list(reader)
    assert rows and len({row["path"] for row in rows}) == len(rows)
    actual = {p.relative_to(ROOT).as_posix() for p in RAW.rglob("*") if p.is_file()}
    assert actual == {row["path"] for row in rows}, "Manifest/file mismatch"
    for row in rows:
        path = ROOT / row["path"]
        assert path.resolve().is_relative_to(RAW.resolve())
        data = path.read_bytes()
        assert len(data) == int(row["bytes"]) and digest(data) == row["sha256"], path
        if path.suffix == ".json":
            json.loads(data)
        elif path.suffix == ".ndjson":
            for line in data.splitlines():
                json.loads(line)
        if path.suffix != ".png":
            assert not LEAK.search(data.decode()), path
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        assert path.suffix not in {".gguf", ".pyc", ".log"}, path
        if path.suffix in {".md", ".py", ".csv"} and path != MANIFEST:
            assert not LEAK.search(path.read_text()), path
    print(f"Verified {len(rows)} files and repository text")


if __name__ == "__main__":
    if sys.argv[1:] == ["check"]:
        check()
    elif len(sys.argv) == 3 and sys.argv[1] == "import":
        import_data(Path(sys.argv[2]))
    else:
        raise SystemExit("Usage: python scripts/data.py import <archive/raw> | check")
