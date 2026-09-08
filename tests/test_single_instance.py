import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = (
    Path(__file__)
    .resolve()
    .parents[1]
    / "hypr"
    / ".config"
    / "hypr"
    / "scripts"
)


class SingleInstanceTests(
    unittest.TestCase
):
    def test_second_process_cannot_acquire_lock(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ.copy()

            env[
                "XDG_RUNTIME_DIR"
            ] = directory

            env[
                "PYTHONDONTWRITEBYTECODE"
            ] = "1"

            holder_code = f"""
import sys
import time

sys.path.insert(
    0,
    {str(SCRIPTS)!r},
)

from single_instance import acquire

if not acquire(
    "unit-test"
):
    raise SystemExit(2)

print(
    "locked",
    flush=True,
)

time.sleep(30)
"""

            contender_code = f"""
import sys

sys.path.insert(
    0,
    {str(SCRIPTS)!r},
)

from single_instance import acquire

raise SystemExit(
    0
    if not acquire(
        "unit-test"
    )
    else 1
)
"""

            released_code = f"""
import sys

sys.path.insert(
    0,
    {str(SCRIPTS)!r},
)

from single_instance import acquire

raise SystemExit(
    0
    if acquire(
        "unit-test"
    )
    else 1
)
"""

            holder = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    holder_code,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )

            try:
                ready = (
                    holder.stdout
                    .readline()
                    .strip()
                )

                self.assertEqual(
                    ready,
                    "locked",
                )

                contender = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        contender_code,
                    ],
                    text=True,
                    capture_output=True,
                    env=env,
                    timeout=5,
                )

                self.assertEqual(
                    contender.returncode,
                    0,
                    contender.stderr,
                )

            finally:
                holder.terminate()

                try:
                    holder.wait(
                        timeout=5
                    )
                except subprocess.TimeoutExpired:
                    holder.kill()
                    holder.wait()

            released = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    released_code,
                ],
                text=True,
                capture_output=True,
                env=env,
                timeout=5,
            )

            self.assertEqual(
                released.returncode,
                0,
                released.stderr,
            )


if __name__ == "__main__":
    unittest.main()