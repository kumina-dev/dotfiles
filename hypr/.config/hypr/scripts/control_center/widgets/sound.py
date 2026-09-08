from gi.repository import GLib, Gtk, Pango

from .. import audio
from ..async_utils import run_async


class AudioEndpoint(Gtk.Box):
    """One device selector, with ordered writes and a coalesced volume slider."""

    def __init__(self, kind, on_refresh):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.kind = kind
        self.on_refresh = on_refresh
        self.revision = 0
        self._devices = {}
        self._choices = None
        self._device = None
        self._volume = None
        self._muted = False
        self._applying = False
        self._dragging = False
        self._busy = None
        self._pending_volume = None
        self._volume_timeout = None
        self._write_future = None
        self._destroyed = False
        self._action_error = None

        title = "Output" if kind == "output" else "Microphone"
        header = Gtk.Box(spacing=8)
        label = Gtk.Label(label=title, xalign=0)
        label.get_style_context().add_class("section-title")
        self.volume_label = Gtk.Label(label="—", xalign=1)
        header.pack_start(label, True, True, 0)
        header.pack_end(self.volume_label, False, False, 0)
        self.pack_start(header, False, False, 0)

        self.device_combo = Gtk.ComboBoxText()
        self.device_combo.set_hexpand(True)
        self.device_combo.set_tooltip_text(f"Default {title.lower()} device")
        for cell in self.device_combo.get_cells():
            cell.set_property("ellipsize", Pango.EllipsizeMode.END)
            cell.set_property("max-width-chars", 28)
        self.device_combo.append("none", "Loading devices…")
        self.device_combo.set_active(0)
        self.device_combo.connect("changed", self.device_changed)
        self.pack_start(self.device_combo, False, False, 0)

        row = Gtk.Box(spacing=8)
        self.volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1,
        )
        self.volume_scale.set_draw_value(False)
        self.volume_scale.set_hexpand(True)
        self.volume_scale.set_tooltip_text(f"{title} volume")
        self.volume_scale.connect("value-changed", self.volume_changed)
        self.volume_scale.connect("button-press-event", self.volume_press)
        self.volume_scale.connect("button-release-event", self.volume_release)
        self.mute_button = Gtk.Button(label="Mute")
        self.mute_button.connect("clicked", self.toggle_mute)
        row.pack_start(self.volume_scale, True, True, 0)
        row.pack_end(self.mute_button, False, False, 0)
        self.pack_start(row, False, False, 0)

        self.error_label = Gtk.Label(xalign=0)
        self.error_label.set_line_wrap(True)
        self.error_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.error_label.set_max_width_chars(36)
        self.error_label.set_no_show_all(True)
        self.pack_start(self.error_label, False, False, 0)
        self.connect("destroy", self.on_destroy)
        self.connect("unmap", self.on_unmap)
        self.update_sensitive()

    def pending(self):
        return (self._busy is not None or self._pending_volume is not None
                or self._volume_timeout is not None or self._dragging)

    def update_sensitive(self):
        available = self._device is not None and self._volume is not None
        self.device_combo.set_sensitive(bool(self._devices) and not self.pending())
        self.volume_scale.set_sensitive(available and self._busy in (None, "volume"))
        self.mute_button.set_sensitive(available and not self.pending())

    def show_error(self, message):
        self.error_label.set_text(message or "")
        self.error_label.set_visible(bool(message))

    def apply_state(self, state, revision):
        if (self._destroyed or revision != self.revision or self.pending()
                or self.device_combo.get_property("popup-shown")):
            return
        self._applying = True
        try:
            self.set_sensitive(True)
            self._devices = {str(device.id): device for device in state["devices"]}
            self._device = state["device"]
            self._volume = state["volume"]
            self._muted = state["muted"]
            choices = (tuple(state["devices"]), self._device is None)
            if choices != self._choices:
                self.device_combo.remove_all()
                if self._device is None:
                    title = "output" if self.kind == "output" else "input"
                    message = (f"Choose an {title} device" if self._devices
                               else f"No {title} device")
                    self.device_combo.append("none", message)
                for device in state["devices"]:
                    self.device_combo.append(str(device.id), device.description)
                self._choices = choices
            self.device_combo.set_active_id(
                str(self._device.id) if self._device else "none",
            )
            self.device_combo.set_tooltip_text(
                self._device.description if self._device else "Choose a device",
            )
            self.volume_scale.set_value(min(self._volume or 0, 100))
            self.volume_label.set_text(
                f"{self._volume}%" if self._volume is not None else "—",
            )
            self.mute_button.set_label("Unmute" if self._muted else "Mute")
            self.mute_button.set_tooltip_text(
                ("Unmute " if self._muted else "Mute ")
                + ("output" if self.kind == "output" else "microphone"),
            )
            context = self.mute_button.get_style_context()
            if self._muted:
                context.add_class("active")
            else:
                context.remove_class("active")
            self.show_error(self._action_error or state["error"])
            self.update_sensitive()
        finally:
            self._applying = False

    def device_changed(self, combo):
        if self._applying or self.pending():
            return
        device = self._devices.get(combo.get_active_id())
        if device is not None and device != self._device:
            self.revision += 1
            self.start_write("default", lambda: audio.set_default(device))

    def volume_changed(self, scale):
        if self._applying or self._device is None or self._volume is None:
            return
        value = round(scale.get_value())
        self.revision += 1
        self.volume_label.set_text(f"{value}%")
        self._pending_volume = (self._device, value)
        if self._volume_timeout is not None:
            GLib.source_remove(self._volume_timeout)
        self._volume_timeout = GLib.timeout_add(100, self.flush_volume)
        self.update_sensitive()

    def volume_press(self, _scale, _event):
        self._dragging = True
        self.update_sensitive()
        return False

    def volume_release(self, _scale, _event):
        self._dragging = False
        self.update_sensitive()
        self.on_refresh()
        return False

    def flush_volume(self):
        self._volume_timeout = None
        if not self._destroyed and self._busy is None and self._pending_volume:
            device, volume = self._pending_volume
            self._pending_volume = None
            self.start_write("volume", lambda: audio.set_volume(device, volume))
        return False

    def toggle_mute(self, _button):
        if self.pending() or self._device is None or self._volume is None:
            return
        self.revision += 1
        device, muted = self._device, not self._muted
        self.start_write("mute", lambda: audio.set_mute(device, muted))

    def start_write(self, kind, action):
        self._busy = kind
        self.update_sensitive()
        self._write_future = run_async(action, self.write_finished, self.write_failed)

    def write_finished(self, _result=None):
        if self._busy != "volume":
            self._volume = None
        self._busy = None
        self.revision += 1
        if self._destroyed:
            return False
        self._action_error = None
        if self._pending_volume and self._volume_timeout is None:
            self.flush_volume()
        self.update_sensitive()
        self.on_refresh()
        return False

    def write_failed(self, error):
        self._busy = None
        self.revision += 1
        if self._destroyed:
            return False
        self._pending_volume = None
        if self._volume_timeout is not None:
            GLib.source_remove(self._volume_timeout)
            self._volume_timeout = None
        self._volume = None
        self._action_error = str(error)
        self.show_error(self._action_error)
        self.update_sensitive()
        self.on_refresh()
        return False

    def on_unmap(self, _widget):
        self._dragging = False
        if self._volume_timeout is not None:
            GLib.source_remove(self._volume_timeout)
            self._volume_timeout = None
        self.flush_volume()

    def on_destroy(self, _widget):
        self._destroyed = True
        if self._volume_timeout is not None:
            GLib.source_remove(self._volume_timeout)
            self._volume_timeout = None
        # Finish the last requested volume even if GTK's main loop has stopped.
        if self._pending_volume:
            device, volume = self._pending_volume
            previous = self._write_future
            self._pending_volume = None

            def finish_volume():
                if previous is not None:
                    try:
                        previous.result()
                    except Exception:
                        return
                audio.set_volume(device, volume)

            run_async(finish_volume)


