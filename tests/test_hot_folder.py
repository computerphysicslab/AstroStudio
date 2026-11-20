"""Hot-folder watcher tests."""

from astrostudio.core.hot_folder import HotFolderWatcher, folders_from_files


def test_watcher_detects_new_lights(tmp_path):
    (tmp_path / "Lights").mkdir()
    (tmp_path / "Darks").mkdir()
    light = tmp_path / "Lights" / "one.fits"
    light.write_bytes(b"x")
    (tmp_path / "Darks" / "dark.fits").write_bytes(b"x")
    fired = []

    watcher = HotFolderWatcher(str(tmp_path), lambda lights, found: fired.append(lights))
    watcher.poll()
    assert fired == []

    second = tmp_path / "Lights" / "two.fits"
    second.write_bytes(b"x")
    watcher.poll()
    assert len(fired) == 1
    assert {path.rsplit("/", 1)[-1] for path in fired[0]} == {"one.fits", "two.fits"}

    watcher.poll()
    assert len(fired) == 1


def test_folders_from_files():
    found = {
        "light": ["/session/Lights/a.fits"],
        "dark": ["/session/Darks/d.fits"],
        "flat": [],
        "bias": [],
    }
    assert folders_from_files(found) == {
        "light": "/session/Lights",
        "dark": "/session/Darks",
        "flat": "",
        "bias": "",
    }
