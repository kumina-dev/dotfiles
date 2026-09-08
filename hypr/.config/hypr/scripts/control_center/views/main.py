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
    ):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=14,
        )

        self.build_header()

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

        self.sound = SoundCard()
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

        sound_settings = Gtk.Button(label="Sound Settings  ›")
        sound_settings.connect("clicked", lambda _button: on_sound_settings())
        self.pack_start(sound_settings, False, False, 0)

        self.pack_start(
            self.media,
            False,
            False,
            0,
        )

    def build_header(self):
        header = Gtk.Label(
            label="Control Center"
        )

        header.set_halign(
            Gtk.Align.START
        )

        header.get_style_context().add_class(
            "title"
        )

        self.pack_start(
            header,
            False,
            False,
            0,
        )

    def refresh(self):
        self.connectivity.refresh()
        self.media.refresh()
