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
        self._commanding = False
        self._has_player = False
        self._action_error = None

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

        self.previous_button = Gtk.Button(
            label="󰒮"
        )

        self.play_pause_button = (
            Gtk.Button(
                label="󰐊"
            )
        )

        self.next_button = Gtk.Button(
            label="󰒭"
        )

        self.previous_button.set_can_focus(False)
        self.play_pause_button.set_can_focus(False)
        self.next_button.set_can_focus(False)

        self.previous_button.connect(
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

        self.next_button.connect(
            "clicked",
            lambda _: self.command(
                "next"
            ),
        )

        controls.pack_start(
            self.previous_button,
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
            self.next_button,
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

        self.error_label = Gtk.Label(
            xalign=0,
        )

        self.error_label.set_line_wrap(
            True
        )

        self.error_label.get_style_context().add_class(
            "secondary"
        )

        self.pack_start(
            self.error_label,
            False,
            False,
            0,
        )

        self.set_controls_sensitive(
            False
        )

    def set_controls_sensitive(
        self,
        sensitive,
    ):
        sensitive = (
            bool(sensitive)
            and not self._commanding
        )

        self.previous_button.set_sensitive(
            sensitive
        )

        self.play_pause_button.set_sensitive(
            sensitive
        )

        self.next_button.set_sensitive(
            sensitive
        )

    def show_error(
        self,
        message,
    ):
        self.error_label.set_text(
            message or ""
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

        self._has_player = bool(
            state["player"]
        )

        self.media_label.set_text(
            metadata
            or "Nothing playing"
        )

        self.play_pause_button.set_label(
            "󰏤"
            if status == "Playing"
            else "󰐊"
        )

        self.set_controls_sensitive(
            self._has_player
        )

        self.show_error(
            self._action_error
        )

        return False

    def refresh_failed(
        self,
        error,
    ):
        self._refreshing = False
        self._has_player = False

        self.media_label.set_text(
            "Media unavailable"
        )

        self.set_controls_sensitive(
            False
        )

        if not self._action_error:
            self.show_error(
                str(error)
            )

        return False

    def command(
        self,
        action,
    ):
        if (
            self._commanding
            or not self._has_player
        ):
            return

        self._commanding = True
        self._action_error = None

        self.show_error("")

        self.set_controls_sensitive(
            False
        )

        run_async(
            lambda: media.command(
                action
            ),
            self.command_finished,
            self.command_failed,
        )

    def command_finished(
        self,
        _result,
    ):
        self._commanding = False
        self._action_error = None

        self.show_error("")

        self.refresh()

        return False

    def command_failed(
        self,
        error,
    ):
        self._commanding = False

        self._action_error = str(
            error
        )

        self.set_controls_sensitive(
            self._has_player
        )

        self.show_error(
            self._action_error
        )

        return False