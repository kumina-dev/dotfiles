import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "hypr/.config/hypr/scripts"
sys.path.insert(0, str(SCRIPTS))

import lock_auth_status as auth_status


class TouchIndicatorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.proc = self.root / "proc"
        self.pending = self.root / "pam-u2f-authpending"
        self.pending.touch()
        self.process(10, "sh", 20)
        self.process(20, "hyprlock", 1)

    def process(self, pid, name, parent):
        base = self.proc / str(pid)
        (base / "fd").mkdir(parents=True)
        (base / "comm").write_text(name + "\n")
        (base / "status").write_text(f"Name:\t{name}\nPPid:\t{parent}\n")
        return base

    def state(self):
        return auth_status.touch_pending(10, self.pending, self.proc)

    def test_stale_file_does_not_display_touch_request(self):
        self.assertFalse(self.state())

    def test_open_close_and_retry_follow_descriptor_state(self):
        descriptor = self.proc / "20/fd/7"
        for _ in range(2):
            descriptor.symlink_to(self.pending)
            self.assertTrue(self.state())
            descriptor.unlink()
            self.assertFalse(self.state())

    def test_other_processes_cannot_trigger_the_indicator(self):
        for pid, name in ((30, "sudo"), (40, "hyprlock")):
            process = self.process(pid, name, 1)
            (process / "fd/7").symlink_to(self.pending)
        self.assertFalse(self.state())

    def test_missing_file_and_disappearing_descriptor_are_idle(self):
        (self.proc / "20/fd/7").symlink_to(self.root / "missing")
        self.assertFalse(self.state())
        self.pending.unlink()
        self.assertFalse(self.state())

    def test_permission_failure_is_unknown_not_a_password_state(self):
        with patch.object(Path, "iterdir", side_effect=PermissionError):
            self.assertIsNone(self.state())

    def test_missing_ancestor_and_cycles_are_unknown(self):
        (self.proc / "20/comm").write_text("something-else\n")
        self.assertIsNone(self.state())
        (self.proc / "20/status").write_text("PPid:\t10\n")
        self.assertIsNone(self.state())

    def test_hidden_state_uses_transparent_markup_not_empty_output(self):
        self.assertNotIn('alpha="1"', auth_status.render(True))
        for state in (False, None):
            self.assertIn('alpha="1"', auth_status.render(state))

    @unittest.skipUnless(sys.platform == "linux", "Requires Linux /proc")
    def test_actual_parent_descriptors_are_visible_from_child(self):
        # Rename only this isolated fixture process, never the test runner.
        code = '''
import ctypes, json, os, subprocess, sys
from pathlib import Path
assert ctypes.CDLL(None).prctl(15, b"hyprlock", 0, 0, 0) == 0
if (Path("/proc") / str(os.getpid()) / "comm").read_text().strip() != "hyprlock":
    print("PROC_NAME_UNAVAILABLE")
    raise SystemExit(0)
child = "import os, sys; from pathlib import Path; import lock_auth_status as a; print(a.touch_pending(os.getppid(), Path(sys.argv[1])))"
def check():
    return subprocess.check_output([sys.executable, "-c", child, sys.argv[1]], text=True).strip()
results = []
with open(sys.argv[1]):
    results.append(check())
results.append(check())
with open(sys.argv[1]):
    results.append(check())
print(json.dumps(results))
'''
        env = dict(os.environ, PYTHONPATH=str(SCRIPTS), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c", code, str(self.pending)],
                                env=env, text=True, capture_output=True, timeout=5, check=True)
        if result.stdout.strip() == "PROC_NAME_UNAVAILABLE":
            self.skipTest("Container /proc does not reflect the fixture process name")
        self.assertEqual(result.stdout.strip(), '["True", "False", "True"]')


if __name__ == "__main__":
    unittest.main()
