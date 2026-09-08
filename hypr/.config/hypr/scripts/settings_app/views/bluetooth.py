from gi.repository import Gtk

from control_center import bluetooth
from settings_app.async_utils import (
    run_async,
)


class BluetoothView(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
        )

        self.get_style_context().add_class(
            "content"
        )

        self.available = False
        self.enabled = False
        self._busy = False
        self._updating_switch = False

        title = Gtk.Label(
            label="Bluetooth",
            xalign=0,
        )

        title.get_style_context().add_class(
            "page-title"
        )

        description = Gtk.Label(
            label=(
                "Connect and manage Bluetooth devices."
            ),
            xalign=0,
        )

        description.set_line_wrap(
            True
        )

        description.get_style_context().add_class(
            "page-description"
        )

        self.pack_start(
            title,
            False,
            False,
            0,
        )

        self.pack_start(
            description,
            False,
            False,
            0,
        )

        self.build_adapter_card()
        self.build_devices_card()

    def build_adapter_card(self):
        card = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
        )

        card.get_style_context().add_class(
            "settings-card"
        )

        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        label = Gtk.Label(
            label="Bluetooth",
            xalign=0,
        )

        label.set_hexpand(
            True
        )

        self.adapter_switch = Gtk.Switch()

        self.adapter_switch.connect(
            "state-set",
            self.adapter_state_set,
        )

        row.pack_start(
            label,
            True,
            True,
            0,
        )

        row.pack_end(
            self.adapter_switch,
            False,
            False,
            0,
        )

        card.pack_start(
            row,
            False,
            False,
            0,
        )

        self.pack_start(
            card,
            False,
            False,
            0,
        )

    def build_devices_card(self):
        card = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
        )

        card.get_style_context().add_class(
            "settings-card"
        )

        header = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        title = Gtk.Label(
            label="Devices",
            xalign=0,
        )

        title.get_style_context().add_class(
            "section-title"
        )

        title.set_hexpand(
            True
        )

        self.scan_button = Gtk.Button(
            label="Scan for devices"
        )

        self.scan_button.connect(
            "clicked",
            self.scan_clicked,
        )

        header.pack_start(
            title,
            True,
            True,
            0,
        )

        header.pack_end(
            self.scan_button,
            False,
            False,
            0,
        )

        card.pack_start(
            header,
            False,
            False,
            0,
        )

        self.device_list = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )

        scroller = Gtk.ScrolledWindow()

        scroller.set_policy(
            Gtk.PolicyType.NEVER,
            Gtk.PolicyType.AUTOMATIC,
        )

        scroller.set_min_content_height(
            240
        )

        scroller.add(
            self.device_list
        )

        card.pack_start(
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
            "page-description"
        )

        card.pack_start(
            self.status,
            False,
            False,
            0,
        )

        self.pack_start(
            card,
            True,
            True,
            0,
        )

    def set_busy(
        self,
        busy,
    ):
        self._busy = busy

        self.adapter_switch.set_sensitive(
            self.available
            and not busy
        )

        self.scan_button.set_sensitive(
            self.available
            and self.enabled
            and not busy
        )

        self.device_list.set_sensitive(
            self.enabled
            and not busy
        )

    def clear_devices(self):
        for child in (
            self.device_list
            .get_children()
        ):
            self.device_list.remove(
                child
            )

    def render_devices(
        self,
        devices,
    ):
        self.clear_devices()

        if not devices:
            empty = Gtk.Label(
                label="No devices found.",
                xalign=0,
            )

            empty.get_style_context().add_class(
                "page-description"
            )

            self.device_list.pack_start(
                empty,
                False,
                False,
                4,
            )

            self.device_list.show_all()

            return

        for device in devices:
            self.add_device_row(
                device
            )

        self.device_list.show_all()

    def add_device_row(
        self,
        device,
    ):
        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        row.get_style_context().add_class(
            "network-row"
        )

        info = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=2,
        )

        info.set_hexpand(
            True
        )

        name = Gtk.Label(
            label=device["name"],
            xalign=0,
        )

        if device["connected"]:
            state = "Connected"
        elif device["paired"]:
            state = "Paired"
        else:
            state = "Available"

        detail = Gtk.Label(
            label=(
                f'{state} · '
                f'{device["address"]}'
            ),
            xalign=0,
        )

        detail.get_style_context().add_class(
            "page-description"
        )

        info.pack_start(
            name,
            False,
            False,
            0,
        )

        info.pack_start(
            detail,
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

        if device["connected"]:
            action_label = "Disconnect"
        elif device["paired"]:
            action_label = "Connect"
        else:
            action_label = "Pair"

        action = Gtk.Button(
            label=action_label
        )

        action.connect(
            "clicked",
            lambda _button, item=device:
                self.device_action(
                    item
                ),
        )

        row.pack_end(
            action,
            False,
            False,
            0,
        )

        if device["paired"]:
            forget = Gtk.Button(
                label="Forget"
            )

            forget.get_style_context().add_class(
                "network-action"
            )

            forget.connect(
                "clicked",
                lambda _button, item=device:
                    self.forget_device(
                        item
                    ),
            )

            row.pack_end(
                forget,
                False,
                False,
                0,
            )

        self.device_list.pack_start(
            row,
            False,
            False,
            0,
        )

    def refresh(self):
        self.status.set_text(
            "Loading Bluetooth…"
        )

        self.set_busy(
            True
        )

        run_async(
            lambda: bluetooth.get_state(
                include_devices=True
            ),
            self.apply_state,
            self.show_error,
        )

    def apply_state(
        self,
        state,
    ):
        self.available = state[
            "available"
        ]

        self.enabled = state[
            "enabled"
        ]

        self._updating_switch = True

        self.adapter_switch.set_active(
            self.enabled
        )

        self._updating_switch = False

        self.render_devices(
            state["devices"]
        )

        self.set_busy(
            False
        )

        if not self.available:
            self.status.set_text(
                "No Bluetooth adapter found."
            )

        elif not self.enabled:
            self.status.set_text(
                "Bluetooth is turned off."
            )

        else:
            self.status.set_text("")

        return False

    def adapter_state_set(
        self,
        _switch,
        desired_state,
    ):
        if self._updating_switch:
            return False

        if self._busy:
            return True

        self.set_busy(
            True
        )

        self.status.set_text(
            (
                "Turning Bluetooth on…"
                if desired_state
                else "Turning Bluetooth off…"
            )
        )

        run_async(
            lambda: bluetooth.set_enabled(
                desired_state
            ),
            self.adapter_toggle_finished,
            self.show_error,
        )

        return True

    def adapter_toggle_finished(
        self,
        _result,
    ):
        self.refresh()

        return False

    def scan_clicked(
        self,
        _button,
    ):
        self.set_busy(
            True
        )

        self.status.set_text(
            "Scanning for devices…"
        )

        run_async(
            lambda: bluetooth.scan(
                5
            ),
            self.scan_finished,
            self.show_error,
        )

    def scan_finished(
        self,
        devices,
    ):
        self.render_devices(
            devices
        )

        self.set_busy(
            False
        )

        self.status.set_text(
            "Scan complete."
        )

        return False

    def device_action(
        self,
        device,
    ):
        address = device[
            "address"
        ]

        if device["connected"]:
            operation = (
                bluetooth.disconnect
            )
            status = (
                f'Disconnecting '
                f'{device["name"]}…'
            )

        elif device["paired"]:
            operation = (
                bluetooth.connect
            )
            status = (
                f'Connecting '
                f'{device["name"]}…'
            )

        else:
            operation = (
                bluetooth.pair
            )
            status = (
                f'Pairing '
                f'{device["name"]}…'
            )

        self.set_busy(
            True
        )

        self.status.set_text(
            status
        )

        run_async(
            lambda: operation(
                address
            ),
            self.device_action_finished,
            self.show_error,
        )

    def forget_device(
        self,
        device,
    ):
        self.set_busy(
            True
        )

        self.status.set_text(
            (
                f'Forgetting '
                f'{device["name"]}…'
            )
        )

        run_async(
            lambda: bluetooth.forget(
                device["address"]
            ),
            self.device_action_finished,
            self.show_error,
        )

    def device_action_finished(
        self,
        _result,
    ):
        self.refresh()

        return False

    def show_error(
        self,
        error,
    ):
        self.set_busy(
            False
        )

        self.status.set_text(
            str(error)
        )

        return False