"""Session scratch-space management.

Original captures are strictly read-only. Every backend artifact is written
under a session/job directory and removed on session close unless preserved.
"""

import os
import shutil
import tempfile


class ScratchManager:
    def __init__(self, session: str = None) -> None:
        session_id = session or str(os.getpid())
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
        if runtime_dir and os.path.isdir(runtime_dir):
            self.root = os.path.join(runtime_dir, "astro-studio", session_id)
        else:
            self.root = tempfile.mkdtemp(prefix="astro_studio_%s_" % session_id)
        os.makedirs(self.root, exist_ok=True)

    @staticmethod
    def _safe_job_id(job_id: str) -> str:
        safe_id = "".join(
            character if character.isalnum() or character in "-_" else "_"
            for character in job_id
        )
        return safe_id or "job"

    def job_dir(self, job_id: str) -> str:
        path = os.path.join(self.root, self._safe_job_id(job_id))
        os.makedirs(path, exist_ok=True)
        return path

    def cleanup_job(self, job_id: str) -> None:
        shutil.rmtree(os.path.join(self.root, self._safe_job_id(job_id)), ignore_errors=True)

    def cleanup_all(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
