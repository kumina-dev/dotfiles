import json
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


from kumina_common.process import (
    CommandError,
)

from settings_app import (
    display,
    keyboard,
    mouse,
    network,
)


class DisplayTests(
    unittest.TestCase
):
    def test_monitor_data_is_normalized(
        self,
    ):
        monitor = display._monitor_from_json({
            "name": "DP-2",
            "description": "Test Display",
            "width": 1920,
            "height": 1080,
            "refreshRate": 180.0,
            "x": 100,
            "y": 200,
            "scale": 1.25,
            "availableModes": [
                "1920x1080@180.00Hz",
                "1920x1080@60.00Hz",
            ],
        })

        self.assertEqual(
            monitor["name"],
            "DP-2",
        )

        self.assertEqual(
            monitor["mode"],
            "1920x1080@180.00",
        )

        self.assertEqual(
            monitor["modes"],
            [
                "1920x1080@180.00",
                "1920x1080@60.00",
            ],
        )

        self.assertEqual(
            monitor["scale"],
            1.25,
        )

        self.assertEqual(
            monitor["x"],
            100,
        )

        self.assertEqual(
            monitor["y"],
            200,
        )

    @patch(
        "settings_app.display._command"
    )
    def test_invalid_monitor_json_is_rejected(
        self,
        mocked_command,
    ):
        mocked_command.return_value = (
            "not-json"
        )

        with self.assertRaisesRegex(
            display.DisplayError,
            "invalid monitor data",
        ):
            display.get_monitors()

    def test_render_config_contains_fallback(
        self,
    ):
        rendered = display.render_config([
            {
                "name": "DP-2",
                "mode": (
                    "1920x1080@180.00"
                ),
                "x": 0,
                "y": 0,
                "scale": 1.25,
            },
        ])

        self.assertIn(
            'output = "DP-2"',
            rendered,
        )

        self.assertIn(
            'position = "0x0"',
            rendered,
        )

        self.assertIn(
            "scale = 1.25",
            rendered,
        )

        self.assertIn(
            'output = ""',
            rendered,
        )

        self.assertIn(
            'mode = "preferred"',
            rendered,
        )

    @patch(
        "settings_app.display.get_monitors"
    )
    def test_invalid_display_mode_is_rejected(
        self,
        mocked_monitors,
    ):
        mocked_monitors.return_value = [
            {
                "name": "DP-2",
                "description": "Display",
                "mode": (
                    "1920x1080@180.00"
                ),
                "modes": [
                    "1920x1080@180.00",
                ],
                "x": 0,
                "y": 0,
                "scale": 1.0,
            },
        ]

        with self.assertRaisesRegex(
            display.DisplayError,
            "mode is no longer available",
        ):
            display.apply_monitor(
                "DP-2",
                "640x480@60.00",
                1.0,
            )

    @patch(
        "settings_app.display.get_monitors"
    )
    def test_invalid_display_scale_is_rejected(
        self,
        mocked_monitors,
    ):
        mocked_monitors.return_value = [
            {
                "name": "DP-2",
                "description": "Display",
                "mode": (
                    "1920x1080@180.00"
                ),
                "modes": [
                    "1920x1080@180.00",
                ],
                "x": 0,
                "y": 0,
                "scale": 1.0,
            },
        ]

        with self.assertRaisesRegex(
            display.DisplayError,
            "between 50% and 300%",
        ):
            display.apply_monitor(
                "DP-2",
                "1920x1080@180.00",
                4.0,
            )

    @patch(
        "settings_app.display._command"
    )
    @patch(
        "settings_app.display.get_monitors"
    )
    def test_apply_display_writes_config(
        self,
        mocked_monitors,
        mocked_command,
    ):
        mocked_monitors.return_value = [
            {
                "name": "DP-2",
                "description": "Display",
                "mode": (
                    "1920x1080@180.00"
                ),
                "modes": [
                    "1920x1080@180.00",
                    "1920x1080@60.00",
                ],
                "x": 0,
                "y": 0,
                "scale": 1.0,
            },
        ]

        with tempfile.TemporaryDirectory() as directory:
            config = (
                Path(directory)
                / "generated"
                / "monitors.lua"
            )

            with patch.object(
                display,
                "GENERATED_CONFIG",
                config,
            ):
                result = (
                    display.apply_monitor(
                        "DP-2",
                        "1920x1080@60.00",
                        1.25,
                    )
                )

            rendered = config.read_text(
                encoding="utf-8"
            )

        self.assertEqual(
            result["scale"],
            1.25,
        )

        self.assertIn(
            (
                'mode = '
                '"1920x1080@60.00"'
            ),
            rendered,
        )

        self.assertIn(
            "scale = 1.25",
            rendered,
        )

        mocked_command.assert_called_once_with(
            "hyprctl",
            "reload",
        )


