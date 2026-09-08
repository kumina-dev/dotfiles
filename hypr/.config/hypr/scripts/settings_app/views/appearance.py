from gi.repository import Gtk

from settings_app import appearance
from settings_app.async_utils import (
    run_async,
)


class AppearanceView(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
        )

        self.get_style_context().add_class(
            "content"
        )

        title = Gtk.Label(
            label="Appearance",
            xalign=0,
        )

        title.get_style_context().add_class(
            "page-title"
        )

        description = Gtk.Label(
            label=(
                "Choose your wallpaper and desktop color mode."
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

        self.build_wallpaper_row(
            card
        )

        self.build_mode_row(
            card
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

    def build_wallpaper_row(
        self,
        parent,
    ):
        label = Gtk.Label(
            label="Wallpaper",
            xalign=0,
        )

        label.get_style_context().add_class(
            "section-title"
        )

        parent.pack_start(
            label,
            False,
            False,
            0,
        )

        self.wallpaper_chooser = (
            Gtk.FileChooserButton(
                title="Choose wallpaper",
                action=(
                    Gtk.FileChooserAction.OPEN
                ),
            )
        )

        image_filter = Gtk.FileFilter()

        image_filter.set_name(
            "Images"
        )

        image_filter.add_mime_type(
            "image/png"
        )

        image_filter.add_mime_type(
            "image/jpeg"
        )

        image_filter.add_mime_type(
            "image/webp"
        )

        self.wallpaper_chooser.add_filter(
            image_filter
        )

        parent.pack_start(
            self.wallpaper_chooser,
            False,
            False,
            0,
        )

        self.current_wallpaper = Gtk.Label(
            xalign=0,
        )

        self.current_wallpaper.set_line_wrap(
            True
        )

        self.current_wallpaper.set_selectable(
            True
        )

        self.current_wallpaper.get_style_context().add_class(
            "page-description"
        )

        parent.pack_start(
            self.current_wallpaper,
            False,
            False,
            0,
        )

    def build_mode_row(
        self,
        parent,
    ):
        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        label = Gtk.Label(
            label="Color mode",
            xalign=0,
        )

        label.set_hexpand(
            True
        )

        self.mode_combo = Gtk.ComboBoxText()

        self.mode_combo.append(
            "dark",
            "Dark",
        )

        self.mode_combo.append(
            "light",
            "Light",
        )

        row.pack_start(
            label,
            True,
            True,
            0,
        )

        row.pack_end(
            self.mode_combo,
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

    def set_controls_sensitive(
        self,
        sensitive,
    ):
        self.wallpaper_chooser.set_sensitive(
            sensitive
        )

        self.mode_combo.set_sensitive(
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
            "Loading appearance settings…"
        )

        run_async(
            appearance.get_state,
            self.apply_state,
            self.show_error,
        )

    def apply_state(
        self,
        state,
    ):
        self.mode_combo.set_active_id(
            state["mode"]
        )

        wallpaper = state[
            "wallpaper"
        ]

        if wallpaper:
            self.current_wallpaper.set_text(
                f"Current: {wallpaper}"
            )

            try:
                self.wallpaper_chooser.set_filename(
                    wallpaper
                )
            except Exception:
                pass
        else:
            self.current_wallpaper.set_text(
                "No wallpaper configured."
            )

        self.set_controls_sensitive(
            True
        )

        self.status.set_text("")

        return False

    def apply_clicked(
        self,
        _button,
    ):
        mode = (
            self.mode_combo
            .get_active_id()
        )

        wallpaper = (
            self.wallpaper_chooser
            .get_filename()
        )

        if not mode:
            self.status.set_text(
                "Choose a color mode."
            )
            return

        self.set_controls_sensitive(
            False
        )

        self.status.set_text(
            "Applying appearance…"
        )

        run_async(
            lambda: appearance.apply_settings(
                wallpaper,
                mode,
            ),
            self.apply_finished,
            self.show_error,
        )

    def apply_finished(
        self,
        state,
    ):
        self.mode_combo.set_active_id(
            state["mode"]
        )

        self.current_wallpaper.set_text(
            (
                "Current: "
                f'{state["wallpaper"]}'
            )
        )

        self.set_controls_sensitive(
            True
        )

        self.status.set_text(
            "Applied."
        )

        return False

    def show_error(
        self,
        error,
    ):
        self.set_controls_sensitive(
            True
        )

        self.status.set_text(
            str(error)
        )

        return False