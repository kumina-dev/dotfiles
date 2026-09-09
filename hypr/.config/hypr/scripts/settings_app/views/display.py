from gi.repository import Gtk

from settings_app import display
from settings_app.async_utils import (
    run_async,
)


class DisplayView(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
        )

        self.get_style_context().add_class(
            "content"
        )

        self.monitors = []

        title = Gtk.Label(
            label="Display",
            xalign=0,
        )

        title.get_style_context().add_class(
            "page-title"
        )

        description = Gtk.Label(
            label=(
                "Choose the active display mode and scale. "
                "Changes are saved for future sessions."
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

        card = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
        )

        card.get_style_context().add_class(
            "settings-card"
        )

        self.monitor_combo = (
            self.add_combo_row(
                card,
                "Display",
            )
        )

        self.mode_combo = (
            self.add_combo_row(
                card,
                "Resolution / refresh rate",
            )
        )

        self.scale_combo = (
            self.add_combo_row(
                card,
                "Scale",
            )
        )

        self.monitor_combo.connect(
            "changed",
            self.monitor_changed,
        )

        self.apply_button = Gtk.Button(
            label="Apply"
        )

        self.apply_button.set_halign(
            Gtk.Align.END
        )

        self.apply_button.get_style_context().add_class(
            "primary-action"
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

        self.status.get_style_context().add_class(
            "settings-status"
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

        row.get_style_context().add_class(
            "settings-row"
        )

        row_label = Gtk.Label(
            label=label,
            xalign=0,
        )

        row_label.get_style_context().add_class(
            "settings-row-title"
        )

        row_label.set_hexpand(
            True
        )

        combo = Gtk.ComboBoxText()

        combo.get_style_context().add_class(
            "settings-control"
        )

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

    def set_controls_sensitive(
        self,
        sensitive,
    ):
        self.monitor_combo.set_sensitive(
            sensitive
        )

        self.mode_combo.set_sensitive(
            sensitive
        )

        self.scale_combo.set_sensitive(
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
            "Loading displays…"
        )

        run_async(
            display.get_monitors,
            self.apply_state,
            self.show_error,
        )

    def apply_state(
        self,
        monitors,
    ):
        self.monitors = monitors

        self.monitor_combo.remove_all()

        for monitor in monitors:
            self.monitor_combo.append(
                monitor["name"],
                monitor["description"],
            )

        if not monitors:
            self.mode_combo.remove_all()
            self.scale_combo.remove_all()

            self.status.set_text(
                "No active displays found."
            )

            self.set_controls_sensitive(
                False
            )

            return False

        self.monitor_combo.set_active_id(
            monitors[0]["name"]
        )

        self.set_controls_sensitive(
            True
        )

        self.status.set_text("")

        return False

    def selected_monitor(self):
        name = (
            self.monitor_combo
            .get_active_id()
        )

        return next(
            (
                monitor
                for monitor in self.monitors
                if monitor["name"] == name
            ),
            None,
        )

    def monitor_changed(
        self,
        _combo,
    ):
        monitor = self.selected_monitor()

        self.mode_combo.remove_all()
        self.scale_combo.remove_all()

        if monitor is None:
            return

        for mode in monitor["modes"]:
            self.mode_combo.append(
                mode,
                mode,
            )

        self.mode_combo.set_active_id(
            monitor["mode"]
        )

        scales = set(
            display.COMMON_SCALES
        )

        scales.add(
            monitor["scale"]
        )

        for scale in sorted(scales):
            scale_id = f"{scale:g}"

            self.scale_combo.append(
                scale_id,
                f"{scale * 100:g}%",
            )

        self.scale_combo.set_active_id(
            f'{monitor["scale"]:g}'
        )

    def apply_clicked(
        self,
        _button,
    ):
        monitor = self.selected_monitor()

        mode = (
            self.mode_combo
            .get_active_id()
        )

        scale = (
            self.scale_combo
            .get_active_id()
        )

        if (
            monitor is None
            or mode is None
            or scale is None
        ):
            return

        self.set_controls_sensitive(
            False
        )

        self.status.set_text(
            "Applying…"
        )

        run_async(
            lambda: display.apply_monitor(
                monitor["name"],
                mode,
                scale,
            ),
            self.apply_finished,
            self.show_error,
        )

    def apply_finished(
        self,
        _monitor,
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
            bool(self.monitors)
        )

        return False