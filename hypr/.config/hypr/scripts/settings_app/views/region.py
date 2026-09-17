from gi.repository import GLib, Gtk

from kumina_common import region as preferences
from settings_app import region
from settings_app.async_utils import run_async


class RegionView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.get_style_context().add_class("content")
        self._busy = False
        self._zones_loaded = False
        self._preferences_loaded = False
        title = self.label("Language & Region", "page-title")
        self.pack_start(title, False, False, 0)
        self.pack_start(self.label("Date, time and calendar preferences.", "page-description"), False, False, 0)

        sections = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.add(sections)
        self.pack_start(scroller, True, True, 0)

        card = self.card(sections)
        self.pack_label(card, "Formats", "section-title")
        self.clock = self.combo(card, "Clock", (("24", "24-hour"), ("12", "12-hour")))
        self.date = self.combo(card, "Date", (("day-first", "Day.Month.Year"), ("iso", "Year-Month-Day"), ("month-first", "Month/Day/Year")))
        self.week = self.combo(card, "Week starts on", (("monday", "Monday"), ("sunday", "Sunday")))
        self.preview = self.label("", "page-description")
        card.pack_start(self.preview, False, False, 0)
        for combo in (self.clock, self.date, self.week):
            combo.connect("changed", lambda *_: self.update_preview())
        save = Gtk.Button(label="Apply formats")
        save.get_style_context().add_class("primary-action")
        save.connect("clicked", self.save_formats)
        card.pack_start(save, False, False, 0)
        self.pack_label(card, "Applies to the KumiOS panel clock and calendar. Other apps keep their own formats.", "page-description")
        self.format_status = self.label("", "settings-status")
        card.pack_start(self.format_status, False, False, 0)

        card = self.card(sections)
        self.pack_label(card, "System time zone", "section-title")
        self.timezone = self.combo(card, "Time zone", ())
        self.zone_button = Gtk.Button(label="Apply time zone")
        self.zone_button.connect("clicked", self.apply_timezone)
        card.pack_start(self.zone_button, False, False, 0)
        self.pack_label(card, "Changes the time zone for all users. Authentication may be requested.", "page-description")
        self.zone_status = self.label("", "settings-status")
        card.pack_start(self.zone_status, False, False, 0)
        retry = Gtk.Button(label="Refresh")
        retry.connect("clicked", lambda *_: self.refresh())
        card.pack_start(retry, False, False, 0)
        self.pack_label(sections, "Interface translations and number/currency formats are not available yet. Keyboard layouts are under Input.", "page-description")
        self.load_preferences()
        self.set_zone_busy(False)

    @staticmethod
    def label(text, style):
        label = Gtk.Label(label=text, xalign=0)
        label.set_line_wrap(True)
        label.set_max_width_chars(55)
        label.get_style_context().add_class(style)
        return label

    def pack_label(self, parent, text, style):
        parent.pack_start(self.label(text, style), False, False, 0)

    @staticmethod
    def card(parent):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("settings-card")
        parent.pack_start(card, False, False, 0)
        return card

    def combo(self, parent, title, options):
        row = Gtk.Box(spacing=12)
        row.pack_start(self.label(title, "settings-row-title"), True, True, 0)
        combo = Gtk.ComboBoxText()
        combo.get_style_context().add_class("settings-control")
        for key, text in options:
            combo.append(key, text)
        row.pack_end(combo, False, False, 0)
        parent.pack_start(row, False, False, 0)
        return combo

    def values(self):
        return {"clock": self.clock.get_active_id(), "date": self.date.get_active_id(), "week_start": self.week.get_active_id()}

    def load_preferences(self):
        if self._preferences_loaded:
            return
        try:
            values = preferences.read_preferences(strict=True)
        except RuntimeError as error:
            self.format_status.set_text(str(error) + " Apply formats to replace the invalid file.")
            values = preferences.DEFAULTS
        self.clock.set_active_id(values["clock"])
        self.date.set_active_id(values["date"])
        self.week.set_active_id(values["week_start"])
        self._preferences_loaded = True

    def update_preview(self):
        values = self.values()
        if all(values.values()):
            now = preferences.local_now()
            self.preview.set_text(f"Preview: {preferences.format_date(now, values)} · {preferences.format_time(now, values)}")

    def save_formats(self, _button):
        try:
            preferences.save_preferences(self.values())
        except (OSError, ValueError) as error:
            self.format_status.set_text(str(error))
            return
        self.format_status.set_text("Applied. The panel and calendar update automatically; no logout needed.")

    def set_zone_busy(self, busy):
        self._busy = busy
        self.timezone.set_sensitive(not busy and self._zones_loaded)
        self.zone_button.set_sensitive(not busy and self._zones_loaded)

    def refresh(self):
        self.update_preview()
        if self._busy:
            return
        self.set_zone_busy(True)
        self.zone_status.set_text("Loading time zones…")
        run_async(region.get_state, self.loaded, self.failed)

    def loaded(self, state):
        self.timezone.remove_all()
        for zone in state["timezones"]:
            self.timezone.append(zone, zone)
        self.timezone.set_active_id(state["timezone"])
        self._zones_loaded = True
        self.set_zone_busy(False)
        self.zone_status.set_text(f"Current: {state['timezone']}")
        return GLib.SOURCE_REMOVE

    def apply_timezone(self, _button):
        zone = self.timezone.get_active_id()
        self.set_zone_busy(True)
        self.zone_status.set_text("Applying time zone…")
        run_async(lambda: region.set_timezone(zone), self.applied, self.failed)

    def applied(self, zone):
        self.set_zone_busy(False)
        self.zone_status.set_text(f"Applied: {zone}. No logout needed.")
        self.update_preview()
        return GLib.SOURCE_REMOVE

    def failed(self, error):
        self.set_zone_busy(False)
        self.zone_status.set_text(str(error))
        return GLib.SOURCE_REMOVE
