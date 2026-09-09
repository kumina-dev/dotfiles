from gi.repository import Gtk, Pango

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
        self._action_error = None

        self.get_style_context().add_class(
            "card"
        )

        self.build()

    def build(self):
        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )
        row.set_homogeneous(True)

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

        wifi_details.set_tooltip_text("Open Wi-Fi settings")
        wifi_details.get_accessible().set_name("Open Wi-Fi settings")

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

        bluetooth_details.set_tooltip_text("Open Bluetooth settings")
        bluetooth_details.get_accessible().set_name("Open Bluetooth settings")

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

        self.status = Gtk.Label(
            xalign=0,
        )

        self.status.set_single_line_mode(True)
        self.status.set_ellipsize(Pango.EllipsizeMode.END)
        self.status.set_max_width_chars(36)

        for button in (self.wifi_button, self.bluetooth_button):
            label = button.get_child()
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_single_line_mode(True)
            label.set_max_width_chars(12)

        self.status.get_style_context().add_class(
            "secondary"
        )

        self.pack_start(
            self.status,
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
        self.wifi_button.set_tooltip_text(
            f"Wi-Fi: {wifi_name or 'not connected'}. Click to turn off."
            if wifi_active else "Wi-Fi off. Click to turn on."
        )
        self.wifi_button.get_accessible().set_name("Toggle Wi-Fi")

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
        self.bluetooth_button.set_tooltip_text(
            f"Bluetooth: {device or 'not connected'}. Click to turn off."
            if bluetooth_active else "Bluetooth off. Click to turn on."
        )
        self.bluetooth_button.get_accessible().set_name("Toggle Bluetooth")

        self.set_active_style(
            self.bluetooth_button,
            bluetooth_active,
        )

        self.show_error(
            self._action_error
        )

        return False

    def refresh_failed(
        self,
        error,
    ):
        self._refreshing = False

        if not self._action_error:
            self.show_error(
                str(error)
            )

        return False

    def toggle_wifi(
        self,
        _button,
    ):
        self._action_error = None

        self.show_error("")

        self.wifi_button.set_sensitive(
            False
        )

        run_async(
            network.toggle_wifi,
            self.wifi_toggle_finished,
            self.wifi_toggle_failed,
        )

    def wifi_toggle_finished(
        self,
        _result,
    ):
        self._action_error = None

        self.wifi_button.set_sensitive(
            True
        )

        self.show_error("")

        self.refresh()

        return False

    def wifi_toggle_failed(
        self,
        error,
    ):
        self._action_error = str(
            error
        )

        self.wifi_button.set_sensitive(
            True
        )

        self.show_error(
            self._action_error
        )

        return False

    def toggle_bluetooth(
        self,
        _button,
    ):
        self._action_error = None

        self.show_error("")

        self.bluetooth_button.set_sensitive(
            False
        )

        run_async(
            bluetooth.toggle,
            self.bluetooth_toggle_finished,
            self.bluetooth_toggle_failed,
        )

    def bluetooth_toggle_finished(
        self,
        _result,
    ):
        self._action_error = None

        self.bluetooth_button.set_sensitive(
            True
        )

        self.show_error("")

        self.refresh()

        return False

    def bluetooth_toggle_failed(
        self,
        error,
    ):
        self._action_error = str(
            error
        )

        self.bluetooth_button.set_sensitive(
            True
        )

        self.show_error(
            self._action_error
        )

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

    def show_error(
        self,
        message,
    ):
        self.status.set_text(
            message or ""
        )
        self.status.set_tooltip_text(message or None)
