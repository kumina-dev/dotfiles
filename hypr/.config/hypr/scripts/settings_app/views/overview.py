from gi.repository import Gtk


class OverviewView(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
        )

        self.get_style_context().add_class(
            "content"
        )

        title = Gtk.Label(
            label="Settings"
        )

        title.set_halign(
            Gtk.Align.START
        )

        title.get_style_context().add_class(
            "page-title"
        )

        description = Gtk.Label(
            label=(
                "Manage system and desktop settings."
            )
        )

        description.set_halign(
            Gtk.Align.START
        )

        description.get_style_context().add_class(
            "page-description"
        )

        card = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )

        card.get_style_context().add_class(
            "settings-card"
        )

        card_title = Gtk.Label(
            label="Welcome"
        )

        card_title.set_halign(
            Gtk.Align.START
        )

        card_text = Gtk.Label(
            label=(
                "Choose a category from the sidebar."
            )
        )

        card_text.set_halign(
            Gtk.Align.START
        )

        card_text.get_style_context().add_class(
            "page-description"
        )

        card.pack_start(
            card_title,
            False,
            False,
            0,
        )

        card.pack_start(
            card_text,
            False,
            False,
            0,
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

        self.pack_start(
            card,
            False,
            False,
            0,
        )