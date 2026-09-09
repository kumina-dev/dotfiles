#!/usr/bin/env python3

import subprocess
from pathlib import Path

from single_instance import acquire


if not acquire(
    "control-center"
):
    raise SystemExit(0)


import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk, GLib

from control_center import theme

from control_center.views.main import (
    MainView,
)


class ControlCenter(Gtk.Window):
    def __init__(self):
        super().__init__(
            title="Kumina Control Center"
        )

        self.set_default_size(
            420,
            480,
        )

        self.set_resizable(False)
        self.set_border_width(12)
        self.set_decorated(False)

        self.connect(
            "destroy",
            self.on_destroy,
        )
        self.connect("key-press-event", self.key_pressed)

        theme.load()

        self.main_view = MainView(
            on_wifi_details=(
                lambda: self.open_settings("wifi")
            ),
            on_bluetooth_details=(
                lambda: self.open_settings("bluetooth")
            ),
            on_sound_settings=lambda: self.open_settings("sound"),
            on_settings=lambda: self.open_settings("overview"),
        )
        self.add(self.main_view)

        GLib.idle_add(
            self.initial_refresh,
        )

        self._refresh_timer = GLib.timeout_add_seconds(
            3,
            self.refresh_state,
        )

    def open_settings(self, page):
        script = Path(__file__).resolve().parent / "open-settings.sh"
        try:
            subprocess.Popen([str(script), page], start_new_session=True)
        except OSError as error:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE,
                text="Could not open Settings",
            )
            dialog.format_secondary_text(str(error))
            dialog.run()
            dialog.destroy()
            return
        self.close()

    def key_pressed(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def on_destroy(self, _window):
        if self._refresh_timer is not None:
            GLib.source_remove(self._refresh_timer)
            self._refresh_timer = None
        Gtk.main_quit()

    def initial_refresh(self):
        self.main_view.refresh()
        return False

    def refresh_state(self):
        self.main_view.refresh()

        return True


window = ControlCenter()
window.show_all()

Gtk.main()
