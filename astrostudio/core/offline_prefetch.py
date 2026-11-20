"""Plan CLI jobs that warm offline plate-solving and survey caches."""

from typing import List, Sequence

DEFAULT_CATALOGS = ("mag07",)


def catalog_download_argv(catalog_id: str) -> List[str]:
    return [
        "skystacker",
        "--download-blind-catalog",
        catalog_id,
        "--no-donation",
    ]


def survey_prefetch_argv(
    source: str, output_dir: str, survey: str, catalog_id: str
) -> List[str]:
    return [
        "skystacker",
        "--process-image",
        source,
        "--image-op",
        "survey-cutout",
        "--image-output",
        output_dir,
        "--survey-hips",
        survey,
        "--blind-catalog",
        catalog_id,
        "--survey-timeout",
        "60",
        "--no-donation",
    ]


def prefetch_plan(
    catalogs: Sequence[str],
    source: str = None,
    output_dir: str = None,
    survey: str = None,
) -> List[List[str]]:
    jobs = [catalog_download_argv(item) for item in dict.fromkeys(catalogs)]
    if source and output_dir and survey:
        jobs.append(survey_prefetch_argv(source, output_dir, survey, catalogs[0]))
    return jobs
