"""Argv builders for remote compute backends."""

import json
import shlex
from typing import List, Sequence


class RemoteAdapter:
    """Wrap a local argv for SSH or an HTTP job API without in-process processing."""

    def __init__(self, mode: str, target: str) -> None:
        self.mode = mode
        self.target = target

    def build_ssh_argv(self, remote_argv: Sequence[str], workdir: str = "") -> List[str]:
        command = " ".join(shlex.quote(token) for token in remote_argv)
        if workdir:
            command = "cd %s && %s" % (shlex.quote(workdir), command)
        return ["ssh", self.target, command]

    def build_api_argv(self, payload: dict) -> List[str]:
        return [
            "curl",
            "--fail",
            "--silent",
            "--show-error",
            "-X",
            "POST",
            "-H",
            "Content-Type: application/json",
            "-d",
            json.dumps(payload, sort_keys=True),
            self.target,
        ]

    def build_argv(self, remote_argv: Sequence[str], workdir: str = "") -> List[str]:
        if self.mode == "api":
            return self.build_api_argv({"argv": list(remote_argv), "workdir": workdir})
        return self.build_ssh_argv(remote_argv, workdir)
