from pathlib import Path
import tomllib

import secondbrain

ROOT = Path(__file__).resolve().parents[1]


def test_package_version():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert secondbrain.__version__ == project["version"] == "1.0.0"


def test_v1_discard_boundary():
    modules = "backup capture lock open_cmd publish receipt restore root search verify".split()
    assert all(not (ROOT / "src/secondbrain" / (name + ".py")).exists() for name in modules)
    assert all(not (ROOT / name).exists() for name in ("legacy", "CONTRIBUTING.md", "docs/design.md", "docs/decisions.md", "docs/STATUS.md"))
