import subprocess
from pathlib import Path

from gi.repository import Gtk, GLib

from .. import network
from ..widgets.switch import CompactSwitch
from ..async_utils import run_async


class WifiView(Gtk.Box):
    def __init__(
        self,
        on_back,
        on_connectivity_changed,
        on_open_settings=None,
    ):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=14,
        )

        self.on_back = on_back
        self.on_connectivity_changed = (
            on_connectivity_changed
        )
        self.on_open_settings = (
            on_open_settings
        )

        self._refreshing = False
        self._action_error = None

        self.build()

    def build(self):
        self.build_header()

        self.wifi_networks = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6,
        )

        scroller = Gtk.ScrolledWindow()

        scroller.set_policy(
            Gtk.PolicyType.NEVER,
            Gtk.PolicyType.AUTOMATIC,
        )

        scroller.set_overlay_scrolling(True)

        scroller.add(
            self.wifi_networks
        )

        self.pack_start(
            scroller,
            True,
            True,
            0,
        )

        self.status = Gtk.Label(
            xalign=0,
        )

        self.status.set_line_wrap(
            True
        )

        self.status.get_style_context().add_class(
            "secondary"
        )

        self.pack_start(
            self.status,
            False,
            False,
            0,
        )

        self.settings_button = Gtk.Button(
            label="Wi-Fi Settings  ›"
        )

        self.settings_button.get_style_context().add_class(
            "settings-link"
        )

        self.settings_button.set_halign(
            Gtk.Align.FILL
        )

        self.settings_button.connect(
            "clicked",
            self.open_wifi_settings,
        )

        self.pack_start(
            self.settings_button,
            False,
            False,
            0,
        )

    def build_header(self):
        header = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        back = Gtk.Button(label="‹")
        back.set_can_focus(False)

        back.connect(
            "clicked",
            lambda _: self.on_back(),
        )

        title = Gtk.Label(
            label="Wi-Fi"
        )

        title.set_halign(
            Gtk.Align.START
        )

        title.get_style_context().add_class(
            "title"
        )

        self.toggle = CompactSwitch()

        self.toggle.connect_toggled(
            self.toggle_changed
        )

        header.pack_start(
            back,
            False,
            False,
            0,
        )

        header.pack_start(
            title,
            True,
            True,
            0,
        )

        header.pack_end(
            self.toggle,
            False,
            False,
            0,
        )

        self.pack_start(
            header,
            False,
            False,
            0,
        )

    def clear_networks(self):
        for child in (
            self.wifi_networks
            .get_children()
        ):
            self.wifi_networks.remove(
                child
            )

    def show_message(
        self,
        message,
    ):
        self.clear_networks()

        label = Gtk.Label(
            label=message,
            xalign=0,
        )

        label.get_style_context().add_class(
            "secondary"
        )

        self.wifi_networks.pack_start(
            label,
            False,
            False,
            20,
        )

        self.wifi_networks.show_all()

    def refresh(self):
        if self._refreshing:
            return

        self._refreshing = True

        self.toggle.set_sensitive(
            False
        )

        self.show_message(
            "Loading networks..."
        )

        run_async(
            self.load_wifi_state,
            self.apply_wifi_state,
            self.refresh_failed,
        )

    def refresh_failed(
        self,
        error,
    ):
        self._refreshing = False

        self.toggle.set_sensitive(
            True
        )

        self.show_message(
            "Could not load Wi-Fi networks"
        )

        if not self._action_error:
            self.status.set_text(
                str(error)
            )

        return False

    def load_wifi_state(self):
        enabled = (
            network.is_wifi_enabled()
        )

        if not enabled:
            return {
                "enabled": False,
                "networks": [],
            }

        return {
            "enabled": True,
            "networks": (
                network.get_networks()
            ),
        }

    def apply_wifi_state(
        self,
        state,
    ):
        self._refreshing = False

        self.toggle.set_sensitive(
            True
        )

        self.clear_networks()

        enabled = state["enabled"]

        self.toggle.set_active(
            enabled,
            emit=False,
        )

        self.status.set_text(
            self._action_error or ""
        )

        if not enabled:
            self.show_disabled_state()

            return False

        for wifi_network in (
            state["networks"]
        ):
            self.add_network(
                wifi_network["ssid"],
                wifi_network["signal"],
                wifi_network["security"],
                wifi_network["connected"],
            )

        self.wifi_networks.show_all()

        return False

    def show_disabled_state(self):
        label = Gtk.Label(
            label="Wi-Fi is turned off"
        )

        label.get_style_context().add_class(
            "secondary"
        )

        self.wifi_networks.pack_start(
            label,
            False,
            False,
            20,
        )

        self.wifi_networks.show_all()

    def add_network(
        self,
        ssid,
        signal,
        security,
        connected,
    ):
        button = Gtk.Button()
        button.set_can_focus(False)

        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        icon = Gtk.Label(
            label=self.signal_icon(
                signal
            )
        )

        info = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=2,
        )

        name = Gtk.Label(
            label=ssid
        )

        name.set_halign(
            Gtk.Align.START
        )

        info.pack_start(
            name,
            False,
            False,
            0,
        )

        if connected:
            status = Gtk.Label(
                label="Connected"
            )

            status.set_halign(
                Gtk.Align.START
            )

            status.get_style_context().add_class(
                "secondary"
            )

            info.pack_start(
                status,
                False,
                False,
                0,
            )

        row.pack_start(
            icon,
            False,
            False,
            0,
        )

        row.pack_start(
            info,
            True,
            True,
            0,
        )

        if security and security != "--":
            lock = Gtk.Label(
                label="󰌾"
            )

            row.pack_end(
                lock,
                False,
                False,
                0,
            )

        if connected:
            check = Gtk.Label(
                label="✓"
            )

            row.pack_end(
                check,
                False,
                False,
                0,
            )

            button.get_style_context().add_class(
                "connected-network"
            )

        button.add(row)

        button.connect(
            "clicked",
            self.network_clicked,
            ssid,
            connected,
        )

        self.wifi_networks.pack_start(
            button,
            False,
            False,
            0,
        )

    def signal_icon(self, signal):
        if signal >= 75:
            return "󰤨"

        if signal >= 50:
            return "󰤥"

        if signal >= 25:
            return "󰤢"

        return "󰤟"

    def network_clicked(
        self,
        button,
        ssid,
        connected,
    ):
        if connected:
            return

        self._action_error = None

        self.status.set_text(
            f"Connecting to {ssid}…"
        )

        button.set_sensitive(
            False
        )

        run_async(
            lambda: (
                network.connect_saved_network(
                    ssid
                )
            ),
            lambda result: (
                self.network_connection_finished(
                    button,
                    result,
                )
            ),
            lambda error: (
                self.network_connection_failed(
                    button,
                    error,
                )
            ),
        )

    def network_connection_finished(
        self,
        button,
        _result,
    ):
        self._action_error = None

        button.set_sensitive(
            True
        )

        self.status.set_text("")

        self.refresh()

        self.on_connectivity_changed()

        return False

    def network_connection_failed(
        self,
        button,
        error,
    ):
        button.set_sensitive(
            True
        )

        self._action_error = str(
            error
        )

        self.status.set_text(
            self._action_error
        )

        return False

    def toggle_changed(
        self,
        switch,
    ):
        enabled = (
            switch.get_active()
        )

        self._action_error = None

        self.status.set_text(
            (
                "Turning Wi-Fi on…"
                if enabled
                else "Turning Wi-Fi off…"
            )
        )

        self.toggle.set_sensitive(
            False
        )

        run_async(
            lambda: (
                network.set_wifi_enabled(
                    enabled
                )
            ),
            self.toggle_finished,
            lambda error: self.toggle_failed(
                enabled,
                error,
            ),
        )

    def toggle_finished(
        self,
        _result,
    ):
        self._action_error = None

        self.toggle.set_sensitive(
            True
        )

        self.status.set_text("")

        self.refresh()

        self.on_connectivity_changed()

        return False

    def toggle_failed(
        self,
        requested_state,
        error,
    ):
        self.toggle.set_sensitive(
            True
        )

        self.toggle.set_active(
            not requested_state,
            emit=False,
        )

        self._action_error = str(
            error
        )

        self.status.set_text(
            self._action_error
        )

        return False

    def open_wifi_settings(
        self,
        _button,
    ):
        script = (
            Path.home()
            / ".config"
            / "hypr"
            / "scripts"
            / "open-settings.sh"
        )

        try:
            subprocess.Popen(
                [
                    str(script),
                    "wifi",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as error:
            self.status.set_text(
                (
                    "Could not open Wi-Fi Settings: "
                    f"{error}"
                )
            )

            return

        if self.on_open_settings:
            self.on_open_settings()