"""Lightweight CPU and RAM level indicators for the right dock."""

import gi

try:
    import psutil
except ImportError:
    psutil = None

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, GLib, Gtk, Pango  # noqa: E402


def parse_meminfo(text: str) -> float:
    values = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parts = value.split()
        if parts:
            values[key] = float(parts[0])
    total = values.get("MemTotal", 0.0)
    available = values.get("MemAvailable", values.get("MemFree", 0.0))
    if total <= 0:
        return 0.0
    return max(0.0, min(100.0, (total - available) / total * 100.0))


def parse_proc_cpu(line: str):
    parts = line.split()
    if not parts or parts[0] != "cpu":
        return 0.0, 0.0
    numbers = [float(value) for value in parts[1:]]
    idle = numbers[3] + (numbers[4] if len(numbers) > 4 else 0.0)
    return idle, sum(numbers)


_METER_CSS = b"""
levelbar.astro-meter trough {
    background-color: #1c1c1c;
    border: 1px solid #3a3a3a;
}
levelbar.astro-meter block {
    background-color: #2ecc71;
}
levelbar.astro-meter.high block {
    background-color: #e74c3c;
}
label.astro-meter-high {
    color: #e74c3c;
    font-weight: bold;
}
label.astro-meter-ok {
    color: #2ecc71;
}
"""


def apply_meter_css() -> None:
    provider = Gtk.CssProvider()
    provider.load_from_data(_METER_CSS)
    screen = Gdk.Screen.get_default()
    if screen is not None:
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


def cpu_reading(overall: float, per_core: list):
    """Return the bar value and label, exposing per-core saturation."""
    peak = max(per_core) if per_core else overall
    value = max(float(overall), float(peak))
    return value, "CPU %.0f%% (core %.0f%%)" % (overall, peak)


def cpu_delta(previous, current) -> float:
    idle = current[0] - previous[0]
    total = current[1] - previous[1]
    if total <= 0:
        return 0.0
    return max(0.0, min(100.0, (1.0 - idle / total) * 100.0))


class ResourceMonitor(Gtk.Box):
    """Update two GTK level bars once per second without touching image data."""

    def __init__(self, interval_ms: int = 1000) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.interval_ms = interval_ms
        self.cpu_label = Gtk.Label(label="CPU 0%", xalign=0.0)
        self.ram_label = Gtk.Label(label="RAM 0%", xalign=0.0)
        for label in (self.cpu_label, self.ram_label):
            label.override_font(Pango.FontDescription("monospace 9"))
            label.get_style_context().add_class("astro-meter-ok")
        self.cpu_bar = Gtk.LevelBar()
        self.ram_bar = Gtk.LevelBar()
        for bar in (self.cpu_bar, self.ram_bar):
            bar.set_min_value(0.0)
            bar.set_max_value(100.0)
            bar.add_offset_value(Gtk.LEVEL_BAR_OFFSET_HIGH, 75.0)
            bar.get_style_context().add_class("astro-meter")
        apply_meter_css()
        self.pack_start(self.cpu_label, False, False, 0)
        self.pack_start(self.cpu_bar, False, False, 0)
        self.pack_start(self.ram_label, False, False, 0)
        self.pack_start(self.ram_bar, False, False, 0)

        self._previous_cpu = self._read_proc_cpu()
        if psutil is not None:
            psutil.cpu_percent(interval=None)
        self.timeout_id = GLib.timeout_add(interval_ms, self._update)
        self.connect("destroy", lambda *_widget: self.stop())

    @staticmethod
    def _read_proc_cpu():
        try:
            with open("/proc/stat", "r", encoding="utf-8") as handle:
                return parse_proc_cpu(handle.readline())
        except OSError:
            return 0.0, 0.0

    @staticmethod
    def _read_proc_memory() -> float:
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as handle:
                return parse_meminfo(handle.read())
        except OSError:
            return 0.0

    def _update(self) -> bool:
        if psutil is not None:
            overall = psutil.cpu_percent(interval=None)
            cpu, cpu_text = cpu_reading(overall, psutil.cpu_percent(percpu=True))
            ram = psutil.virtual_memory().percent
        else:
            current = self._read_proc_cpu()
            cpu, cpu_text = cpu_reading(cpu_delta(self._previous_cpu, current), [])
            self._previous_cpu = current
            ram = self._read_proc_memory()
        cpu = max(0.0, min(100.0, cpu))
        ram = max(0.0, min(100.0, ram))
        self.cpu_bar.set_value(cpu)
        self.ram_bar.set_value(ram)
        for label, value in ((self.cpu_label, cpu), (self.ram_label, ram)):
            context = label.get_style_context()
            if value >= 75.0:
                context.remove_class("astro-meter-ok")
                context.add_class("astro-meter-high")
            else:
                context.remove_class("astro-meter-high")
                context.add_class("astro-meter-ok")
        self.cpu_label.set_text(cpu_text)
        self.ram_label.set_text("RAM %.0f%%" % ram)
        return True

    def stop(self) -> None:
        if self.timeout_id is not None:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
