#!/usr/bin/env python3
"""Merge all per-job .yml files and import them in a single macromog call."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent.resolve()
BACKUP_DIR = SCRIPT_DIR / "macromog_backups"


def merge_ymls(paths: list[Path]) -> dict:
    merged_books = {}
    all_selections = []

    for path in paths:
        with open(path) as f:
            data = yaml.safe_load(f)
        merged_books.update(data.get("books", {}))
        all_selections.extend(data.get("scope", {}).get("selections", []))

    return {
        "version": 1,
        "scope": {
            "level": "book",
            "selections": all_selections,
        },
        "books": merged_books,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Merge all macro .yml files and import via macromog"
    )
    parser.add_argument("char_name", help="Character name as configured in macromog")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate and show what would be written without writing")
    parser.add_argument("--no-backup", action="store_true",
                        help="skip the pre-import backup (merged YAML will not be saved)")
    args = parser.parse_args()

    yml_files = sorted(SCRIPT_DIR.glob("*.yml"))
    if not yml_files:
        print(f"No .yml files found in {SCRIPT_DIR}", file=sys.stderr)
        sys.exit(1)

    print(f"Merging {len(yml_files)} files...")
    merged = merge_ymls(yml_files)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", prefix="ffxi_macros_", delete=False
    ) as tmp:
        yaml.dump(merged, tmp, default_flow_style=False, allow_unicode=True, sort_keys=False)
        tmp_path = Path(tmp.name)

    try:
        cmd = [
            "macromog", "--output", "json",
            "import", "--char-name", args.char_name,
        ]
        if not args.no_backup:
            cmd += ["--backup-dir", str(BACKUP_DIR)]
        if args.dry_run:
            cmd.append("--dry-run")
        cmd.append(str(tmp_path))

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if not result.stdout.strip():
            print("macromog produced no output", file=sys.stderr)
            sys.exit(result.returncode or 1)

        output = json.loads(result.stdout)
        entries = output if isinstance(output, list) else [output]

        backup_path = None
        for entry in entries:
            if entry.get("ok"):
                sets = entry.get("sets", 0)
                print(f"Imported {sets} macro set(s) into {args.char_name}")
                if entry.get("backup_path"):
                    backup_path = Path(entry["backup_path"])
                    print(f"Backed up to {backup_path}")
            else:
                print(f"Import failed: {entry.get('error', 'unknown error')}", file=sys.stderr)
                sys.exit(1)

        if result.returncode != 0:
            sys.exit(result.returncode)

        if args.dry_run or args.no_backup:
            print("Temp file removed.")
            return

        if backup_path:
            dest = BACKUP_DIR / (backup_path.name + ".yml")
            shutil.move(str(tmp_path), dest)
            print(f"Saved merged YAML as {dest.name}")
        else:
            print(f"Warning: no backup path in output; temp file left at {tmp_path}")
            tmp_path = None  # don't delete in finally

    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


if __name__ == "__main__":
    main()
