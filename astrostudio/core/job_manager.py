"""In-memory state for the visual job manager."""

import time
from dataclasses import dataclass
from typing import Dict, List

from .process_engine import JobResult


@dataclass
class JobState:
    job_id: str
    argv: List[str]
    started: float
    state: str = "running"
    duration_s: float = 0.0
    exit_code: int = -1
    error: str = None


class JobManager:
    """Track CLI jobs from dispatch to completion for the UI and retries."""

    def __init__(self) -> None:
        self.jobs: Dict[str, JobState] = {}

    def start(self, job_id: str, argv: List[str]) -> None:
        self.jobs[job_id] = JobState(job_id, list(argv), time.monotonic())

    def finish(self, job_id: str, result: JobResult) -> None:
        state = self.jobs.get(job_id)
        if state is None:
            return
        state.state = "done" if result.ok else "failed"
        state.duration_s = round(time.monotonic() - state.started, 3)
        state.exit_code = result.exit_code
        state.error = result.error or (result.stderr.splitlines()[0] if result.stderr else None)

    def entries(self) -> List[JobState]:
        return sorted(self.jobs.values(), key=lambda item: item.started, reverse=True)

    def argv_for(self, job_id: str) -> List[str]:
        state = self.jobs.get(job_id)
        return list(state.argv) if state else []
