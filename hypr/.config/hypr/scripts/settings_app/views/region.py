from kumina_common.i18n import translate as tr

from gi.repository import GLib, Gtk

from kumina_common import region as preferences
from kumina_common import i18n
from kumina_common.formatting import format_number, format_currency
from settings_app import region
from settings_app.async_utils import run_async


class RegionView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.get_style_context().add_class("content")
        self._busy = False
        self._zones_loaded = False
        self._preferences_loaded = False
        title = self.label(tr("Language & Region"), "page-title")
        self.pack_start(title, False, False, 0)
        self.pack_start(self.label(tr("Language, date, time and number preferences."), "page-description"), False, False, 0)

        sections = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.add(sections)
        self.pack_start(scroller, True, True, 0)

        card = self.card(sections)
        self.pack_label(card, tr("Interface language"), "section-title")
        self.language = self.combo(card, tr("Interface language"), i18n.LANGUAGES.items())
        apply_language = Gtk.Button(label=tr("Apply language"))
        apply_language.get_style_context().add_class("primary-action")
        apply_language.connect("clicked", self.save_language)
        card.pack_start(apply_language, False, False, 0)
        self.pack_label(card, tr("Applies to KumiOS apps only. Keyboard layouts and other apps are unchanged. No logout needed."), "page-description")
        self.language_status = self.label("", "settings-status")
        card.pack_start(self.language_status, False, False, 0)
        try:
            language = i18n.read_language(strict=True)
        except RuntimeError as error:
            language = "en"
            self.language_status.set_text(str(error) + tr(" Apply language to replace the invalid file."))
        self.language.set_active_id(language)

        card = self.card(sections)
        self.pack_label(card, tr("Formats"), "section-title")
        self.clock = self.combo(card, tr("Clock"), (("24", tr("24-hour")), ("12", tr("12-hour"))))
        self.date = self.combo(card, tr("Date"), (("day-first", tr("Day.Month.Year")), ("iso", tr("Year-Month-Day")), ("month-first", tr("Month/Day/Year"))))
        self.week = self.combo(card, tr("Week starts on"), (("monday", tr("Monday")), ("sunday", tr("Sunday"))))
        self.number_format = self.combo(card, tr("Number format"), (
            ("fi", tr("Finnish · 1 234,56")),
            ("en", tr("English · 1,234.56")),
        ))
        self.currency = self.combo(card, tr("Currency"), (
            ("EUR", tr("Euro (EUR)")),
            ("USD", tr("US dollar (USD)")),
            ("GBP", tr("Pound sterling (GBP)")),
        ))
        self.preview = self.label("", "page-description")
        card.pack_start(self.preview, False, False, 0)
        for combo in (self.clock, self.date, self.week, self.number_format, self.currency):
            combo.connect("changed", lambda *_: self.update_preview())
        save = Gtk.Button(label=tr("Apply formats"))
        save.get_style_context().add_class("primary-action")
        save.connect("clicked", self.save_formats)
        card.pack_start(save, False, False, 0)
        self.pack_label(card, tr("Applies to the panel, calendar and About this PC. Other apps keep their own formats."), "page-description")
        self.format_status = self.label("", "settings-status")
        card.pack_start(self.format_status, False, False, 0)

        card = self.card(sections)
        self.pack_label(card, tr("System time zone"), "section-title")
        self.timezone = self.combo(card, tr("Time zone"), ())
        self.zone_button = Gtk.Button(label=tr("Apply time zone"))
        self.zone_button.connect("clicked", self.apply_timezone)
        card.pack_start(self.zone_button, False, False, 0)
        self.pack_label(card, tr("Changes the time zone for all users. Authentication may be requested."), "page-description")
        self.zone_status = self.label("", "settings-status")
        card.pack_start(self.zone_status, False, False, 0)
        retry = Gtk.Button(label=tr("Refresh"))
        retry.connect("clicked", lambda *_: self.refresh())
        card.pack_start(retry, False, False, 0)
        self.pack_label(sections, tr("Currency is a display preference; it does not convert amounts. Keyboard layouts are under Input."), "page-description")
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
        return {
            "clock": self.clock.get_active_id(),
            "date": self.date.get_active_id(),
            "week_start": self.week.get_active_id(),
            "number_format": self.number_format.get_active_id(),
            "currency": self.currency.get_active_id(),
        }

    def save_language(self, _button):
        selected = self.language.get_active_id()
        try:
            i18n.save_language(selected)
        except (OSError, ValueError) as error:
            self.language_status.set_text(str(error))
            return
        self.language_status.set_text(tr(
            "Saved. Close and reopen Settings, Control Center, the power menu and calendar to use the new language. The panel updates automatically.",
            language=selected,
        ))

    def load_preferences(self):
        if self._preferences_loaded:
            return
        try:
            values = preferences.read_preferences(strict=True)
        except RuntimeError as error:
            self.format_status.set_text(str(error) + tr(" Apply formats to replace the invalid file."))
            values = preferences.DEFAULTS
        self.clock.set_active_id(values["clock"])
        self.date.set_active_id(values["date"])
        self.week.set_active_id(values["week_start"])
        self.number_format.set_active_id(values["number_format"])
        self.currency.set_active_id(values["currency"])
        self._preferences_loaded = True

    def update_preview(self):
        values = self.values()
        if all(values.values()):
            now = preferences.local_now()
            lines = [
                tr("Preview: {date} · {time}", date=preferences.format_date(now, values), time=preferences.format_time(now, values)),
                tr("Number: {value}", value=format_number("1234567.89", values)),
                tr("Currency: {value}", value=format_currency("1234.56", values)),
            ]
            self.preview.set_text("\n".join(lines))

    def save_formats(self, _button):
        try:
            preferences.save_preferences(self.values())
        except (OSError, ValueError) as error:
            self.format_status.set_text(str(error))
            return
        self.format_status.set_text(tr("Applied. The panel and calendar update automatically. Refresh About this PC for updated numbers."))

    def set_zone_busy(self, busy):
        self._busy = busy
        self.timezone.set_sensitive(not busy and self._zones_loaded)
        self.zone_button.set_sensitive(not busy and self._zones_loaded)

    def refresh(self):
        self.update_preview()
        if self._busy:
            return
        self.set_zone_busy(True)
        self.zone_status.set_text(tr("Loading time zones…"))
        run_async(region.get_state, self.loaded, self.failed)

    def loaded(self, state):
        self.timezone.remove_all()
        for zone in state["timezones"]:
            self.timezone.append(zone, zone)
        self.timezone.set_active_id(state["timezone"])
        self._zones_loaded = True
        self.set_zone_busy(False)
        self.zone_status.set_text(tr("Current: {value}", value=state['timezone']))
        return GLib.SOURCE_REMOVE

    def apply_timezone(self, _button):
        zone = self.timezone.get_active_id()
        self.set_zone_busy(True)
        self.zone_status.set_text(tr("Applying time zone…"))
        run_async(lambda: region.set_timezone(zone), self.applied, self.failed)

    def applied(self, zone):
        self.set_zone_busy(False)
        self.zone_status.set_text(tr("Applied: {zone}. No logout needed.", zone=zone))
        self.update_preview()
        return GLib.SOURCE_REMOVE

    def failed(self, error):
        self.set_zone_busy(False)
        self.zone_status.set_text(str(error))
        return GLib.SOURCE_REMOVE
