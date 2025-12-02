"""
mark_mvc_for_deletion.py

Utility to find files and directories which include 'mvc' in their path or name
(case-insensitive) and optionally delete them from the repository when run in a
local clone. This script is provided as a safety tool: deletion will not be
performed against the remote repository by itself; instead it modifies the working tree and can be used with git to commit the removals.
"""
from pathlib import Path
import argparse

def find_mvc_paths(root: Path):
    results = []
    for p in root.rglob("*"):
        if "mvc" in p.name.lower() or "mvc" in str(p).lower():
            results.append(p)
    return results

def main():
    p = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true", help="Delete matched files/directories locally")
    args = parser.parse_args()
    matches = find_mvc_paths(p)
    if not matches:
        print("No MVC-related paths found")
        return 0
    print("Found MVC-related paths:")
    for m in matches:
        print(" -", m)
    if args.delete:
        for m in matches:
            try:
                if m.is_dir():
                    import shutil
                    shutil.rmtree(m)
                else:
                    m.unlink()
                print("Deleted:", m)
            except Exception as e:
                print("Failed to delete", m, e)
    else:
        print("Run with --delete to remove these paths locally")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