class SoundCard(Gtk.Box):
    def __init__(self, card_class="card"):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.get_style_context().add_class(card_class)
        self._refreshing = False
        self._refresh_again = False
        self._timer = None
        self._destroyed = False
        self.endpoints = {}

        for kind in ("output", "input"):
            endpoint = AudioEndpoint(kind, self.refresh)
            self.endpoints[kind] = endpoint
            self.pack_start(endpoint, False, False, 0)

        self.error_label = Gtk.Label(xalign=0)
        self.error_label.set_line_wrap(True)
        self.error_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.error_label.set_max_width_chars(36)
        self.error_label.set_no_show_all(True)
        self.pack_start(self.error_label, False, False, 0)
        self.connect("map", self.on_map)
        self.connect("unmap", self.on_unmap)
        self.connect("destroy", self.on_destroy)

    def on_map(self, _widget):
        if self._timer is None:
            self._timer = GLib.timeout_add_seconds(2, self.poll)
        self.refresh()

    def on_unmap(self, _widget):
        if self._timer is not None:
            GLib.source_remove(self._timer)
            self._timer = None

    def on_destroy(self, widget):
        self._destroyed = True
        self.on_unmap(widget)

    def poll(self):
        self.refresh()
        return True

    def refresh(self):
        if self._destroyed or not self.get_mapped():
            return False
        if self._refreshing:
            self._refresh_again = True
            return False
        self._refreshing = True
        revisions = {kind: endpoint.revision for kind, endpoint in self.endpoints.items()}
        run_async(
            audio.get_state,
            lambda state: self.apply_state(state, revisions),
            self.refresh_failed,
        )
        return False

    def finish_refresh(self):
        self._refreshing = False
        if self._refresh_again:
            self._refresh_again = False
            self.refresh()
        return False

    def apply_state(self, state, revisions):
        if not self._destroyed:
            self.error_label.hide()
            for kind, endpoint in self.endpoints.items():
                endpoint.apply_state(state[kind], revisions[kind])
        return self.finish_refresh()

    def refresh_failed(self, error):
        if not self._destroyed:
            self.error_label.set_text(str(error))
            self.error_label.show()
            for endpoint in self.endpoints.values():
                endpoint.set_sensitive(False)
                endpoint.volume_label.set_text("—")
        return self.finish_refresh()
