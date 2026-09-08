#!/usr/bin/env python3

import sys
import gi

gi.require_version(
    "Gtk",
    "3.0",
)

from gi.repository import Gtk

from settings_app import theme

from settings_app.views.overview import (
    OverviewView,
)

from settings_app.views.wifi import (
    WifiView,
)

from settings_app.views.sound import (
    SoundView,
)


class SettingsWindow(Gtk.Window):
    def __init__(
            self,
            initial_page="overview",
        ):
        super().__init__(
            title="Kumina Settings"
        )

        self.set_default_size(
            820,
            560,
        )

        self.set_resizable(False)

        self.connect(
            "destroy",
            Gtk.main_quit,
        )

        theme.load()

        root = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=0,
        )

        root.get_style_context().add_class(
            "settings-root"
        )

        self.sidebar = self.create_sidebar()

        self.stack = Gtk.Stack()

        self.stack.set_transition_type(
            Gtk.StackTransitionType.CROSSFADE
        )

        self.stack.set_transition_duration(
            140
        )

        self.overview_view = OverviewView()
        self.wifi_view = WifiView()
        self.sound_view = SoundView()

        self.stack.add_named(
            self.overview_view,
            "overview",
        )

        self.stack.add_named(
            self.wifi_view,
            "wifi",
        )

        self.stack.add_named(
            self.sound_view,
            "sound",
        )

        root.pack_start(
            self.sidebar,
            False,
            False,
            0,
        )

        root.pack_start(
            self.stack,
            True,
            True,
            0,
        )

        self.add(root)

        if initial_page not in (
            "overview",
            "wifi",
            "sound",
        ):
            initial_page = "overview"

        self.initial_page = initial_page

    def create_sidebar(self):
        sidebar = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=6,
        )

        sidebar.set_size_request(
            220,
            -1,
        )

        sidebar.get_style_context().add_class(
            "sidebar"
        )

        title = Gtk.Label(
            label="Settings"
        )

        title.set_halign(
            Gtk.Align.START
        )

        title.get_style_context().add_class(
            "sidebar-title"
        )

        sidebar.pack_start(
            title,
            False,
            False,
            0,
        )

        self.sidebar_buttons = {}

        self.add_sidebar_button(
            sidebar,
            "Overview",
            "overview",
        )

        self.add_sidebar_button(
            sidebar,
            "Wi-Fi",
            "wifi",
        )

        self.add_sidebar_button(
            sidebar,
            "Sound",
            "sound",
        )

        separator = Gtk.Separator(
            orientation=Gtk.Orientation.HORIZONTAL
        )

        sidebar.pack_start(
            separator,
            False,
            False,
            8,
        )

        for label in (
            "Bluetooth",
            "Display",
            "Appearance",
            "Keyboard",
        ):
            button = Gtk.Button(
                label=label
            )

            button.set_sensitive(False)

            child = button.get_child()

            if isinstance(child, Gtk.Label):
                child.set_halign(
                    Gtk.Align.START
                )
                child.set_xalign(0)

            sidebar.pack_start(
                button,
                False,
                False,
                0,
            )

        return sidebar

    def add_sidebar_button(
        self,
        sidebar,
        label,
        page,
    ):
        button = Gtk.Button(
            label=label
        )

        button.set_halign(
            Gtk.Align.FILL
        )

        child = button.get_child()

        if isinstance(child, Gtk.Label):
            child.set_halign(
                Gtk.Align.START
            )
            child.set_xalign(0)

        button.connect(
            "clicked",
            lambda _button: self.show_page(
                page
            ),
        )

        sidebar.pack_start(
            button,
            False,
            False,
            0,
        )

        self.sidebar_buttons[
            page
        ] = button

    def show_page(
        self,
        page,
    ):
        if page == "overview":
            child = self.overview_view

        elif page == "wifi":
            child = self.wifi_view

        elif page == "sound":
            child = self.sound_view

        else:
            print(
                "Unknown page:",
                page,
            )
            return
        
        self.stack.set_visible_child(
            child
        )

        for (
            name,
            button,
        ) in self.sidebar_buttons.items():
            context = (
                button.get_style_context()
            )

            if name == page:
                context.add_class(
                    "active"
                )
            else:
                context.remove_class(
                    "active"
                )

        if page == "wifi":
            self.wifi_view.refresh()


initial_page = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "overview"
)

window = SettingsWindow(
    initial_page=initial_page
)

window.show_all()

window.show_page(
    window.initial_page
)

Gtk.main()
