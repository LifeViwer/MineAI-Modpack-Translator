import subprocess
import threading
import unittest
from unittest import mock

from mineai.runtime.ai_launcher import AiLauncher
from mineai.runtime.state import JobState


class _Config:
    def get(self, section: str, key: str) -> str:
        values = {
            ("AI", "exe_path"): "koboldcpp",
            ("AI", "model_path"): "model.gguf",
            ("AI", "gpu_layers"): "99",
        }
        return values[(section, key)]


class JobStateShutdownTests(unittest.TestCase):
    @staticmethod
    def _paused_worker(state: JobState) -> tuple[threading.Thread, threading.Event]:
        exited = threading.Event()
        thread = threading.Thread(
            target=lambda: (state.wait_if_paused(), exited.set())
        )
        thread.start()
        return thread, exited

    def test_stop_wakes_a_paused_worker(self) -> None:
        state = JobState()
        state.start()
        self.assertTrue(state.pause())
        thread, exited = self._paused_worker(state)
        self.assertFalse(exited.wait(0.05))

        state.stop()

        self.assertTrue(exited.wait(0.5))
        thread.join(0.5)
        self.assertFalse(thread.is_alive())
        self.assertFalse(state.should_run())
        self.assertFalse(state.snapshot().is_paused)

    def test_resume_wakes_a_paused_worker(self) -> None:
        state = JobState()
        state.start()
        state.pause()
        thread, exited = self._paused_worker(state)
        self.assertFalse(exited.wait(0.05))

        self.assertTrue(state.resume())

        self.assertTrue(exited.wait(0.5))
        thread.join(0.5)
        self.assertTrue(state.should_run())
        state.stop()

    def test_legacy_direct_resume_wakes_a_paused_worker(self) -> None:
        state = JobState()
        state.is_running = True
        state.is_paused = True
        thread, exited = self._paused_worker(state)
        self.assertFalse(exited.wait(0.05))

        state.is_paused = False

        self.assertTrue(exited.wait(0.5))
        thread.join(0.5)
        self.assertFalse(thread.is_alive())
        state.stop()

    def test_legacy_direct_stop_wakes_a_paused_worker(self) -> None:
        state = JobState(is_running=True, is_paused=True)
        thread, exited = self._paused_worker(state)
        self.assertFalse(exited.wait(0.05))

        state.is_running = False

        self.assertTrue(exited.wait(0.5))
        thread.join(0.5)
        self.assertFalse(thread.is_alive())

    def test_stop_is_idempotent(self) -> None:
        state = JobState(is_running=True, is_paused=True)

        state.stop()
        state.stop()

        snapshot = state.snapshot()
        self.assertFalse(snapshot.is_running)
        self.assertFalse(snapshot.is_paused)

    def test_line_progress_is_preserved_from_current_beta(self) -> None:
        state = JobState(total_strings=4, translated_strings=3)
        self.assertEqual(state.line_progress(), 0.75)


class AiLauncherShutdownTests(unittest.TestCase):
    @staticmethod
    def _running_process() -> mock.Mock:
        process = mock.Mock()
        process.poll.side_effect = [None, 0]
        return process

    def test_cancellation_during_startup_terminates_owned_process(self) -> None:
        launcher = AiLauncher(_Config())
        process = self._running_process()
        logs = []

        with (
            mock.patch.object(launcher, "is_alive", return_value=False),
            mock.patch(
                "mineai.runtime.ai_launcher.subprocess.Popen",
                return_value=process,
            ),
        ):
            started = launcher.ensure_running(
                lambda: False,
                lambda _message: None,
                lambda message, tag: logs.append((message, tag)),
            )

        self.assertFalse(started)
        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(
            timeout=launcher.TERMINATE_TIMEOUT_SECONDS
        )
        self.assertIsNone(launcher.process)
        self.assertTrue(any("отменён" in message for message, _tag in logs))

    def test_startup_timeout_terminates_owned_process(self) -> None:
        launcher = AiLauncher(_Config())
        launcher.STARTUP_TIMEOUT_SECONDS = 0
        process = self._running_process()

        with (
            mock.patch.object(launcher, "is_alive", return_value=False),
            mock.patch(
                "mineai.runtime.ai_launcher.subprocess.Popen",
                return_value=process,
            ),
        ):
            started = launcher.ensure_running(
                lambda: True,
                lambda _message: None,
                lambda _message, _tag: None,
            )

        self.assertFalse(started)
        process.terminate.assert_called_once_with()
        self.assertIsNone(launcher.process)

    def test_terminate_escalates_to_kill_after_timeout(self) -> None:
        launcher = AiLauncher(_Config())
        process = mock.Mock()
        process.poll.side_effect = [None, 0]
        process.wait.side_effect = [
            subprocess.TimeoutExpired("koboldcpp", 5),
            None,
        ]
        launcher.process = process

        stopped = launcher.terminate()

        self.assertTrue(stopped)
        process.terminate.assert_called_once_with()
        process.kill.assert_called_once_with()
        self.assertEqual(process.wait.call_count, 2)
        self.assertIsNone(launcher.process)

    def test_terminate_keeps_reference_when_process_will_not_die(self) -> None:
        launcher = AiLauncher(_Config())
        process = mock.Mock()
        process.poll.return_value = None
        process.wait.side_effect = subprocess.TimeoutExpired("koboldcpp", 5)
        launcher.process = process

        stopped = launcher.terminate()

        self.assertFalse(stopped)
        process.terminate.assert_called_once_with()
        process.kill.assert_called_once_with()
        self.assertIs(launcher.process, process)


if __name__ == "__main__":
    unittest.main()
