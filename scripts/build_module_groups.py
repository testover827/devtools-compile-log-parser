"""
build_module_groups.py

Walks the repository looking for JSON artifacts under configured module paths
and emits group-specific merged JSON files at config/module-groups/{group}.json.

Expected input config: config/module_groups.json
Format:
{
  "groupA": ["src/moduleA", "src/moduleB"],
  "groupB": ["src/moduleC"]
}

Behavior:
- For each group, find all .json files under each listed module path.
- Merge them into a single object where top-level keys are the relative JSON
  file paths (deterministic sorted order) and values are the parsed contents.
- Write pretty-printed JSON to config/module-groups/{group}.json (idempotent).
"""
from pathlib import Path
import json
import sys
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"
MODULE_GROUPS_IN = CONFIG_DIR / "module_groups.json"
MODULE_GROUPS_OUT_DIR = CONFIG_DIR / "module-groups"

def load_module_groups_config(path: Path) -> Dict[str, List[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Module groups config not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("module_groups.json must contain an object mapping group->list")
    return data

def collect_json_files_for_module(module_path: Path) -> List[Path]:
    if not module_path.exists():
        return []
    return sorted([p for p in module_path.rglob("*.json") if p.is_file()])

def build_group_json(group_name: str, module_paths: List[str]) -> Dict[str, object]:
    merged = {}
    for mod in module_paths:
        modpath = (REPO_ROOT / mod).resolve()
        files = collect_json_files_for_module(modpath)
        for f in files:
            # store by relative path from repo root for determinism
            try:
                rel = f.relative_to(REPO_ROOT)
            except Exception:
                rel = f
            key = str(rel)
            with f.open("r", encoding="utf-8") as fh:
                try:
                    content = json.load(fh)
                except Exception as e:
                    # keep parsing robust: include an error marker instead of failing entirely
                    content = {"__parse_error__": str(e), "__path__": key}
            merged[key] = content
    # ensure deterministic ordering by returning a dict with sorted keys
    return {k: merged[k] for k in sorted(merged.keys())}

def write_group_output(group_name: str, data: Dict[str, object], out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{group_name}.json"
    tmp_file = out_file.with_suffix(out_file.suffix + ".tmp")
    with tmp_file.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    tmp_file.replace(out_file)

def main(argv=None):
    try:
        groups = load_module_groups_config(MODULE_GROUPS_IN)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    outputs = []
    for group, module_list in groups.items():
        if not isinstance(module_list, list):
            print(f"WARN: group {group} does not map to a list, skipping", file=sys.stderr)
            continue
        data = build_group_json(group, module_list)
        write_group_output(group, data, MODULE_GROUPS_OUT_DIR)
        outputs.append(str(MODULE_GROUPS_OUT_DIR / f"{group}.json"))

    print("Wrote group JSON files:")
    for p in outputs:
        print(" -", p)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
