import sys
import tempfile
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


from settings_app import appearance


class AppearanceTests(
    unittest.TestCase
):
    @patch(
        "settings_app.appearance.get_state"
    )
    @patch(
        "settings_app.appearance.output"
    )
    def test_apply_uses_checked_process(
        self,
        mocked_output,
        mocked_state,
    ):
        mocked_state.return_value = {
            "mode": "dark",
            "wallpaper": "test",
        }

        with tempfile.TemporaryDirectory() as directory:
            directory = Path(
                directory
            )

            wallpaper = (
                directory
                / "wallpaper.png"
            )

            script = (
                directory
                / "set-wallpaper"
            )

            wallpaper.write_bytes(
                b"test"
            )

            script.write_text(
                "#!/bin/sh\n",
                encoding="utf-8",
            )

            with (
                patch.object(
                    appearance,
                    "SET_WALLPAPER",
                    script,
                ),
            ):
                appearance.apply_settings(
                    str(wallpaper),
                    "dark",
                )

            mocked_output.assert_called_once_with(
                [
                    str(script),
                    str(wallpaper),
                    "dark",
                ],
                timeout=30,
                check=True,
                error_type=(
                    appearance.AppearanceError
                ),
                fallback=(
                    "Could not apply appearance settings."
                ),
            )


if __name__ == "__main__":
    unittest.main()