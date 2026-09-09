from gi.repository import Gdk, Gtk, Pango

from settings_app import system_info
from settings_app.async_utils import run_async


class AboutView(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
        )
        self.get_style_context().add_class("content")
        self._refreshing = False
        self._destroyed = False
        self._rows = []
        self.connect("destroy", self.on_destroy)

        title = Gtk.Label(label="About this PC", xalign=0)
        title.get_style_context().add_class("page-title")
        self.pack_start(title, False, False, 0)

        description = Gtk.Label(
            label="Hardware, system, and desktop information.",
            xalign=0,
        )
        description.get_style_context().add_class("page-description")
        self.pack_start(description, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_hexpand(True)
        scroller.set_vexpand(True)

        self.card = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=14,
        )
        self.card.set_valign(Gtk.Align.START)
        self.card.get_style_context().add_class("settings-card")

        header = Gtk.Box(spacing=12)
        icon = Gtk.Label(label="󰍹")
        icon.get_style_context().add_class("overview-icon")
        header.pack_start(icon, False, False, 0)

        identity = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name = Gtk.Label(label="KumiOS", xalign=0)
        name.get_style_context().add_class("section-title")
        subtitle = Gtk.Label(label="Personal Arch Linux + Hyprland desktop", xalign=0)
        subtitle.set_line_wrap(True)
        subtitle.set_max_width_chars(36)
        subtitle.get_style_context().add_class("page-description")
        identity.pack_start(name, False, False, 0)
        identity.pack_start(subtitle, False, False, 0)
        header.pack_start(identity, True, True, 0)
        self.card.pack_start(header, False, False, 0)

        self.details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.card.pack_start(self.details, False, False, 0)
        scroller.add(self.card)
        self.pack_start(scroller, True, True, 0)

        footer = Gtk.Box(spacing=8)
        self.status = Gtk.Label(label="Open this page to load system information.", xalign=0)
        self.status.set_ellipsize(Pango.EllipsizeMode.END)
        self.status.set_max_width_chars(22)
        self.status.get_style_context().add_class("page-description")
        footer.pack_start(self.status, True, True, 0)

        self.refresh_button = Gtk.Button(label="Refresh")
        self.refresh_button.connect("clicked", lambda _button: self.refresh())
        footer.pack_start(self.refresh_button, False, False, 0)
        self.copy_button = Gtk.Button(label="Copy system information")
        self.copy_button.set_sensitive(False)
        self.copy_button.connect("clicked", self.copy_information)
        footer.pack_start(self.copy_button, False, False, 0)
        self.pack_start(footer, False, False, 0)

    def refresh(self):
        if self._refreshing or self._destroyed:
            return
        self._refreshing = True
        self.refresh_button.set_sensitive(False)
        self.copy_button.set_sensitive(False)
        self.set_status("Loading…")
        run_async(system_info.collect, self.apply_info, self.show_error)

    def apply_info(self, rows):
        if self._destroyed:
            return False
        self._refreshing = False
        self._rows = rows
        for child in self.details.get_children():
            child.destroy()
        for label, value in rows:
            self.add_row(self.details, label, value)
        self.details.show_all()
        self.refresh_button.set_sensitive(True)
        self.copy_button.set_sensitive(True)
        self.set_status("")
        return False

    def show_error(self, error):
        if self._destroyed:
            return False
        self._refreshing = False
        self.refresh_button.set_sensitive(True)
        self.copy_button.set_sensitive(bool(self._rows))
        prefix = "Refresh failed; previous information shown. " if self._rows else "Could not read system information. "
        self.set_status(prefix + str(error))
        return False

    def set_status(self, message):
        self.status.set_text(message)
        self.status.set_tooltip_text(message or None)

    def copy_information(self, _button):
        if not self._rows:
            return
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(system_info.format_report(self._rows), -1)
        clipboard.store()
        self.set_status("Copied")

    def on_destroy(self, _widget):
        self._destroyed = True

    @staticmethod
    def add_row(card, label, value):
        row = Gtk.Box(spacing=16)
        name = Gtk.Label(label=label, xalign=0, yalign=0)
        name.set_size_request(130, -1)
        detail = Gtk.Label(label=value, xalign=0, yalign=0)
        detail.set_hexpand(True)
        detail.set_selectable(True)
        detail.set_line_wrap(True)
        detail.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        detail.set_max_width_chars(34)
        detail.get_style_context().add_class("page-description")
        row.pack_start(name, False, False, 0)
        row.pack_start(detail, True, True, 0)
        card.pack_start(row, False, False, 0)
