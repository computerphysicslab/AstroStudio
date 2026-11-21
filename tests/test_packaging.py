"""Packaging metadata tests."""

import json

import yaml


def test_flatpak_manifest_is_valid():
    path = "packaging/flatpak/org.astrostudio.AstroStudio.json"
    data = json.load(open(path, encoding="utf-8"))
    assert data["app-id"] == "org.astrostudio.AstroStudio"
    assert data["command"] == "astro-studio"
    assert data["modules"]


def test_appimage_recipe_is_valid():
    path = "packaging/appimage/AppImageBuilder.yml"
    data = yaml.safe_load(open(path, encoding="utf-8"))
    assert data["AppDir"]["app_info"]["name"] == "Astro Studio"
    assert "python3-gi" in data["AppDir"]["apt"]["include"]


def test_ci_workflow_installs_test_dependencies():
    text = open(".github/workflows/ci.yml", encoding="utf-8").read()
    for dependency in (
        "python3-cairo",
        "python3-gi",
        "python3-gi-cairo",
        "xvfb",
        "desktop-file-utils",
    ):
        assert dependency in text
    assert "mypy --config-file mypy.ini" in text
    assert "--cov-fail-under=70" in text


def test_optional_dependencies_declared():
    text = open("packaging/OPTIONAL_DEPENDENCIES.md", encoding="utf-8").read()
    for binary in ("skystacker", "siril-cli", "solve-field", "exiftool"):
        assert binary in text
