from gi.repository import Gtk

from ..widgets.connectivity import (
    ConnectivityCard,
)

from ..widgets.sound import (
    SoundCard,
)

from ..widgets.media import (
    MediaCard,
)


class MainView(Gtk.Box):
    def __init__(
        self,
        on_wifi_details,
        on_bluetooth_details,
        on_sound_settings,
        on_settings,
    ):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )

        self.get_style_context().add_class("quick-controls")
        self.build_header(on_settings, on_sound_settings)

        self.connectivity = (
            ConnectivityCard(
                on_wifi_details=(
                    on_wifi_details
                ),
                on_bluetooth_details=(
                    on_bluetooth_details
                ),
            )
        )

        self.sound = SoundCard(compact=True)
        self.media = MediaCard()

        self.pack_start(
            self.connectivity,
            False,
            False,
            0,
        )

        self.pack_start(
            self.sound,
            False,
            False,
            0,
        )

        self.pack_start(
            self.media,
            False,
            False,
            0,
        )

    def build_header(self, on_settings, on_sound_settings):
        row = Gtk.Box(spacing=8)
        header = Gtk.Label(
            label="Control Center"
        )

        header.set_halign(
            Gtk.Align.START
        )

        header.get_style_context().add_class(
            "title"
        )

        settings = Gtk.Button(label="Settings")
        settings.connect("clicked", lambda _button: on_settings())
        sound_settings = Gtk.Button(label="Sound")
        sound_settings.set_tooltip_text("Open Sound settings and select devices")
        sound_settings.connect("clicked", lambda _button: on_sound_settings())
        row.pack_start(header, True, True, 0)
        row.pack_end(settings, False, False, 0)
        row.pack_end(sound_settings, False, False, 0)
        self.pack_start(row, False, False, 0)

    def refresh(self):
        self.connectivity.refresh()
        self.media.refresh()
