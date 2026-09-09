from gi.repository import Gtk

from settings_app import mouse
from settings_app.async_utils import (
    run_async,
)


class MouseView(Gtk.Box):
    def __init__(
        self,
        embedded=False,
    ):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
        )

        self._loaded = False

        if embedded:
            self.get_style_context().add_class(
                "input-section"
            )
        else:
            self.get_style_context().add_class(
                "content"
            )

        title = Gtk.Label(
            label="Mouse",
            xalign=0,
        )

        title.get_style_context().add_class(
            (
                "subpage-title"
                if embedded
                else "page-title"
            )
        )

        description = Gtk.Label(
            label=(
                "Configure pointer and scrolling behaviour."
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
            spacing=16,
        )

        card.get_style_context().add_class(
            "settings-card"
        )

        self.sensitivity = self.add_scale_row(
            card,
            "Pointer speed",
            -1.0,
            1.0,
            0.05,
            2,
        )

        self.scroll_factor = self.add_scale_row(
            card,
            "Scroll speed",
            0.0,
            2.0,
            0.05,
            2,
        )

        self.natural_scroll = self.add_switch_row(
            card,
            "Natural scrolling",
        )

        self.left_handed = self.add_switch_row(
            card,
            "Left-handed buttons",
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
    def add_scale_row(
        parent,
        label,
        minimum,
        maximum,
        step,
        digits,
    ):
        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=16,
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

        row_label.set_size_request(
            150,
            -1,
        )

        scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            minimum,
            maximum,
            step,
        )

        scale.get_style_context().add_class(
            "settings-scale"
        )

        scale.set_hexpand(
            True
        )

        scale.set_digits(
            digits
        )

        scale.set_value_pos(
            Gtk.PositionType.RIGHT
        )

        row.pack_start(
            row_label,
            False,
            False,
            0,
        )

        row.pack_start(
            scale,
            True,
            True,
            0,
        )

        parent.pack_start(
            row,
            False,
            False,
            0,
        )

        return scale

    @staticmethod
    def add_switch_row(
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

        switch = Gtk.Switch()

        switch.get_style_context().add_class(
            "settings-switch"
        )

        row.pack_start(
            row_label,
            True,
            True,
            0,
        )

        row.pack_end(
            switch,
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

        return switch

    def set_controls_sensitive(
        self,
        sensitive,
    ):
        self.sensitivity.set_sensitive(
            sensitive
        )

        self.scroll_factor.set_sensitive(
            sensitive
        )

        self.natural_scroll.set_sensitive(
            sensitive
        )

        self.left_handed.set_sensitive(
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
            "Loading mouse settings…"
        )

        run_async(
            mouse.get_state,
            self.apply_state,
            self.show_error,
        )

    def apply_state(
        self,
        state,
    ):
        self._loaded = True

        self.sensitivity.set_value(
            state["sensitivity"]
        )

        self.scroll_factor.set_value(
            state["scroll_factor"]
        )

        self.natural_scroll.set_active(
            state["natural_scroll"]
        )

        self.left_handed.set_active(
            state["left_handed"]
        )

        self.status.set_text("")

        self.set_controls_sensitive(
            True
        )

        return False

    def apply_clicked(
        self,
        _button,
    ):
        self.set_controls_sensitive(
            False
        )

        self.status.set_text(
            "Applying…"
        )

        run_async(
            lambda: mouse.apply_settings(
                self.sensitivity.get_value(),
                self.natural_scroll.get_active(),
                self.left_handed.get_active(),
                self.scroll_factor.get_value(),
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