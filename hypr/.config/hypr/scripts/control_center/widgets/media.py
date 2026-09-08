from gi.repository import Gtk

from .. import media
from ..async_utils import run_async


class MediaCard(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )

        self._refreshing = False

        self.get_style_context().add_class(
            "card"
        )

        self.build()

    def build(self):
        title = Gtk.Label(
            label="Media"
        )

        title.set_halign(
            Gtk.Align.START
        )

        title.get_style_context().add_class(
            "section-title"
        )

        self.pack_start(
            title,
            False,
            False,
            0,
        )

        self.media_label = Gtk.Label(
            label="Nothing playing"
        )

        self.media_label.set_halign(
            Gtk.Align.START
        )

        self.media_label.set_ellipsize(
            3
        )

        self.media_label.get_style_context().add_class(
            "secondary"
        )

        self.pack_start(
            self.media_label,
            False,
            False,
            0,
        )

        controls = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
        )

        previous = Gtk.Button(
            label="󰒮"
        )

        self.play_pause_button = (
            Gtk.Button(
                label="󰐊"
            )
        )

        next_button = Gtk.Button(
            label="󰒭"
        )

        previous.set_can_focus(False)
        self.play_pause_button.set_can_focus(False)
        next_button.set_can_focus(False)

        previous.connect(
            "clicked",
            lambda _: self.command(
                "previous"
            ),
        )

        self.play_pause_button.connect(
            "clicked",
            lambda _: self.command(
                "play-pause"
            ),
        )

        next_button.connect(
            "clicked",
            lambda _: self.command(
                "next"
            ),
        )

        controls.pack_start(
            previous,
            True,
            True,
            0,
        )

        controls.pack_start(
            self.play_pause_button,
            True,
            True,
            0,
        )

        controls.pack_start(
            next_button,
            True,
            True,
            0,
        )

        self.pack_start(
            controls,
            False,
            False,
            0,
        )

    def refresh(self):
        if self._refreshing:
            return

        self._refreshing = True

        run_async(
            self.load_state,
            self.apply_state,
            self.refresh_failed,
        )

    def load_state(self):
        return media.get_state()

    def apply_state(
        self,
        state,
    ):
        self._refreshing = False

        metadata = state["metadata"]
        status = state["status"]

        self.media_label.set_text(
            metadata
            or "Nothing playing"
        )

        self.play_pause_button.set_label(
            "󰏤"
            if status == "Playing"
            else "󰐊"
        )

        return False

    def refresh_failed(
        self,
        _error,
    ):
        self._refreshing = False
        return False

    def command(
        self,
        action,
    ):
        run_async(
            lambda: media.command(
                action
            ),
            self.command_finished,
        )

    def command_finished(
        self,
        _result,
    ):
        self.refresh()
        return False