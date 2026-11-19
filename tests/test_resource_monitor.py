"""Resource monitor parsing helpers."""

from astrostudio.ui.resource_monitor import (
    cpu_delta,
    cpu_reading,
    parse_meminfo,
    parse_proc_cpu,
)


def test_parse_meminfo_uses_available_memory():
    text = "MemTotal:       1000000 kB\nMemFree:         100000 kB\nMemAvailable:    300000 kB\n"
    assert parse_meminfo(text) == 70.0


def test_parse_proc_cpu_and_delta():
    previous = parse_proc_cpu("cpu  100 0 50 850 0 0 0 0 0 0")
    current = parse_proc_cpu("cpu  200 0 100 1700 0 0 0 0 0 0")
    assert previous == (850.0, 1000.0)
    assert round(cpu_delta(previous, current), 3) == 15.0


def test_cpu_reading_exposes_per_core_saturation():
    value, label = cpu_reading(15.0, [98.0, 12.0, 10.0])
    assert value == 98.0
    assert "core 98%" in label
    assert cpu_reading(15.0, []) == (15.0, "CPU 15% (core 15%)")


def test_empty_proc_data_is_safe():
    assert parse_proc_cpu("") == (0.0, 0.0)
    assert parse_meminfo("") == 0.0
    assert cpu_delta((0, 0), (0, 0)) == 0.0
