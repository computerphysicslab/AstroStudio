"""Asynchronous CLI process execution on the GLib main context."""

import os
import signal
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence

from gi.repository import Gio, GLib

LogCallback = Callable[[str], None]
DoneCallback = Callable[["JobResult"], None]


@dataclass
class JobResult:
    job_id: str
    argv: List[str]
    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.exit_code == 0


class ProcessHandle:
    def __init__(
        self,
        job_id: str,
        argv: List[str],
        on_done: Optional[DoneCallback] = None,
    ) -> None:
        self.job_id = job_id
        self.argv = argv
        self.on_done = on_done
        self.cancellable = Gio.Cancellable()
        self.process: Optional[Gio.Subprocess] = None
        self.streams: List[Gio.DataInputStream] = []
        self.pending_streams = 0
        self.process_finished = False
        self.finished = False
        self.exit_code = -1
        self.error: Optional[str] = None
        self.cancelled = False
        self.stdout_lines: List[str] = []
        self.stderr_lines: List[str] = []
        self.started = time.monotonic()


class ProcessEngine:
    """Spawn CLI backends without blocking the GTK main thread."""

    def __init__(self, operation_log=None) -> None:
        self._active: Dict[str, ProcessHandle] = {}
        self.operation_log = operation_log

    def run(
        self,
        job_id: str,
        argv: Sequence[str],
        on_log: Optional[LogCallback] = None,
        on_done: Optional[DoneCallback] = None,
    ) -> ProcessHandle:
        argv_list = list(argv)
        handle = ProcessHandle(job_id, argv_list, on_done)
        self._active[job_id] = handle
        if self._should_record(job_id):
            self.operation_log.record("cli_start", job_id=job_id, argv=argv_list)

        flags = Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE
        try:
            process = Gio.Subprocess.new(argv_list, flags)
        except GLib.Error as exc:
            handle.error = str(exc)
            if self._should_record(job_id):
                self._record_end(handle)
            if on_done:
                GLib.idle_add(on_done, self._result(handle))
            return handle

        handle.process = process
        handle.pending_streams = 2
        for source, name in (
            (process.get_stdout_pipe(), "stdout"),
            (process.get_stderr_pipe(), "stderr"),
        ):
            stream = Gio.DataInputStream.new(source)
            handle.streams.append(stream)
            self._watch_stream(stream, handle, name, on_log)

        process.wait_async(handle.cancellable, self._on_wait, handle)
        return handle

    def _should_record(self, job_id: str) -> bool:
        return self.operation_log is not None and not job_id.startswith("probe-")

    def _record_end(self, handle: ProcessHandle) -> None:
        if self.operation_log is None:
            return
        input_bytes = output_bytes = None
        paths = [token for token in handle.argv[1:] if os.path.isfile(token)]
        if paths:
            try:
                input_bytes = os.path.getsize(paths[0])
            except OSError:
                pass
        if paths and len(paths) > 1:
            try:
                output_bytes = os.path.getsize(paths[-1])
            except OSError:
                pass
        self.operation_log.record(
            "cli_end",
            job_id=handle.job_id,
            argv=handle.argv,
            duration_s=round(time.monotonic() - handle.started, 3),
            exit_code=handle.exit_code,
            stdout_lines=len(handle.stdout_lines),
            stderr_lines=len(handle.stderr_lines),
            input_bytes=input_bytes,
            output_bytes=output_bytes,
            error=handle.error,
            stderr=handle.stderr_lines[0] if handle.stderr_lines else None,
        )

    def _watch_stream(
        self,
        stream: Gio.DataInputStream,
        handle: ProcessHandle,
        name: str,
        on_log: Optional[LogCallback],
    ) -> None:
        stream.read_line_async(
            GLib.PRIORITY_DEFAULT,
            handle.cancellable,
            self._on_line,
            (handle, name, on_log, stream),
        )

    def _on_line(self, stream: Gio.DataInputStream, result, user_data) -> None:
        handle, name, on_log, source = user_data
        try:
            line, length = stream.read_line_finish_utf8(result)
        except GLib.Error as exc:
            line, length = "", 0
            handle.error = "cancelled by user" if handle.cancelled else (handle.error or str(exc))
        if length:
            target = handle.stdout_lines if name == "stdout" else handle.stderr_lines
            target.append(line)
            if on_log:
                GLib.idle_add(on_log, "[%s] %s" % (name, line))
            self._watch_stream(source, handle, name, on_log)
            return
        handle.pending_streams -= 1
        self._maybe_finish(handle)

    def _on_wait(self, process: Gio.Subprocess, result, handle: ProcessHandle) -> None:
        try:
            process.wait_finish(result)
        except GLib.Error as exc:
            handle.error = "cancelled by user" if handle.cancelled else (handle.error or str(exc))
        handle.exit_code = process.get_exit_status() if process.get_if_exited() else -1
        handle.process_finished = True
        self._maybe_finish(handle)

    def _maybe_finish(self, handle: ProcessHandle) -> None:
        if handle.finished or handle.pending_streams or not handle.process_finished:
            return
        handle.finished = True
        for stream in handle.streams:
            try:
                stream.close()
            except GLib.Error:
                pass
        handle.streams.clear()
        self._record_end(handle)
        self._active.pop(handle.job_id, None)
        on_done = getattr(handle, "on_done", None)
        if on_done:
            GLib.idle_add(on_done, self._result(handle))

    @staticmethod
    def _result(handle: ProcessHandle) -> JobResult:
        return JobResult(
            job_id=handle.job_id,
            argv=handle.argv,
            exit_code=handle.exit_code,
            stdout="\n".join(handle.stdout_lines),
            stderr="\n".join(handle.stderr_lines),
            error=handle.error,
        )

    def cancel(self, job_id: str) -> bool:
        handle = self._active.get(job_id)
        if handle is None or handle.finished:
            return False
        handle.cancelled = True
        handle.cancellable.cancel()
        if handle.process is not None:
            try:
                handle.process.send_signal(signal.SIGTERM)
            except (GLib.Error, RuntimeError):
                pass
        return True

    def cancel_all(self) -> None:
        for job_id in list(self._active):
            self.cancel(job_id)

    @property
    def active_jobs(self) -> List[str]:
        return list(self._active)
