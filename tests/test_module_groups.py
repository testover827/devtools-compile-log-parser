import json
from pathlib import Path
import tempfile
import shutil
import importlib

from scripts import build_module_groups

def test_build_group_json(tmp_path, monkeypatch):
    # create a fake repo layout under tmp_path
    repo_root = tmp_path
    # create module files
    mod_a = repo_root / "src" / "moduleA"
    mod_a.mkdir(parents=True)
    f1 = mod_a / "a.json"
    f1.write_text(json.dumps({"value": 1}), encoding="utf-8")

    mod_b = repo_root / "src" / "moduleB"
    mod_b.mkdir(parents=True)
    f2 = mod_b / "b.json"
    f2.write_text(json.dumps({"value": 2}), encoding="utf-8")

    # create module_groups config
    cfg_dir = repo_root / "config"
    cfg_dir.mkdir()
    cfg = cfg_dir / "module_groups.json"
    cfg.write_text(json.dumps({"groupA": ["src/moduleA", "src/moduleB"]}), encoding="utf-8")

    # monkeypatch REPO_ROOT used by the module
    monkeypatch.setattr(build_module_groups, "REPO_ROOT", repo_root)
    monkeypatch.setattr(build_module_groups, "MODULE_GROUPS_IN", cfg)
    monkeypatch.setattr(build_module_groups, "MODULE_GROUPS_OUT_DIR", cfg_dir / "module-groups")

    # run main
    rc = build_module_groups.main()
    assert rc == 0

    out_file = cfg_dir / "module-groups" / "groupA.json"
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    # expect keys for both files
    assert any("moduleA/a.json" in k or "moduleA\\a.json" in k for k in data.keys())
    assert any("moduleB/b.json" in k or "moduleB\\b.json" in k for k in data.keys())