class KeyboardTests(
    unittest.TestCase
):
    def test_keyboard_options_replace_group_toggle(
        self,
    ):
        options = keyboard._build_options(
            (
                "caps:escape,"
                "grp:win_space_toggle,"
                "compose:ralt"
            ),
            True,
        )

        self.assertEqual(
            options,
            (
                "caps:escape,"
                "compose:ralt,"
                "grp:alt_shift_toggle"
            ),
        )

    def test_keyboard_without_secondary_has_no_group_toggle(
        self,
    ):
        options = keyboard._build_options(
            (
                "caps:escape,"
                "grp:alt_shift_toggle"
            ),
            False,
        )

        self.assertEqual(
            options,
            "caps:escape",
        )

    def test_keyboard_render_config(
        self,
    ):
        rendered = keyboard.render_config(
            "fi",
            "us",
            30,
            500,
            True,
            "caps:escape",
        )

        self.assertIn(
            'kb_layout = "fi,us"',
            rendered,
        )

        self.assertIn(
            (
                'kb_options = '
                '"caps:escape,'
                'grp:alt_shift_toggle"'
            ),
            rendered,
        )

        self.assertIn(
            "repeat_rate = 30",
            rendered,
        )

        self.assertIn(
            "repeat_delay = 500",
            rendered,
        )

        self.assertIn(
            "numlock_by_default = true",
            rendered,
        )

    def test_invalid_keyboard_repeat_value(
        self,
    ):
        with self.assertRaisesRegex(
            keyboard.KeyboardError,
            "Invalid keyboard repeat setting",
        ):
            keyboard.apply_settings(
                "fi",
                None,
                "fast",
                500,
                False,
            )

    def test_keyboard_repeat_range(
        self,
    ):
        with self.assertRaisesRegex(
            keyboard.KeyboardError,
            "between 1 and 100",
        ):
            keyboard.apply_settings(
                "fi",
                None,
                101,
                500,
                False,
            )

    @patch(
        "settings_app.keyboard._command"
    )
    @patch(
        "settings_app.keyboard._get_string"
    )
    def test_apply_keyboard_writes_config(
        self,
        mocked_string,
        mocked_command,
    ):
        mocked_string.return_value = (
            "caps:escape,"
            "grp:win_space_toggle"
        )

        with tempfile.TemporaryDirectory() as directory:
            config = (
                Path(directory)
                / "generated"
                / "keyboard.lua"
            )

            with patch.object(
                keyboard,
                "GENERATED_CONFIG",
                config,
            ):
                keyboard.apply_settings(
                    "fi",
                    "us",
                    30,
                    500,
                    True,
                )

            rendered = config.read_text(
                encoding="utf-8"
            )

        self.assertIn(
            'kb_layout = "fi,us"',
            rendered,
        )

        self.assertIn(
            (
                "caps:escape,"
                "grp:alt_shift_toggle"
            ),
            rendered,
        )

        self.assertNotIn(
            "grp:win_space_toggle",
            rendered,
        )

        mocked_command.assert_called_once_with(
            "hyprctl",
            "reload",
        )


