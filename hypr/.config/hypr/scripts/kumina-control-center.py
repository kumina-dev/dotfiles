#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from control_center import theme

from control_center.views.main import (
    MainView,
)

from control_center.views.wifi import (
    WifiView,
)


class ControlCenter(Gtk.Window):
    def __init__(self):
        super().__init__(
            title="Kumina Control Center"
        )

        self.set_default_size(
            420,
            520,
        )

        self.set_resizable(False)
        self.set_border_width(18)

        self.connect(
            "destroy",
            Gtk.main_quit,
        )

        theme.load()

        self.stack = Gtk.Stack()

        self.stack.set_transition_type(
            Gtk.StackTransitionType.SLIDE_LEFT_RIGHT
        )

        self.stack.set_transition_duration(
            180
        )

        self.main_view = MainView(
            on_wifi_details=(
                self.show_wifi_view
            ),
        )

        self.wifi_view = WifiView(
            on_back=self.show_main_view,
            on_connectivity_changed=(
                self.main_view.connectivity.refresh
            ),
        )

        self.stack.add_named(
            self.main_view,
            "main",
        )

        self.stack.add_named(
            self.wifi_view,
            "wifi",
        )

        self.stack.set_visible_child_name(
            "main"
        )

        self.add(self.stack)

        GLib.idle_add(
            self.initial_refresh,
        )

        GLib.timeout_add_seconds(
            3,
            self.refresh_state,
        )

    def show_main_view(self):
        self.stack.set_visible_child_name(
            "main"
        )


    def show_wifi_view(self):
        self.stack.set_visible_child_name(
            "wifi"
        )

        self.wifi_view.refresh()

    def initial_refresh(self):
        self.main_view.refresh()
        return False

    def refresh_state(self):
        self.main_view.refresh()

        return True


window = ControlCenter()
window.show_all()

Gtk.main()