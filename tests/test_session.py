"""Session save/resume tests."""

from astrostudio.core.session import load_session, save_session


def test_session_round_trip(tmp_path):
    path = str(tmp_path / "session.json")
    state = {"images": ["/tmp/a.fits"], "stretch_points": {"/tmp/a.fits": [10, 200]}}
    save_session(path, state)
    assert load_session(path) == state
    assert load_session(str(tmp_path / "missing.json")) == {}
