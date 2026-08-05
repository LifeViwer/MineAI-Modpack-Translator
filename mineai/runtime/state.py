import threading
import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class JobSnapshot:
    is_running: bool
    is_paused: bool
    total_strings: int
    translated_strings: int
    current_file_type: str
    current_file_done: int
    total_files: int
    start_time: float | None


@dataclass
class JobState:
    is_running: bool = False
    is_paused: bool = False

    total_strings: int = 0
    translated_strings: int = 0

    current_file_type: str = ""
    current_file_done: int = 0
    total_files: int = 0

    start_time: float | None = None
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    _condition: threading.Condition = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_condition", threading.Condition(self._lock))

    def __setattr__(self, name: str, value) -> None:
        """Keep legacy direct GUI assignments compatible with Condition waits.

        The GUI still writes ``is_running`` and ``is_paused`` directly. Once the
        condition exists, route those writes through it so a direct resume/stop
        cannot leave a worker blocked forever.
        """
        if name not in {"is_running", "is_paused"}:
            object.__setattr__(self, name, value)
            return

        condition = self.__dict__.get("_condition")
        if condition is None:
            object.__setattr__(self, name, bool(value))
            return

        with condition:
            object.__setattr__(self, name, bool(value))
            if (name == "is_running" and not value) or (
                name == "is_paused" and not value
            ):
                condition.notify_all()

    def start(self) -> None:
        with self._condition:
            self.is_running = True
            self.is_paused = False
            self._condition.notify_all()

    def finish(self) -> None:
        with self._condition:
            self.is_running = False
            self.is_paused = False
            self._condition.notify_all()

    def pause(self) -> bool:
        with self._condition:
            if not self.is_running:
                return False
            self.is_paused = True
            return True

    def resume(self) -> bool:
        with self._condition:
            if not self.is_paused:
                return False
            self.is_paused = False
            return True

    def toggle_pause(self) -> bool:
        with self._condition:
            if not self.is_running:
                return False
            self.is_paused = not self.is_paused
            return self.is_paused

    def wait_if_paused(self) -> None:
        with self._condition:
            while self.is_paused and self.is_running:
                self._condition.wait()

    def should_run(self) -> bool:
        with self._lock:
            return self.is_running

    def stop(self) -> None:
        self.finish()

    def set_total_strings(self, total: int) -> None:
        with self._lock:
            self.total_strings = max(0, total)

    def begin_progress(self) -> None:
        with self._lock:
            self.start_time = time.time()
            self.translated_strings = 0
            self.current_file_type = ""
            self.current_file_done = 0
            self.total_files = 0

    def increment_translated(self, count: int = 1) -> None:
        with self._lock:
            self.translated_strings += count

    def update_file_progress(self, file_type: str, done: int, total: int) -> None:
        with self._lock:
            self.current_file_type = file_type
            self.current_file_done = done
            self.total_files = total

    def snapshot(self) -> JobSnapshot:
        with self._lock:
            return JobSnapshot(
                is_running=self.is_running,
                is_paused=self.is_paused,
                total_strings=self.total_strings,
                translated_strings=self.translated_strings,
                current_file_type=self.current_file_type,
                current_file_done=self.current_file_done,
                total_files=self.total_files,
                start_time=self.start_time,
            )

    def line_progress(self) -> float:
        snapshot = self.snapshot()
        if snapshot.total_strings <= 0:
            return 0.0
        return min(snapshot.translated_strings / snapshot.total_strings, 1.0)

    @staticmethod
    def _eta_text(snapshot: JobSnapshot, now: float | None = None) -> str:
        if not snapshot.start_time or snapshot.translated_strings == 0:
            return "расчёт..."
        elapsed = (time.time() if now is None else now) - snapshot.start_time
        if elapsed < 5:
            return "расчёт..."
        remaining = snapshot.total_strings - snapshot.translated_strings
        if remaining <= 0:
            return "готово"
        rate = snapshot.translated_strings / elapsed
        if rate <= 0:
            return "расчёт..."
        seconds = remaining / rate
        if seconds < 60:
            return f"{int(seconds)} сек"
        if seconds < 3600:
            return f"{int(seconds // 60)} мин {int(seconds % 60)} сек"
        return f"{int(seconds // 3600)} ч {int((seconds % 3600) // 60)} мин"

    def eta_text(self) -> str:
        return self._eta_text(self.snapshot())

    def get_full_status(self, engine_msg: str = "") -> str:
        snapshot = self.snapshot()

        file_info = ""
        if snapshot.total_files > 0:
            file_info = (
                f"[{snapshot.current_file_type} "
                f"{snapshot.current_file_done}/{snapshot.total_files}] "
            )

        string_info = ""
        if snapshot.total_strings > 0:
            string_info = (
                f"Строки: {snapshot.translated_strings}/"
                f"{snapshot.total_strings} | "
            )

        engine_info = f"{engine_msg} | " if engine_msg else ""
        eta = f"Осталось: {self._eta_text(snapshot)}"
        return f"{file_info}{string_info}{engine_info}{eta}"
