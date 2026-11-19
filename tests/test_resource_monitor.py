"""Resource monitor parsing helpers."""

from astrostudio.ui.resource_monitor import cpu_delta, parse_meminfo, parse_proc_cpu


def test_parse_meminfo_uses_available_memory():
    text = "MemTotal:       1000000 kB\nMemFree:         100000 kB\nMemAvailable:    300000 kB\n"
    assert parse_meminfo(text) == 70.0


def test_parse_proc_cpu_and_delta():
    previous = parse_proc_cpu("cpu  100 0 50 850 0 0 0 0 0 0")
    current = parse_proc_cpu("cpu  200 0 100 1700 0 0 0 0 0 0")
    assert previous == (850.0, 1000.0)
    assert round(cpu_delta(previous, current), 3) == 15.0


def test_empty_proc_data_is_safe():
    assert parse_proc_cpu("") == (0.0, 0.0)
    assert parse_meminfo("") == 0.0
    assert cpu_delta((0, 0), (0, 0)) == 0.0
