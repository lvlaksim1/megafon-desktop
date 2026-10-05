from pathlib import Path
import tomllib

import megafon_desktop


ROOT = Path(__file__).resolve().parents[1]


def test_release_versions_are_synchronized() -> None:
    release_version = (ROOT / "RELEASE_VERSION").read_text(encoding="utf-8").strip()
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["version"] == release_version
    assert megafon_desktop.__version__ == release_version


def test_post_initial_releases_are_update_installers() -> None:
    assert (ROOT / "RELEASE_KIND").read_text(encoding="utf-8").strip() == "Update"
