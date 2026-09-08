#!/usr/bin/env python3

import subprocess

from single_instance import acquire


if not acquire(
    "power-menu"
):
    raise SystemExit(0)


import gi

gi.require_version(
    "Gtk",
    "3.0",
)

gi.require_version(
    "Gdk",
    "3.0",
)

from gi.repository import (
    Gdk,
    Gtk,
)

from control_center import theme


ACTIONS = {
    "lock": [
        "hyprlock",
    ],
    "sleep": [
        "systemctl",
        "suspend",
    ],
    "logout": [
        "hyprctl",
        "dispatch",
        "exit",
    ],
    "restart": [
        "systemctl",
        "reboot",
    ],
    "shutdown": [
        "systemctl",
        "poweroff",
    ],
}


CONFIRMATIONS = {
    "logout": {
        "title": "Log out?",
        "description": (
            "Open applications will be closed."
        ),
        "button": "Log Out",
    },
    "restart": {
        "title": "Restart?",
        "description": (
            "The computer will restart and "
            "open applications will be closed."
        ),
        "button": "Restart",
    },
    "shutdown": {
        "title": "Shut down?",
        "description": (
            "The computer will turn off and "
            "open applications will be closed."
        ),
        "button": "Shut Down",
    },
}


class PowerMenu(Gtk.Window):
    def __init__(self):
        super().__init__(
            title="Kumina Power Menu"
        )

        self.pending_action = None

        self.set_default_size(
            320,
            330,
        )

        self.set_resizable(
            False
        )

        self.set_decorated(
            False
        )

        self.set_border_width(
            12
        )

        self.set_skip_taskbar_hint(
            True
        )

        self.set_skip_pager_hint(
            True
        )

        self.connect(
            "destroy",
            Gtk.main_quit,
        )

        self.connect(
            "key-press-event",
            self.key_pressed,
        )

        theme.load()

        self.stack = Gtk.Stack()

        self.stack.set_transition_type(
            Gtk.StackTransitionType.SLIDE_LEFT_RIGHT
        )

        self.stack.set_transition_duration(
            160
        )

        self.main_view = (
            self.build_main_view()
        )

        self.confirm_view = (
            self.build_confirm_view()
        )

        self.stack.add_named(
            self.main_view,
            "main",
        )

        self.stack.add_named(
            self.confirm_view,
            "confirm",
        )

        self.stack.set_visible_child_name(
            "main"
        )

        self.add(
            self.stack
        )

    def build_main_view(self):
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )

        title = Gtk.Label(
            label="Power",
            xalign=0,
        )

        title.get_style_context().add_class(
            "title"
        )

        box.pack_start(
            title,
            False,
            False,
            2,
        )

        self.first_button = self.add_action(
            box,
            "󰌾",
            "Lock",
            lambda _button: self.execute_action(
                "lock"
            ),
        )

        self.add_action(
            box,
            "󰒲",
            "Sleep",
            lambda _button: self.execute_action(
                "sleep"
            ),
        )

        separator = Gtk.Separator(
            orientation=Gtk.Orientation.HORIZONTAL
        )

        box.pack_start(
            separator,
            False,
            False,
            4,
        )

        self.add_action(
            box,
            "󰍃",
            "Log Out",
            lambda _button: self.show_confirmation(
                "logout"
            ),
        )

        self.add_action(
            box,
            "󰜉",
            "Restart",
            lambda _button: self.show_confirmation(
                "restart"
            ),
        )

        self.add_action(
            box,
            "󰐥",
            "Shut Down",
            lambda _button: self.show_confirmation(
                "shutdown"
            ),
        )

        return box

    @staticmethod
    def add_action(
        parent,
        icon,
        label,
        callback,
    ):
        button = Gtk.Button()

        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        icon_label = Gtk.Label(
            label=icon
        )

        text = Gtk.Label(
            label=label,
            xalign=0,
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
            callback,
        )

        parent.pack_start(
            button,
            False,
            False,
            0,
        )

        return button

    def build_confirm_view(self):
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=14,
        )

        self.confirm_title = Gtk.Label(
            xalign=0,
        )

        self.confirm_title.get_style_context().add_class(
            "title"
        )

        self.confirm_description = Gtk.Label(
            xalign=0,
        )

        self.confirm_description.set_line_wrap(
            True
        )

        self.confirm_description.get_style_context().add_class(
            "secondary"
        )

        box.pack_start(
            self.confirm_title,
            False,
            False,
            0,
        )

        box.pack_start(
            self.confirm_description,
            False,
            False,
            0,
        )

        spacer = Gtk.Box()

        box.pack_start(
            spacer,
            True,
            True,
            0,
        )

        buttons = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
        )

        cancel = Gtk.Button(
            label="Cancel"
        )

        cancel.connect(
            "clicked",
            lambda _button: self.show_main(),
        )

        self.confirm_button = Gtk.Button()

        self.confirm_button.get_style_context().add_class(
            "active"
        )

        self.confirm_button.connect(
            "clicked",
            self.confirm_clicked,
        )

        buttons.pack_start(
            cancel,
            True,
            True,
            0,
        )

        buttons.pack_start(
            self.confirm_button,
            True,
            True,
            0,
        )

        box.pack_end(
            buttons,
            False,
            False,
            0,
        )

        return box

    def show_confirmation(
        self,
        action,
    ):
        config = CONFIRMATIONS[
            action
        ]

        self.pending_action = action

        self.confirm_title.set_text(
            config["title"]
        )

        self.confirm_description.set_text(
            config["description"]
        )

        self.confirm_button.set_label(
            config["button"]
        )

        self.stack.set_visible_child_name(
            "confirm"
        )

        self.confirm_button.grab_focus()

    def confirm_clicked(
        self,
        _button,
    ):
        if self.pending_action is None:
            return

        self.execute_action(
            self.pending_action
        )

    def show_main(self):
        self.pending_action = None

        self.stack.set_visible_child_name(
            "main"
        )

        self.first_button.grab_focus()

    def execute_action(
        self,
        action,
    ):
        command = ACTIONS[
            action
        ]

        try:
            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as error:
            self.show_error(
                str(error)
            )

            return

        self.close()

    def show_error(
        self,
        message,
    ):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Power action failed",
        )

        dialog.format_secondary_text(
            message
        )

        dialog.run()
        dialog.destroy()

    def key_pressed(
        self,
        _window,
        event,
    ):
        if event.keyval != Gdk.KEY_Escape:
            return False

        if (
            self.stack.get_visible_child_name()
            == "confirm"
        ):
            self.show_main()
        else:
            self.close()

        return True


window = PowerMenu()

window.show_all()

window.first_button.grab_focus()

Gtk.main()