"""Backend discovery and menu capability gating tests."""

from astrostudio.core import backends
from astrostudio.core.backends import BackendRegistry, BackendSpec
from astrostudio.core.process_engine import JobResult


class FakeEngine:
    def __init__(self, output="tool 7.1.2", exit_code=0):
        self.output = output
        self.exit_code = exit_code
        self.calls = []

    def run(self, job_id, argv, on_log=None, on_done=None):
        self.calls.append((job_id, argv))
        on_done(
            JobResult(job_id=job_id, argv=list(argv), stdout=self.output, exit_code=self.exit_code)
        )


def test_probe_records_installed_binary_and_version(monkeypatch):
    monkeypatch.setattr(backends.shutil, "which", lambda binary: "/usr/bin/" + binary)
    monkeypatch.setattr(backends.GLib, "idle_add", lambda function, *args: function(*args))
    updates = []
    registry = BackendRegistry((BackendSpec("Fake", "fake-tool", "Test", ("-v",)),))
    engine = FakeEngine(output="fake-tool version 3.4.5")

    registry.probe(engine, on_update=updates.append)

    assert engine.calls == [("probe-Fake", ["/usr/bin/fake-tool", "-v"])]
    assert registry.available("Fake")
    assert registry.version("Fake") == "3.4.5"
    assert len(updates) == 1


def test_probe_marks_missing_binary(monkeypatch):
    monkeypatch.setattr(backends.shutil, "which", lambda binary: None)
    monkeypatch.setattr(backends.GLib, "idle_add", lambda function, *args: function(*args))
    registry = BackendRegistry((BackendSpec("Fake", "missing-tool", "Test"),))

    registry.probe(FakeEngine(), on_update=lambda registry: None)

    assert not registry.available("Fake")
    assert registry.status["Fake"].error == "not installed"


def test_version_query_failure_keeps_available_status(monkeypatch):
    monkeypatch.setattr(backends.shutil, "which", lambda binary: "/usr/bin/" + binary)
    registry = BackendRegistry((BackendSpec("Fake", "fake-tool", "Test"),))
    registry.probe(FakeEngine(output="no version here"))
    assert registry.available("Fake")
    assert registry.version("Fake") == "unknown"


def test_alternative_binary_is_detected(monkeypatch):
    monkeypatch.setattr(
        backends.shutil,
        "which",
        lambda binary: "/usr/bin/convert" if binary == "convert" else None,
    )
    registry = BackendRegistry(
        (BackendSpec("ImageMagick", "magick", "Conversion", ("-version",), ("convert",)),)
    )
    assert registry.available("ImageMagick")
    assert registry.status["ImageMagick"].binary == "/usr/bin/convert"


def test_menu_actions_are_gated_by_backend_availability(monkeypatch):
    monkeypatch.setattr(backends.shutil, "which", lambda binary: None)
    registry = BackendRegistry()
    assert not registry.is_action_enabled("export")
    assert not registry.is_action_enabled("metadata")
    assert registry.is_action_enabled("open")

    registry.status["ImageMagick"].available = True
    assert registry.is_action_enabled("export")
    assert registry.is_action_enabled("resize")

    registry.status["ExifTool"].available = True
    assert registry.is_action_enabled("metadata")

    assert not registry.is_action_enabled("calibration")
    assert not registry.is_action_enabled("stacking")
    assert not registry.is_action_enabled("plate-solve")

    registry.status["SkyStacker"].available = True
    assert registry.is_action_enabled("plate-solve")
    assert registry.is_action_enabled("sky-map")
