from gi.repository import GLib, Gtk

from .. import audio
from ..async_utils import run_async


class SoundCard(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )

        self._refreshing = False
        self._volume_timeout = None
        self._changing_volume = False

        self.get_style_context().add_class(
            "card"
        )

        self.build()

    def build(self):
        header = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        title = Gtk.Label(
            label="Sound"
        )

        title.set_halign(
            Gtk.Align.START
        )

        title.get_style_context().add_class(
            "section-title"
        )

        self.volume_label = Gtk.Label(
            label="..."
        )

        self.volume_label.set_halign(
            Gtk.Align.END
        )

        self.mute_button = Gtk.Button(
            label=""
        )

        self.mute_button.set_can_focus(
            False
        )

        self.mute_button.connect(
            "clicked",
            self.toggle_mute,
        )

        header.pack_start(
            title,
            True,
            True,
            0,
        )

        header.pack_end(
            self.mute_button,
            False,
            False,
            0,
        )

        header.pack_end(
            self.volume_label,
            False,
            False,
            0,
        )

        self.pack_start(
            header,
            False,
            False,
            0,
        )

        self.volume_scale = (
            Gtk.Scale.new_with_range(
                Gtk.Orientation.HORIZONTAL,
                0,
                100,
                1,
            )
        )

        self.volume_scale.set_draw_value(
            False
        )

        self.volume_scale.set_value(0)

        self.volume_scale.connect(
            "value-changed",
            self.volume_changed,
        )

        self.volume_scale.connect(
            "button-press-event",
            self.volume_press,
        )

        self.volume_scale.connect(
            "button-release-event",
            self.volume_release,
        )

        self.pack_start(
            self.volume_scale,
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
        return audio.get_state()

    def apply_state(
        self,
        state,
    ):
        self._refreshing = False

        volume = state["volume"]
        muted = state["muted"]

        if not self._changing_volume:
            self.volume_scale.set_value(
                volume
            )

        self.volume_label.set_text(
            f"{volume}%"
        )

        self.mute_button.set_label(
            "󰝟" if muted else ""
        )

        return False

    def refresh_failed(
        self,
        _error,
    ):
        self._refreshing = False
        return False

    def volume_changed(
        self,
        scale,
    ):
        value = int(
            scale.get_value()
        )

        self.volume_label.set_text(
            f"{value}%"
        )

        if self._volume_timeout is not None:
            GLib.source_remove(
                self._volume_timeout
            )

        self._volume_timeout = (
            GLib.timeout_add(
                80,
                self.apply_volume,
                value,
            )
        )

    def volume_press(
        self,
        _scale,
        _event,
    ):
        self._changing_volume = True
        return False


    def volume_release(
        self,
        _scale,
        _event,
    ):
        self._changing_volume = False
        return False

    def apply_volume(
        self,
        value,
    ):
        self._volume_timeout = None

        run_async(
            lambda: audio.set_volume(
                value
            )
        )

        return False

    def toggle_mute(
        self,
        _button,
    ):
        run_async(
            audio.toggle_mute,
            self.mute_finished,
        )

    def mute_finished(
        self,
        _result,
    ):
        self.refresh()
        return False