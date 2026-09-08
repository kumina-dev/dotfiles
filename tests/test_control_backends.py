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


from control_center import (
    media,
    network,
)

from settings_app import (
    network as settings_network,
)


class ControlBackendTests(
    unittest.TestCase
):
    @patch(
        "control_center.network.run"
    )
    def test_control_center_ssid_is_argv_value(
        self,
        mocked_run,
    ):
        ssid = (
            "Cafe Wi-Fi; "
            "still just an SSID"
        )

        network.connect_saved_network(
            ssid
        )

        mocked_run.assert_called_once_with(
            [
                "nmcli",
                "connection",
                "up",
                "id",
                ssid,
            ],
            check=True,
            fallback=(
                "Could not connect to the Wi-Fi network."
            ),
        )

    @patch(
        "control_center.media.run"
    )
    @patch(
        "control_center.media.get_player"
    )
    def test_media_player_is_argv_value(
        self,
        mocked_player,
        mocked_run,
    ):
        player = (
            "spotify.instance;not-shell"
        )

        mocked_player.return_value = (
            player
        )

        media.command(
            "play-pause"
        )

        mocked_run.assert_called_once_with(
            [
                "playerctl",
                f"--player={player}",
                "play-pause",
            ],
            check=True,
            fallback=(
                "Could not control media playback."
            ),
        )

    def test_invalid_media_action_is_rejected(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            media.command(
                "definitely-not-an-action"
            )

    @patch(
        "control_center.network.run"
    )
    def test_wifi_state_write_is_checked(
        self,
        mocked_run,
    ):
        network.set_wifi_enabled(
            True
        )

        mocked_run.assert_called_once_with(
            [
                "nmcli",
                "radio",
                "wifi",
                "on",
            ],
            check=True,
            fallback=(
                "Could not change Wi-Fi state."
            ),
        )

    @patch(
        "settings_app.network.run"
    )
    def test_wifi_password_is_argv_value(
        self,
        mocked_run,
    ):
        ssid = "Test Network"
        password = "spaces;quotes'$remain-data"

        settings_network.connect_new(
            ssid,
            password,
        )

        mocked_run.assert_called_once_with([
            "nmcli",
            "device",
            "wifi",
            "connect",
            ssid,
            "password",
            password,
        ])


if __name__ == "__main__":
    unittest.main()