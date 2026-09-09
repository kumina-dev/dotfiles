#!/usr/bin/env python3

import sys

from single_instance import acquire


if not acquire(
    "settings"
):
    raise SystemExit(0)


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

from settings_app.views.display import (
    DisplayView,
)

from settings_app.views.input import (
    InputView,
)

from settings_app.views.bluetooth import (
    BluetoothView,
)

from settings_app.views.appearance import (
    AppearanceView,
)

from settings_app.views.about import (
    AboutView,
)


NAVIGATION = (
    (
        None,
        (
            (
                "󰋜",
                "Overview",
                "overview",
            ),
        ),
    ),
    (
        "Connectivity",
        (
            (
                "󰤨",
                "Wi-Fi",
                "wifi",
            ),
            (
                "",
                "Bluetooth",
                "bluetooth",
            ),
        ),
    ),
    (
        "System",
        (
            (
                "󰕾",
                "Sound",
                "sound",
            ),
            (
                "󰍹",
                "Display",
                "display",
            ),
            (
                "󰌌",
                "Input",
                "input",
            ),
        ),
    ),
    (
        "Personalization",
        (
            (
                "󰏘",
                "Appearance",
                "appearance",
            ),
        ),
    ),
    (
        "Information",
        (
            (
                "󰋼",
                "About",
                "about",
            ),
        ),
    ),
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
            900,
            620,
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

        self.overview_view = OverviewView(
            self.show_page
        )
        self.wifi_view = WifiView()
        self.sound_view = SoundView()
        self.display_view = DisplayView()
        self.input_view = InputView()
        self.bluetooth_view = BluetoothView()
        self.appearance_view = AppearanceView()
        self.about_view = AboutView()

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

        self.stack.add_named(
            self.display_view,
            "display",
        )

        self.stack.add_named(
            self.input_view,
            "input",
        )

        self.stack.add_named(
            self.bluetooth_view,
            "bluetooth",
        )

        self.stack.add_named(
            self.appearance_view,
            "appearance",
        )

        self.stack.add_named(
            self.about_view,
            "about",
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

        initial_page = {
            "keyboard": "input",
            "mouse": "input",
        }.get(
            initial_page,
            initial_page,
        )

        if initial_page not in (
            "overview",
            "wifi",
            "sound",
            "display",
            "input",
            "bluetooth",
            "appearance",
            "about",
        ):
            initial_page = "overview"

        self.initial_page = initial_page

    def create_sidebar(self):
        sidebar = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4,
        )

        sidebar.set_size_request(
            210,
            -1,
        )

        sidebar.get_style_context().add_class(
            "sidebar"
        )

        title = Gtk.Label(
            label="Settings",
            xalign=0,
        )

        title.get_style_context().add_class(
            "sidebar-title"
        )

        subtitle = Gtk.Label(
            label="System & desktop",
            xalign=0,
        )

        subtitle.get_style_context().add_class(
            "sidebar-subtitle"
        )

        sidebar.pack_start(
            title,
            False,
            False,
            0,
        )

        sidebar.pack_start(
            subtitle,
            False,
            False,
            0,
        )

        self.sidebar_buttons = {}

        for (
            section,
            items,
        ) in NAVIGATION:
            if section is not None:
                section_label = Gtk.Label(
                    label=section,
                    xalign=0,
                )

                section_label.get_style_context().add_class(
                    "sidebar-section"
                )

                sidebar.pack_start(
                    section_label,
                    False,
                    False,
                    0,
                )

            for (
                icon,
                label,
                page,
            ) in items:
                self.add_sidebar_button(
                    sidebar,
                    icon,
                    label,
                    page,
                )

        return sidebar

    def add_sidebar_button(
        self,
        sidebar,
        icon,
        label,
        page,
    ):
        button = Gtk.Button()

        button.set_halign(
            Gtk.Align.FILL
        )

        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        icon_label = Gtk.Label(
            label=icon
        )

        icon_label.set_size_request(
            22,
            -1,
        )

        icon_label.get_style_context().add_class(
            "sidebar-icon"
        )

        text = Gtk.Label(
            label=label,
            xalign=0,
        )

        text.set_hexpand(
            True
        )

        row.pack_start(
            icon_label,
            False,
            False,
            0,
        )

        row.pack_start(
            text,
            True,
            True,
            0,
        )

        button.add(
            row
        )

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
        page = {
            "keyboard": "input",
            "mouse": "input",
        }.get(
            page,
            page,
        )

        if page == "overview":
            child = self.overview_view

        elif page == "wifi":
            child = self.wifi_view

        elif page == "sound":
            child = self.sound_view

        elif page == "display":
            child = self.display_view

        elif page == "input":
            child = self.input_view

        elif page == "bluetooth":
            child = self.bluetooth_view

        elif page == "appearance":
            child = self.appearance_view

        elif page == "about":
            child = self.about_view

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

        if page == "display":
            self.display_view.refresh()

        if page == "input":
            self.input_view.refresh()

        if page == "bluetooth":
            self.bluetooth_view.refresh()

        if page == "appearance":
            self.appearance_view.refresh()


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
