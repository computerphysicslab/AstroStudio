"""Plugin discovery and remote adapter tests."""

from astrostudio.adapters.remote import RemoteAdapter
from astrostudio.core.plugins import register_plugins


class FakeAdapter:
    name = "FakePlugin"

    def build_argv(self, inputs, output=None, params=None):
        return list(inputs)


class FakeEntryPoint:
    def __init__(self, factory):
        self.factory = factory

    def load(self):
        return self.factory


def test_register_plugins(monkeypatch):
    import importlib.metadata

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda: {"astrostudio.adapters": [FakeEntryPoint(FakeAdapter)]},
    )
    target = {}
    names = register_plugins(target)
    assert names == ["FakePlugin"]
    assert target["FakePlugin"].build_argv(["a"]) == ["a"]


def test_remote_ssh_argv_quotes_paths():
    adapter = RemoteAdapter("ssh", "user@host")
    argv = adapter.build_ssh_argv(["convert", "my image.tif", "out.tif"], "/work dir")
    assert argv[:2] == ["ssh", "user@host"]
    assert "my image.tif" in argv[2]
    assert "cd '/work dir'" in argv[2]


def test_remote_api_argv_is_json_payload():
    adapter = RemoteAdapter("api", "https://example.invalid/jobs")
    argv = adapter.build_api_argv({"argv": ["convert", "a.tif", "b.tif"]})
    assert argv[0] == "curl"
    assert '"argv"' in argv[-2]
