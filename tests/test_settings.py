"""Persistent preference tests."""

from astrostudio.core import BackendRegistry, SettingsManager
from astrostudio.core.backends import BackendSpec


def test_settings_round_trip(tmp_path):
    path = str(tmp_path / "settings.json")
    settings = SettingsManager(path)
    assert settings.is_backend_enabled("ExifTool")
    assert settings.get("language") == "en"

    settings.set_backend_enabled("ExifTool", False)
    settings.set("language", "es")
    settings.save()

    reloaded = SettingsManager(path)
    assert not reloaded.is_backend_enabled("ExifTool")
    assert reloaded.get("language") == "es"


def test_binary_override_is_used_by_registry(monkeypatch):
    import astrostudio.core.backends as backend_module

    monkeypatch.setattr(
        backend_module.shutil,
        "which",
        lambda binary: "/opt/custom/exiftool" if binary == "/opt/custom/exiftool" else None,
    )
    settings = SettingsManager("/tmp/astro-studio-nonexistent-override.json")
    settings.set("binary_overrides", {"ExifTool": "/opt/custom/exiftool"})
    registry = backend_module.BackendRegistry(
        (backend_module.BackendSpec("ExifTool", "exiftool", "Metadata", ("-ver",)),),
        settings=settings,
    )
    assert registry.installed("ExifTool")
    assert registry.status["ExifTool"].binary == "/opt/custom/exiftool"


def test_disabled_backend_disables_its_actions():
    settings = SettingsManager("/tmp/astro-studio-settings-does-not-exist.json")
    settings.set_backend_enabled("ImageMagick", False)
    registry = BackendRegistry(
        (BackendSpec("ImageMagick", "convert", "Conversion", ("-version",)),),
        settings=settings,
    )
    registry.status["ImageMagick"].available = True

    assert registry.installed("ImageMagick")
    assert not registry.available("ImageMagick")
    assert not registry.is_action_enabled("export")
