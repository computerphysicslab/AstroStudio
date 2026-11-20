"""Offline prefetch planning tests."""

from astrostudio.core.offline_prefetch import catalog_download_argv, prefetch_plan


def test_catalog_download_argv():
    assert catalog_download_argv("mag07") == [
        "skystacker", "--download-blind-catalog", "mag07", "--no-donation"
    ]


def test_prefetch_plan_deduplicates_and_adds_survey_when_source_given():
    jobs = prefetch_plan(["mag07", "mag07", "mag06"], "sky.png", "/tmp/survey", "CDS/P/DSS2/color")
    assert len(jobs) == 3
    assert jobs[0][2] == "mag07"
    assert jobs[1][2] == "mag06"
    assert "--survey-hips" in jobs[2]
