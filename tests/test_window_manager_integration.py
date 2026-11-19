"""Opt-in integration test: the window must be maximizable under a real WM."""

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    not all(
        (
            os.environ.get("DISPLAY"),
            os.environ.get("ASTROSTUDIO_WM_TEST") == "1",
            shutil.which("wmctrl"),
            shutil.which("xprop"),
            shutil.which("xdpyinfo"),
            shutil.which("dbus-run-session"),
        )
    ),
    reason="set ASTROSTUDIO_WM_TEST=1 with a display and X11 tools",
)


def _window_id():
    output = subprocess.check_output(["wmctrl", "-l"], text=True)
    for line in output.splitlines():
        if "Astro Studio" in line:
            return line.split()[0]
    return None


def test_window_can_maximize():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    proc = subprocess.Popen(
        ["dbus-run-session", "--", "python3", "-m", "astrostudio"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wid = None
        for _ in range(160):
            wid = _window_id()
            if wid:
                break
            time.sleep(0.25)
        assert wid, "Astro Studio window did not appear (poll=%s)" % proc.poll()

        hints = subprocess.check_output(
            ["xprop", "-id", wid, "WM_NORMAL_HINTS"], text=True
        )
        match = re.search(r"minimum size: \d+ by (\d+)", hints)
        assert match, hints
        min_height = int(match.group(1))
        screen = subprocess.check_output(["xdpyinfo"], text=True)
        height = int(re.search(r"dimensions:\s+\d+x(\d+)", screen).group(1))
        assert min_height < height - 40, (min_height, height)

        subprocess.check_call(
            ["wmctrl", "-i", "-r", wid, "-b", "add,maximized_vert,maximized_horz"]
        )
        state = ""
        for _ in range(20):
            state = subprocess.check_output(
                ["xprop", "-id", wid, "_NET_WM_STATE"], text=True
            )
            if "MAXIMIZED_VERT" in state:
                break
            time.sleep(0.25)
        assert "MAXIMIZED_VERT" in state, state
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
