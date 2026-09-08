import subprocess
from pathlib import Path

from gi.repository import Gtk

from .. import bluetooth
from ..async_utils import run_async
from ..widgets.switch import CompactSwitch


class BluetoothView(Gtk.Box):
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

        self.available = False
        self.enabled = False
        self._refreshing = False

        self.build()

    def build(self):
        self.build_header()

        self.devices = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6,
        )

        scroller = Gtk.ScrolledWindow()

        scroller.set_policy(
            Gtk.PolicyType.NEVER,
            Gtk.PolicyType.AUTOMATIC,
        )

        scroller.set_overlay_scrolling(
            True
        )

        scroller.add(
            self.devices
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
            label="Bluetooth Settings  ›"
        )

        self.settings_button.get_style_context().add_class(
            "settings-link"
        )

        self.settings_button.set_halign(
            Gtk.Align.FILL
        )

        self.settings_button.connect(
            "clicked",
            self.open_bluetooth_settings,
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

        back = Gtk.Button(
            label="‹"
        )

        back.set_can_focus(
            False
        )

        back.connect(
            "clicked",
            lambda _: self.on_back(),
        )

        title = Gtk.Label(
            label="Bluetooth"
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

    def clear_devices(self):
        for child in (
            self.devices.get_children()
        ):
            self.devices.remove(
                child
            )

    def show_message(
        self,
        message,
    ):
        self.clear_devices()

        label = Gtk.Label(
            label=message,
            xalign=0,
        )

        label.get_style_context().add_class(
            "secondary"
        )

        self.devices.pack_start(
            label,
            False,
            False,
            20,
        )

        self.devices.show_all()

    def refresh(self):
        if self._refreshing:
            return

        self._refreshing = True

        self.status.set_text("")

        self.show_message(
            "Loading devices..."
        )

        run_async(
            lambda: bluetooth.get_state(
                include_devices=True
            ),
            self.apply_state,
            self.refresh_failed,
        )

    def apply_state(
        self,
        state,
    ):
        self._refreshing = False

        self.available = state[
            "available"
        ]

        self.enabled = state[
            "enabled"
        ]

        self.toggle.set_sensitive(
            self.available
        )

        self.toggle.set_active(
            self.enabled,
            emit=False,
        )

        if not self.available:
            self.show_message(
                "No Bluetooth adapter found"
            )

            return False

        if not self.enabled:
            self.show_message(
                "Bluetooth is turned off"
            )

            return False

        paired = [
            device
            for device in state[
                "devices"
            ]
            if device["paired"]
        ]

        if not paired:
            self.show_message(
                "No paired devices"
            )

            return False

        self.clear_devices()

        for device in paired:
            self.add_device(
                device
            )

        self.devices.show_all()

        return False

    def refresh_failed(
        self,
        error,
    ):
        self._refreshing = False

        self.show_message(
            "Could not load Bluetooth devices"
        )

        self.status.set_text(
            str(error)
        )

        return False

    def add_device(
        self,
        device,
    ):
        button = Gtk.Button()

        button.set_can_focus(
            False
        )

        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        icon = Gtk.Label(
            label=""
        )

        info = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=2,
        )

        name = Gtk.Label(
            label=device["name"],
            xalign=0,
        )

        status = Gtk.Label(
            label=(
                "Connected"
                if device["connected"]
                else "Paired"
            ),
            xalign=0,
        )

        status.get_style_context().add_class(
            "secondary"
        )

        info.pack_start(
            name,
            False,
            False,
            0,
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

        if device["connected"]:
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

        button.add(
            row
        )

        button.connect(
            "clicked",
            self.device_clicked,
            device,
        )

        self.devices.pack_start(
            button,
            False,
            False,
            0,
        )

    def device_clicked(
        self,
        button,
        device,
    ):
        button.set_sensitive(
            False
        )

        if device["connected"]:
            action = (
                bluetooth.disconnect
            )

            self.status.set_text(
                f'Disconnecting {device["name"]}…'
            )
        else:
            action = (
                bluetooth.connect
            )

            self.status.set_text(
                f'Connecting {device["name"]}…'
            )

        run_async(
            lambda: action(
                device["address"]
            ),
            self.device_action_finished,
            lambda error: self.device_action_failed(
                button,
                error,
            ),
        )

    def device_action_finished(
        self,
        _result,
    ):
        self.status.set_text("")

        self.refresh()

        self.on_connectivity_changed()

        return False

    def device_action_failed(
        self,
        button,
        error,
    ):
        button.set_sensitive(
            True
        )

        self.status.set_text(
            str(error)
        )

        return False

    def toggle_changed(
        self,
        switch,
    ):
        enabled = (
            switch.get_active()
        )

        self.toggle.set_sensitive(
            False
        )

        self.status.set_text(
            (
                "Turning Bluetooth on…"
                if enabled
                else "Turning Bluetooth off…"
            )
        )

        run_async(
            lambda: bluetooth.set_enabled(
                enabled
            ),
            self.toggle_finished,
            self.toggle_failed,
        )

    def toggle_finished(
        self,
        _result,
    ):
        self.status.set_text("")

        self.refresh()

        self.on_connectivity_changed()

        return False

    def toggle_failed(
        self,
        error,
    ):
        self.toggle.set_sensitive(
            True
        )

        self.status.set_text(
            str(error)
        )

        return False

    def open_bluetooth_settings(
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

        subprocess.Popen(
            [
                str(script),
                "bluetooth",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        if self.on_open_settings:
            self.on_open_settings()