from gi.repository import Gtk

from settings_app import keyboard
from settings_app.async_utils import (
    run_async,
)


NONE_LAYOUT = "__none__"


class KeyboardView(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
        )

        self._loaded = False

        self.get_style_context().add_class(
            "content"
        )

        title = Gtk.Label(
            label="Keyboard",
            xalign=0,
        )

        title.get_style_context().add_class(
            "page-title"
        )

        description = Gtk.Label(
            label=(
                "Configure keyboard layouts and key repeat behaviour."
            ),
            xalign=0,
        )

        description.set_line_wrap(True)

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

        card = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=14,
        )

        card.get_style_context().add_class(
            "settings-card"
        )

        self.primary_combo = self.add_combo_row(
            card,
            "Primary layout",
        )

        self.secondary_combo = self.add_combo_row(
            card,
            "Secondary layout",
        )

        self.repeat_rate = self.add_spin_row(
            card,
            "Repeat rate",
            1,
            100,
            1,
        )

        self.repeat_delay = self.add_spin_row(
            card,
            "Repeat delay",
            100,
            2000,
            50,
        )

        numlock_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        numlock_label = Gtk.Label(
            label="Num Lock on startup",
            xalign=0,
        )

        numlock_label.set_hexpand(
            True
        )

        self.numlock_switch = Gtk.Switch()

        numlock_row.pack_start(
            numlock_label,
            True,
            True,
            0,
        )

        numlock_row.pack_end(
            self.numlock_switch,
            False,
            False,
            0,
        )

        card.pack_start(
            numlock_row,
            False,
            False,
            0,
        )

        self.apply_button = Gtk.Button(
            label="Apply"
        )

        self.apply_button.connect(
            "clicked",
            self.apply_clicked,
        )

        card.pack_start(
            self.apply_button,
            False,
            False,
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
            False,
            False,
            0,
        )

    @staticmethod
    def add_combo_row(
        parent,
        label,
    ):
        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        row_label = Gtk.Label(
            label=label,
            xalign=0,
        )

        row_label.set_hexpand(
            True
        )

        combo = Gtk.ComboBoxText()

        combo.set_size_request(
            260,
            -1,
        )

        row.pack_start(
            row_label,
            True,
            True,
            0,
        )

        row.pack_end(
            combo,
            False,
            False,
            0,
        )

        parent.pack_start(
            row,
            False,
            False,
            0,
        )

        return combo

    @staticmethod
    def add_spin_row(
        parent,
        label,
        minimum,
        maximum,
        step,
    ):
        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        row_label = Gtk.Label(
            label=label,
            xalign=0,
        )

        row_label.set_hexpand(
            True
        )

        adjustment = Gtk.Adjustment(
            value=minimum,
            lower=minimum,
            upper=maximum,
            step_increment=step,
            page_increment=step * 5,
        )

        spin = Gtk.SpinButton(
            adjustment=adjustment,
        )

        spin.set_numeric(
            True
        )

        row.pack_start(
            row_label,
            True,
            True,
            0,
        )

        row.pack_end(
            spin,
            False,
            False,
            0,
        )

        parent.pack_start(
            row,
            False,
            False,
            0,
        )

        return spin

    def set_controls_sensitive(
        self,
        sensitive,
    ):
        self.primary_combo.set_sensitive(
            sensitive
        )

        self.secondary_combo.set_sensitive(
            sensitive
        )

        self.repeat_rate.set_sensitive(
            sensitive
        )

        self.repeat_delay.set_sensitive(
            sensitive
        )

        self.numlock_switch.set_sensitive(
            sensitive
        )

        self.apply_button.set_sensitive(
            sensitive
        )

    def refresh(self):
        self.set_controls_sensitive(
            False
        )

        self.status.set_text(
            "Loading keyboard settings…"
        )

        run_async(
            keyboard.get_state,
            self.apply_state,
            self.show_error,
        )

    def apply_state(
        self,
        state,
    ):
        self.primary_combo.remove_all()
        self.secondary_combo.remove_all()

        layouts = list(
            state["available_layouts"]
        )

        known_codes = {
            layout["code"]
            for layout in layouts
        }

        for current in (
            state["primary"],
            state["secondary"],
        ):
            if (
                current
                and current not in known_codes
            ):
                layouts.append({
                    "code": current,
                    "description": current,
                })

        for layout in layouts:
            code = layout["code"]
            description = (
                layout["description"]
            )

            label = (
                f"{description} ({code})"
            )

            self.primary_combo.append(
                code,
                label,
            )

            self.secondary_combo.append(
                code,
                label,
            )

        self.secondary_combo.prepend(
            NONE_LAYOUT,
            "None",
        )

        self.primary_combo.set_active_id(
            state["primary"]
        )

        self.secondary_combo.set_active_id(
            state["secondary"]
            or NONE_LAYOUT
        )

        self.repeat_rate.set_value(
            state["repeat_rate"]
        )

        self.repeat_delay.set_value(
            state["repeat_delay"]
        )

        self.numlock_switch.set_active(
            state["numlock"]
        )

        self._loaded = True

        self.set_controls_sensitive(
            True
        )

        self.status.set_text("")

        return False

    def apply_clicked(
        self,
        _button,
    ):
        primary = (
            self.primary_combo
            .get_active_id()
        )

        secondary = (
            self.secondary_combo
            .get_active_id()
        )

        if secondary == NONE_LAYOUT:
            secondary = None

        if not primary:
            self.status.set_text(
                "Select a primary keyboard layout."
            )
            return

        self.set_controls_sensitive(
            False
        )

        self.status.set_text(
            "Applying…"
        )

        run_async(
            lambda: keyboard.apply_settings(
                primary,
                secondary,
                self.repeat_rate.get_value_as_int(),
                self.repeat_delay.get_value_as_int(),
                self.numlock_switch.get_active(),
            ),
            self.apply_finished,
            self.show_error,
        )

    def apply_finished(
        self,
        _result,
    ):
        self.status.set_text(
            "Applied."
        )

        self.set_controls_sensitive(
            True
        )

        return False

    def show_error(
        self,
        error,
    ):
        self.status.set_text(
            str(error)
        )

        self.set_controls_sensitive(
            self._loaded
        )

        return False