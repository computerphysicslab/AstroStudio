#!/usr/bin/env python3
"""Export recorded CLI jobs for a session as a shell script or Makefile."""

import argparse

from astrostudio.core.operation_log import OperationLog
from astrostudio.core.pipeline_export import cli_entries, write_makefile, write_shell


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default=OperationLog().path)
    parser.add_argument("--session", default=None)
    parser.add_argument("--format", choices=("sh", "make"), default="sh")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    entries = OperationLog(args.log).entries()
    jobs = cli_entries(entries, args.session)
    if args.format == "make":
        write_makefile(jobs, args.out)
    else:
        write_shell(jobs, args.out)
    print("Exported %d jobs to %s" % (len(jobs), args.out))


if __name__ == "__main__":
    main()
