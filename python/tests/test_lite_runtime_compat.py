from pathlib import Path
import sys
import types

import pytest

from PiFinder import utils


def _load_marking_menus(monkeypatch):
    fonts = types.ModuleType("PiFinder.ui.fonts")
    fonts.Font = object
    displays = types.ModuleType("PiFinder.displays")
    displays.DisplayBase = object
    monkeypatch.setitem(sys.modules, "PiFinder.ui.fonts", fonts)
    monkeypatch.setitem(sys.modules, "PiFinder.displays", displays)

    from PiFinder.ui.marking_menus import MarkingMenu, MarkingMenuOption

    return MarkingMenu, MarkingMenuOption


@pytest.mark.unit
def test_marking_menu_default_up_option_is_not_shared(monkeypatch):
    MarkingMenu, MarkingMenuOption = _load_marking_menus(monkeypatch)

    def menu_option(label):
        return MarkingMenuOption(label=label)

    first = MarkingMenu(
        down=menu_option("down"),
        left=menu_option("left"),
        right=menu_option("right"),
    )
    second = MarkingMenu(
        down=menu_option("down"),
        left=menu_option("left"),
        right=menu_option("right"),
    )

    first.up.selected = True

    assert first.up is not second.up
    assert second.up.selected is False


@pytest.mark.unit
def test_resolve_tetra3_dir_prefers_package_parent(tmp_path):
    repo_root = tmp_path
    package_parent = repo_root / "python" / "PiFinder" / "tetra3"
    package_dir = package_parent / "tetra3"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "tetra3.py").write_text("", encoding="utf-8")

    assert utils.resolve_tetra3_dir(repo_root) == package_parent


@pytest.mark.unit
def test_tetra3_sys_paths_include_generated_proto_import_dir(tmp_path):
    repo_root = tmp_path
    package_parent = repo_root / "python" / "PiFinder" / "tetra3"
    package_dir = package_parent / "tetra3"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "cedar_detect_pb2.py").write_text("", encoding="utf-8")

    assert utils.tetra3_sys_paths(repo_root) == (package_parent, package_dir)


@pytest.mark.unit
def test_resolve_tetra3_dir_keeps_legacy_nested_layout(tmp_path):
    repo_root = tmp_path
    legacy_dir = repo_root / "python" / "PiFinder" / "tetra3" / "tetra3"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "tetra3.py").write_text("", encoding="utf-8")

    assert utils.resolve_tetra3_dir(repo_root) == legacy_dir


@pytest.mark.unit
def test_resolve_tetra3_dir_returns_package_parent_when_missing(tmp_path):
    repo_root = Path(tmp_path)

    assert utils.resolve_tetra3_dir(repo_root) == (
        repo_root / "python" / "PiFinder" / "tetra3"
    )
