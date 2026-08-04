import threading
import unittest

from mineai.runtime.state import JobState


class JobStateShutdownTests(unittest.TestCase):
    def test_stop_wakes_a_paused_worker(self) -> None:
        state = JobState()
        state.start()
        self.assertTrue(state.pause())

        entered = threading.Event()
        exited = threading.Event()

        def worker() -> None:
            entered.set()
            state.wait_if_paused()
            exited.set()

        thread = threading.Thread(target=worker)
        thread.start()
        self.assertTrue(entered.wait(0.5))
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

        exited = threading.Event()
        thread = threading.Thread(
            target=lambda: (state.wait_if_paused(), exited.set())
        )
        thread.start()
        self.assertFalse(exited.wait(0.05))

        self.assertTrue(state.resume())

        self.assertTrue(exited.wait(0.5))
        thread.join(0.5)
        self.assertTrue(state.should_run())
        state.stop()

    def test_stop_is_idempotent(self) -> None:
        state = JobState(is_running=True, is_paused=True)

        state.stop()
        state.stop()

        snapshot = state.snapshot()
        self.assertFalse(snapshot.is_running)
        self.assertFalse(snapshot.is_paused)


if __name__ == "__main__":
    unittest.main()
