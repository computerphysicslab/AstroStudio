"""Compact circular CPU/RAM meters with history and per-core bars."""

import math

import gi

try:
    import psutil
except ImportError:
    psutil = None

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, GLib, Gtk  # noqa: E402


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


def cpu_reading(overall: float, per_core: list):
    peak = max(per_core) if per_core else overall
    value = max(float(overall), float(peak))
    return value, "CPU %.0f%% (core %.0f%%)" % (overall, peak)


def cpu_delta(previous, current) -> float:
    idle = current[0] - previous[0]
    total = current[1] - previous[1]
    if total <= 0:
        return 0.0
    return max(0.0, min(100.0, (1.0 - idle / total) * 100.0))


class MeterWidget(Gtk.DrawingArea):
    """Circular gauge, 60-sample history sparkline and optional core bars."""

    def __init__(self, title: str) -> None:
        super().__init__()
        self.title = title
        self.value = 0.0
        self.history = []
        self.per_core = []
        self.set_app_paintable(True)
        self.set_size_request(300, 60)
        self.connect("draw", self._on_draw)

    def update(self, value: float, per_core: list = None) -> None:
        self.value = max(0.0, min(100.0, value))
        self.history.append(self.value)
        self.history = self.history[-60:]
        self.per_core = per_core or []
        self.queue_draw()

    @staticmethod
    def _colour(value: float):
        return (0.96, 0.30, 0.30) if value >= 75 else (0.16, 0.72, 0.36)

    def _on_draw(self, _widget, cr) -> bool:
        width = self.get_allocated_width()
        height = self.get_allocated_height()
        cr.set_source_rgb(0.08, 0.08, 0.10)
        cr.paint()
        cr.set_source_rgb(0.85, 0.85, 0.85)
        cr.set_font_size(9)
        cr.move_to(6, 12)
        cr.show_text(self.title)
        cr.set_font_size(13)
        cr.move_to(32, 38)
        cr.show_text("%.0f%%" % self.value)

        cx, cy, radius = 22, 34, 17
        cr.set_line_width(5)
        cr.set_source_rgb(0.22, 0.22, 0.26)
        cr.arc(cx, cy, radius, -math.pi / 2, 1.5 * math.pi)
        cr.stroke()
        end = -math.pi / 2 + 2 * math.pi * self.value / 100.0
        cr.set_source_rgb(*self._colour(self.value))
        cr.arc(cx, cy, radius, -math.pi / 2, end)
        cr.stroke()

        left, top = 72, 6
        chart_w = max(10, width - left - 8)
        chart_h = 28
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.12)
        cr.rectangle(left, top, chart_w, chart_h)
        cr.stroke()
        if len(self.history) > 1:
            cr.set_source_rgb(*self._colour(self.value))
            for index, sample in enumerate(self.history):
                x = left + index / 59.0 * chart_w
                y = top + chart_h - sample / 100.0 * chart_h
                if index == 0:
                    cr.move_to(x, y)
                else:
                    cr.line_to(x, y)
            cr.stroke()

        if self.per_core:
            bar_y = 44
            bar_h = 12
            bar_w = max(2, (width - 20) / len(self.per_core) - 2)
            for index, core in enumerate(self.per_core):
                x = 10 + index * (bar_w + 2)
                cr.set_source_rgb(0.22, 0.22, 0.26)
                cr.rectangle(x, bar_y, bar_w, bar_h)
                cr.fill()
                cr.set_source_rgb(*self._colour(core))
                cr.rectangle(x, bar_y + bar_h - core / 100.0 * bar_h, bar_w, core / 100.0 * bar_h)
                cr.fill()
        return False


class ResourceMonitor(Gtk.Box):
    """Update both meters once per second without touching image data."""

    def __init__(self, interval_ms: int = 1000) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.cpu_meter = MeterWidget("CPU")
        self.ram_meter = MeterWidget("RAM")
        self.pack_start(self.cpu_meter, False, False, 0)
        self.pack_start(self.ram_meter, False, False, 0)
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
            per_core = psutil.cpu_percent(percpu=True)
            value, _label = cpu_reading(overall, per_core)
            ram = psutil.virtual_memory().percent
        else:
            current = self._read_proc_cpu()
            value, _label = cpu_reading(cpu_delta(self._previous_cpu, current), [])
            self._previous_cpu = current
            per_core = []
            ram = self._read_proc_memory()
        self.cpu_meter.update(value, per_core)
        self.ram_meter.update(ram)
        return True

    def stop(self) -> None:
        if self.timeout_id is not None:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
