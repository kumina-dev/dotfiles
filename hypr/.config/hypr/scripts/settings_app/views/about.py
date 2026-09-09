from gi.repository import Gtk


class AboutView(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
        )

        self.get_style_context().add_class(
            "content"
        )

        title = Gtk.Label(
            label="About",
            xalign=0,
        )

        title.get_style_context().add_class(
            "page-title"
        )

        description = Gtk.Label(
            label=(
                "Information about this "
                "desktop environment."
            ),
            xalign=0,
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
            spacing=14,
        )

        card.get_style_context().add_class(
            "settings-card"
        )

        header = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )

        icon = Gtk.Label(
            label="󰍹"
        )

        icon.get_style_context().add_class(
            "overview-icon"
        )

        identity = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=2,
        )

        name = Gtk.Label(
            label="Kumina Desktop",
            xalign=0,
        )

        name.get_style_context().add_class(
            "section-title"
        )

        subtitle = Gtk.Label(
            label=(
                "Personal Arch Linux + "
                "Hyprland desktop"
            ),
            xalign=0,
        )

        subtitle.get_style_context().add_class(
            "page-description"
        )

        identity.pack_start(
            name,
            False,
            False,
            0,
        )

        identity.pack_start(
            subtitle,
            False,
            False,
            0,
        )

        header.pack_start(
            icon,
            False,
            False,
            0,
        )

        header.pack_start(
            identity,
            True,
            True,
            0,
        )

        card.pack_start(
            header,
            False,
            False,
            0,
        )

        self.add_row(
            card,
            "Desktop",
            "Hyprland",
        )

        self.add_row(
            card,
            "Interface",
            "GTK 3 + PyGObject",
        )

        self.add_row(
            card,
            "Theming",
            "Matugen",
        )

        self.add_row(
            card,
            "Configuration",
            "GNU Stow dotfiles",
        )

        self.pack_start(
            card,
            False,
            False,
            0,
        )

    @staticmethod
    def add_row(
        card,
        label,
        value,
    ):
        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=16,
        )

        name = Gtk.Label(
            label=label,
            xalign=0,
        )

        name.set_hexpand(
            True
        )

        detail = Gtk.Label(
            label=value,
            xalign=1,
        )

        detail.get_style_context().add_class(
            "page-description"
        )

        row.pack_start(
            name,
            True,
            True,
            0,
        )

        row.pack_end(
            detail,
            False,
            False,
            0,
        )

        card.pack_start(
            row,
            False,
            False,
            0,
        )