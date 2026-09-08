import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = (
    Path(__file__)
    .resolve()
    .parents[1]
    / "hypr"
    / ".config"
    / "hypr"
    / "scripts"
)

sys.path.insert(
    0,
    str(SCRIPTS),
)


from kumina_common import process


class CustomError(RuntimeError):
    pass


class ProcessTests(
    unittest.TestCase
):
    @patch(
        "kumina_common.process.subprocess.run"
    )
    def test_run_uses_argument_list(
        self,
        mocked_run,
    ):
        mocked_run.return_value = (
            subprocess.CompletedProcess(
                args=[
                    "tool",
                    "value",
                ],
                returncode=0,
                stdout="ok\n",
                stderr="",
            )
        )

        result = process.run([
            "tool",
            "value",
        ])

        self.assertEqual(
            result.stdout,
            "ok\n",
        )

        mocked_run.assert_called_once_with(
            [
                "tool",
                "value",
            ],
            text=True,
            capture_output=True,
            timeout=None,
        )

    @patch(
        "kumina_common.process.subprocess.run"
    )
    def test_output_strips_stdout(
        self,
        mocked_run,
    ):
        mocked_run.return_value = (
            subprocess.CompletedProcess(
                args=["tool"],
                returncode=0,
                stdout="hello\n",
                stderr="",
            )
        )

        self.assertEqual(
            process.output(
                ["tool"]
            ),
            "hello",
        )

    @patch(
        "kumina_common.process.subprocess.run"
    )
    def test_output_returns_default_on_failure(
        self,
        mocked_run,
    ):
        mocked_run.return_value = (
            subprocess.CompletedProcess(
                args=["tool"],
                returncode=1,
                stdout="",
                stderr="failure",
            )
        )

        self.assertEqual(
            process.output(
                ["tool"],
                default="fallback",
            ),
            "fallback",
        )

    @patch(
        "kumina_common.process.subprocess.run"
    )
    def test_checked_command_raises_domain_error(
        self,
        mocked_run,
    ):
        mocked_run.return_value = (
            subprocess.CompletedProcess(
                args=["tool"],
                returncode=1,
                stdout="",
                stderr="specific failure",
            )
        )

        with self.assertRaisesRegex(
            CustomError,
            "specific failure",
        ):
            process.output(
                ["tool"],
                check=True,
                error_type=CustomError,
                fallback="Fallback.",
            )

    @patch(
        "kumina_common.process.subprocess.run"
    )
    def test_missing_program_is_reported(
        self,
        mocked_run,
    ):
        mocked_run.side_effect = (
            FileNotFoundError()
        )

        with self.assertRaisesRegex(
            process.CommandError,
            "missing-tool is not installed",
        ):
            process.run([
                "missing-tool",
            ])

    @patch(
        "kumina_common.process.subprocess.run"
    )
    def test_timeout_is_reported(
        self,
        mocked_run,
    ):
        mocked_run.side_effect = (
            subprocess.TimeoutExpired(
                cmd=["tool"],
                timeout=2,
            )
        )

        with self.assertRaisesRegex(
            process.CommandError,
            "timed out",
        ):
            process.run(
                ["tool"],
                timeout=2,
            )


if __name__ == "__main__":
    unittest.main()