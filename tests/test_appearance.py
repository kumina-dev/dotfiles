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

    def test_wallpaper_source_is_preferred(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(
                directory
            )

            source = (
                directory
                / "nebula.png"
            )

            source.write_bytes(
                b"image"
            )

            source_file = (
                directory
                / "wallpaper-source"
            )

            source_file.write_text(
                f"{source}\n",
                encoding="utf-8",
            )

            current = (
                directory
                / "main.png"
            )

            current.write_bytes(
                b"runtime-copy"
            )

            with (
                patch.object(
                    appearance,
                    "WALLPAPER_SOURCE_FILE",
                    source_file,
                ),
                patch.object(
                    appearance,
                    "CURRENT_WALLPAPER",
                    current,
                ),
            ):
                self.assertEqual(
                    appearance.get_wallpaper(),
                    str(source.resolve()),
                )

    def test_missing_source_falls_back_to_runtime_wallpaper(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(
                directory
            )

            source_file = (
                directory
                / "wallpaper-source"
            )

            source_file.write_text(
                (
                    "/definitely/missing/"
                    "wallpaper.png\n"
                ),
                encoding="utf-8",
            )

            current = (
                directory
                / "main.png"
            )

            current.write_bytes(
                b"runtime-copy"
            )

            with (
                patch.object(
                    appearance,
                    "WALLPAPER_SOURCE_FILE",
                    source_file,
                ),
                patch.object(
                    appearance,
                    "CURRENT_WALLPAPER",
                    current,
                ),
            ):
                self.assertEqual(
                    appearance.get_wallpaper(),
                    str(current.resolve()),
                )

    def test_no_wallpaper_returns_empty_string(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(
                directory
            )

            with (
                patch.object(
                    appearance,
                    "WALLPAPER_SOURCE_FILE",
                    (
                        directory
                        / "wallpaper-source"
                    ),
                ),
                patch.object(
                    appearance,
                    "CURRENT_WALLPAPER",
                    (
                        directory
                        / "main.png"
                    ),
                ),
            ):
                self.assertEqual(
                    appearance.get_wallpaper(),
                    "",
                )


if __name__ == "__main__":
    unittest.main()