class MouseTests(
    unittest.TestCase
):
    def test_mouse_render_config(
        self,
    ):
        rendered = mouse.render_config(
            -0.25,
            True,
            False,
            1.5,
        )

        self.assertIn(
            "sensitivity = -0.25",
            rendered,
        )

        self.assertIn(
            "natural_scroll = true",
            rendered,
        )

        self.assertIn(
            "left_handed = false",
            rendered,
        )

        self.assertIn(
            "scroll_factor = 1.5",
            rendered,
        )

    def test_invalid_mouse_value(
        self,
    ):
        with self.assertRaisesRegex(
            mouse.MouseError,
            "Invalid mouse setting",
        ):
            mouse.apply_settings(
                "fast",
                False,
                False,
                1.0,
            )

    def test_mouse_sensitivity_range(
        self,
    ):
        with self.assertRaisesRegex(
            mouse.MouseError,
            "between -1.0 and 1.0",
        ):
            mouse.apply_settings(
                2.0,
                False,
                False,
                1.0,
            )

    def test_mouse_scroll_range(
        self,
    ):
        with self.assertRaisesRegex(
            mouse.MouseError,
            "between 0.0 and 2.0",
        ):
            mouse.apply_settings(
                0.0,
                False,
                False,
                3.0,
            )

    @patch(
        "settings_app.mouse._command"
    )
    def test_apply_mouse_writes_config(
        self,
        mocked_command,
    ):
        with tempfile.TemporaryDirectory() as directory:
            config = (
                Path(directory)
                / "generated"
                / "mouse.lua"
            )

            with patch.object(
                mouse,
                "GENERATED_CONFIG",
                config,
            ):
                mouse.apply_settings(
                    0.25,
                    True,
                    False,
                    1.5,
                )

            rendered = config.read_text(
                encoding="utf-8"
            )

        self.assertIn(
            "sensitivity = 0.25",
            rendered,
        )

        self.assertIn(
            "natural_scroll = true",
            rendered,
        )

        self.assertIn(
            "scroll_factor = 1.5",
            rendered,
        )

        mocked_command.assert_called_once_with(
            "hyprctl",
            "reload",
        )


class WifiTests(
    unittest.TestCase
):
    @patch(
        "settings_app.network.get_saved_profiles"
    )
    @patch(
        "settings_app.network.output"
    )
    def test_networks_are_sorted(
        self,
        mocked_output,
        mocked_profiles,
    ):
        mocked_output.return_value = (
            "*:Current:75:WPA2\n"
            ":Saved:50:WPA2\n"
            ":Open:90:--\n"
        )

        mocked_profiles.return_value = {
            "Saved": {
                "uuid": "saved-uuid",
                "name": "Saved",
            },
        }

        networks = (
            network.get_networks()
        )

        self.assertEqual(
            [
                item["ssid"]
                for item in networks
            ],
            [
                "Current",
                "Saved",
                "Open",
            ],
        )

        self.assertTrue(
            networks[0]["connected"]
        )

        self.assertTrue(
            networks[1]["saved"]
        )

        self.assertFalse(
            networks[2]["secured"]
        )

    @patch(
        "settings_app.network.get_wifi_device"
    )
    def test_disconnect_requires_wifi_device(
        self,
        mocked_device,
    ):
        mocked_device.return_value = ""

        with self.assertRaisesRegex(
            CommandError,
            "No Wi-Fi device",
        ):
            network.disconnect()

    @patch(
        "settings_app.network.get_networks"
    )
    @patch(
        "settings_app.network.get_current_ssid"
    )
    @patch(
        "settings_app.network.is_wifi_enabled"
    )
    def test_disabled_wifi_does_not_scan(
        self,
        mocked_enabled,
        mocked_ssid,
        mocked_networks,
    ):
        mocked_enabled.return_value = (
            False
        )

        state = network.get_state()

        self.assertEqual(
            state,
            {
                "enabled": False,
                "ssid": "",
                "networks": [],
            },
        )

        mocked_ssid.assert_not_called()
        mocked_networks.assert_not_called()


if __name__ == "__main__":
    unittest.main()