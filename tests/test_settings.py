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
