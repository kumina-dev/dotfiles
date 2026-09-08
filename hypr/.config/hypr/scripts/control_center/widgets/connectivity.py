from gi.repository import Gtk

from .. import bluetooth
from .. import network
from ..async_utils import run_async


class ConnectivityCard(Gtk.Box):
    def __init__(
        self,
        on_wifi_details,
        on_bluetooth_details,
    ):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )

        self.on_wifi_details = on_wifi_details
        self.on_bluetooth_details = on_bluetooth_details
        self._refreshing = False

        self.get_style_context().add_class(
            "card"
        )

        self.build()

    def build(self):
        title = Gtk.Label(
            label="Connectivity"
        )

        title.set_halign(
            Gtk.Align.START
        )

        title.get_style_context().add_class(
            "section-title"
        )

        self.pack_start(
            title,
            False,
            False,
            0,
        )

        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        wifi_group = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=4,
        )

        self.wifi_button = Gtk.Button(
            label="󰤨  Wi-Fi"
        )

        self.wifi_button.set_hexpand(
            True
        )

        wifi_details = Gtk.Button(
            label="›"
        )

        wifi_details.set_can_focus(
            False
        )

        self.wifi_button.connect(
            "clicked",
            self.toggle_wifi,
        )

        wifi_details.connect(
            "clicked",
            lambda _: self.on_wifi_details(),
        )

        wifi_group.pack_start(
            self.wifi_button,
            True,
            True,
            0,
        )

        wifi_group.pack_end(
            wifi_details,
            False,
            False,
            0,
        )

        bluetooth_group = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=4,
        )

        self.bluetooth_button = Gtk.Button(
            label="  Bluetooth"
        )

        self.bluetooth_button.set_hexpand(
            True
        )

        bluetooth_details = Gtk.Button(
            label="›"
        )

        bluetooth_details.set_can_focus(
            False
        )

        self.bluetooth_button.connect(
            "clicked",
            self.toggle_bluetooth,
        )

        bluetooth_details.connect(
            "clicked",
            lambda _: self.on_bluetooth_details(),
        )

        bluetooth_group.pack_start(
            self.bluetooth_button,
            True,
            True,
            0,
        )

        bluetooth_group.pack_end(
            bluetooth_details,
            False,
            False,
            0,
        )

        row.pack_start(
            wifi_group,
            True,
            True,
            0,
        )

        row.pack_start(
            bluetooth_group,
            True,
            True,
            0,
        )

        self.pack_start(
            row,
            False,
            False,
            0,
        )

    def refresh(self):
        if self._refreshing:
            return

        self._refreshing = True

        run_async(
            self.load_state,
            self.apply_state,
            self.refresh_failed,
        )

    def load_state(self):
        wifi = network.get_state()
        bt = bluetooth.get_state()

        return {
            "wifi_active": wifi["enabled"],
            "wifi_name": wifi["ssid"],
            "bluetooth_active": bt["enabled"],
            "bluetooth_device": bt["device"],
        }

    def apply_state(
        self,
        state,
    ):
        self._refreshing = False

        wifi_active = (
            state["wifi_active"]
        )

        wifi_name = state["wifi_name"]

        if wifi_active:
            if wifi_name:
                wifi_label = (
                    f"󰤨 {wifi_name}"
                )
            else:
                wifi_label = (
                    "󰤨  Wi-Fi"
                )
        else:
            wifi_label = (
                "󰤭  Wi-Fi"
            )

        self.wifi_button.set_label(
            wifi_label
        )

        self.set_active_style(
            self.wifi_button,
            wifi_active,
        )

        bluetooth_active = (
            state["bluetooth_active"]
        )

        device = (
            state["bluetooth_device"]
        )

        if bluetooth_active:
            if device:
                bluetooth_label = (
                    f"  {device}"
                )
            else:
                bluetooth_label = (
                    "  Bluetooth"
                )
        else:
            bluetooth_label = (
                "󰂲  Bluetooth"
            )

        self.bluetooth_button.set_label(
            bluetooth_label
        )

        self.set_active_style(
            self.bluetooth_button,
            bluetooth_active,
        )

        return False

    def refresh_failed(
        self,
        _error,
    ):
        self._refreshing = False
        return False

    def toggle_wifi(
        self,
        _button,
    ):
        self.wifi_button.set_sensitive(
            False
        )

        run_async(
            network.toggle_wifi,
            self.wifi_toggle_finished,
        )

    def wifi_toggle_finished(
        self,
        _result,
    ):
        self.wifi_button.set_sensitive(
            True
        )

        self.refresh()

        return False

    def toggle_bluetooth(
        self,
        _button,
    ):
        self.bluetooth_button.set_sensitive(
            False
        )

        run_async(
            bluetooth.toggle,
            self.bluetooth_toggle_finished,
        )

    def bluetooth_toggle_finished(
        self,
        _result,
    ):
        self.bluetooth_button.set_sensitive(
            True
        )

        self.refresh()

        return False

    @staticmethod
    def set_active_style(
        button,
        active,
    ):
        context = (
            button.get_style_context()
        )

        if active:
            context.add_class(
                "active"
            )
        else:
            context.remove_class(
                "active"
            )