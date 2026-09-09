from gi.repository import Gtk


GROUPS = (
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


class OverviewView(Gtk.Box):
    def __init__(
        self,
        on_navigate,
    ):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
        )

        self.on_navigate = (
            on_navigate
        )

        self.get_style_context().add_class(
            "content"
        )

        title = Gtk.Label(
            label="Settings",
            xalign=0,
        )

        title.get_style_context().add_class(
            "page-title"
        )

        description = Gtk.Label(
            label=(
                "Manage your system and "
                "desktop configuration."
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

        for (
            group,
            items,
        ) in GROUPS:
            self.add_group(
                group,
                items,
            )

    def add_group(
        self,
        title,
        items,
    ):
        card = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
        )

        card.get_style_context().add_class(
            "settings-card"
        )

        heading = Gtk.Label(
            label=title,
            xalign=0,
        )

        heading.get_style_context().add_class(
            "section-title"
        )

        card.pack_start(
            heading,
            False,
            False,
            0,
        )

        grid = Gtk.Grid()

        grid.set_column_spacing(
            10
        )

        grid.set_row_spacing(
            10
        )

        grid.set_column_homogeneous(
            True
        )

        for index, (
            icon,
            label,
            page,
        ) in enumerate(items):
            button = self.create_action(
                icon,
                label,
                page,
            )

            if len(items) == 1:
                column = 0
                row = 0
                width = 2
            else:
                column = (
                    index % 2
                )

                row = (
                    index // 2
                )

                width = 1

            grid.attach(
                button,
                column,
                row,
                width,
                1,
            )

        card.pack_start(
            grid,
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

    def create_action(
        self,
        icon,
        label,
        page,
    ):
        button = Gtk.Button()

        button.get_style_context().add_class(
            "overview-action"
        )

        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        icon_label = Gtk.Label(
            label=icon
        )

        icon_label.set_size_request(
            24,
            -1,
        )

        icon_label.get_style_context().add_class(
            "overview-icon"
        )

        text = Gtk.Label(
            label=label,
            xalign=0,
        )

        text.set_hexpand(
            True
        )

        arrow = Gtk.Label(
            label="›"
        )

        arrow.get_style_context().add_class(
            "overview-arrow"
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

        row.pack_end(
            arrow,
            False,
            False,
            0,
        )

        button.add(
            row
        )

        button.connect(
            "clicked",
            lambda _button: (
                self.on_navigate(
                    page
                )
            ),
        )

        return button