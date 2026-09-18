from gi.repository import Gdk, Gtk, Pango

from kumina_common.i18n import translate as tr
from settings_app import account
from settings_app.async_utils import run_async


class AccountView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.get_style_context().add_class("content")
        self._refreshing = False
        self._destroyed = False
        self._info = None
        self.connect("destroy", self.on_destroy)
        self.pack_start(self.label(tr("Account"), "page-title"), False, False, 0)
        self.pack_start(self.label(tr("Information for the Linux user running Settings."), "page-description"), False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        card.set_valign(Gtk.Align.START)
        card.get_style_context().add_class("settings-card")
        header = Gtk.Box(spacing=12)
        header.pack_start(self.label("󰀄", "overview-icon"), False, False, 0)
        self.identity = self.label(tr("Linux account"), "section-title")
        self.identity.set_selectable(True)
        header.pack_start(self.identity, True, True, 0)
        card.pack_start(header, False, False, 0)
        self.details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        card.pack_start(self.details, False, False, 0)
        card.pack_start(self.label(tr("Session groups are the groups active in this running session."), "page-description"), False, False, 0)
        scroller.add(card)
        self.pack_start(scroller, True, True, 0)

        footer = Gtk.Box(spacing=8)
        self.status = Gtk.Label(xalign=0)
        self.status.set_ellipsize(Pango.EllipsizeMode.END)
        self.status.set_max_width_chars(22)
        self.status.get_style_context().add_class("page-description")
        self.set_status(tr("Open this page to load account information."))
        footer.pack_start(self.status, True, True, 0)
        self.refresh_button = Gtk.Button(label=tr("Refresh"))
        self.refresh_button.connect("clicked", lambda _button: self.refresh())
        footer.pack_start(self.refresh_button, False, False, 0)
        self.copy_button = Gtk.Button(label=tr("Copy account information"))
        self.copy_button.set_sensitive(False)
        self.copy_button.connect("clicked", self.copy_information)
        footer.pack_start(self.copy_button, False, False, 0)
        self.pack_start(footer, False, False, 0)

    @staticmethod
    def label(text, style):
        label = Gtk.Label(label=text, xalign=0)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(45)
        label.get_style_context().add_class(style)
        return label

    def set_status(self, message):
        self.status.set_text(message)
        self.status.set_tooltip_text(message or None)

    def refresh(self):
        if self._refreshing or self._destroyed:
            return
        self._refreshing = True
        self.refresh_button.set_sensitive(False)
        self.copy_button.set_sensitive(False)
        self.set_status(tr("Loading…"))
        run_async(account.collect, self.apply_info, self.show_error)

    def apply_info(self, info):
        if self._destroyed:
            return False
        self._refreshing = False
        self._info = info
        self.identity.set_text(info.display_name)
        for child in self.details.get_children():
            child.destroy()
        for title, value in info.rows():
            row = Gtk.Box(spacing=16)
            name = self.label(title, "settings-row-title")
            name.set_size_request(130, -1)
            name.set_max_width_chars(18)
            name.set_valign(Gtk.Align.START)
            detail = self.label(value, "page-description")
            detail.set_max_width_chars(32)
            detail.set_selectable(True)
            detail.set_hexpand(True)
            row.pack_start(name, False, False, 0)
            row.pack_start(detail, True, True, 0)
            self.details.pack_start(row, False, False, 0)
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
        self.copy_button.set_sensitive(self._info is not None)
        prefix = tr("Refresh failed; previous information shown. ") if self._info else ""
        self.set_status(prefix + str(error))
        return False

    def copy_information(self, _button):
        if self._info is None:
            return
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(account.format_report(self._info), -1)
        clipboard.store()
        self.set_status(tr("Copied"))

    def on_destroy(self, _widget):
        self._destroyed = True
