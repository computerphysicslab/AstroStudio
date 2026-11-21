"""Plan CLI jobs that warm offline plate-solving and survey caches."""

from typing import List, Sequence

DEFAULT_CATALOGS = ("mag07",)


def _with_catalog_env(argv: List[str], catalog_dir: str = None) -> List[str]:
    if not catalog_dir:
        return argv
    return ["/usr/bin/env", "SKYSTACKER_CATALOGS=" + catalog_dir] + argv


def catalog_download_argv(catalog_id: str, catalog_dir: str = None) -> List[str]:
    return _with_catalog_env(
        [
            "skystacker",
            "--download-blind-catalog",
            catalog_id,
            "--no-donation",
        ],
        catalog_dir,
    )


def survey_prefetch_argv(
    source: str,
    output_dir: str,
    survey: str,
    catalog_id: str,
    catalog_dir: str = None,
    plate_center: str = None,
) -> List[str]:
    argv = [
        "skystacker",
        "--process-image",
        source,
        "--image-op",
        "survey-cutout",
        "--image-output",
        output_dir,
    ]
    if plate_center:
        argv.extend(("--plate-solve", "--plate-center", plate_center))
    argv.extend(
        (
            "--survey-hips",
            survey,
            "--blind-catalog",
            catalog_id,
            "--survey-timeout",
            "60",
            "--no-donation",
        )
    )
    return _with_catalog_env(argv, catalog_dir)


def prefetch_plan(
    catalogs: Sequence[str],
    source: str = None,
    output_dir: str = None,
    survey: str = None,
    catalog_dir: str = None,
    plate_center: str = None,
) -> List[List[str]]:
    jobs = [catalog_download_argv(item, catalog_dir) for item in dict.fromkeys(catalogs)]
    if source and output_dir and survey:
        jobs.append(
            survey_prefetch_argv(
                source, output_dir, survey, catalogs[0], catalog_dir, plate_center
            )
        )
    return jobs
