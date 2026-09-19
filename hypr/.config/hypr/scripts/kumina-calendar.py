#!/usr/bin/env python3

from datetime import date

from kumina_common import region
from kumina_common.i18n import MONTHS as MONTH_NAMES, WEEKDAYS as DAY_NAMES, translate as tr
from single_instance import acquire


if not acquire(
    "calendar"
):
    raise SystemExit(0)


import gi

gi.require_version(
    "Gtk",
    "3.0",
)

gi.require_version(
    "Gdk",
    "3.0",
)

from gi.repository import (
    Gdk,
    GLib,
    Gtk,
)


from calendar_app import events
from calendar_app.model import month_days
from calendar_app.views import Agenda
from kumina_common.async_utils import run_async


MONTHS = [tr(name) for name in MONTH_NAMES]
WEEKDAYS = [tr(name) for name in DAY_NAMES]


CSS = """
.day.selected-day {
    border-color: @accent_color;
}
.today.selected-day {
    border-color: @window_fg_color;
}
.agenda-heading {
    font-size: 18px;
    font-weight: 600;
}
.event-card {
    background-color: alpha(@window_fg_color, 0.045);
    border-radius: 10px;
    padding: 10px;
}

window {
    background-color: @window_bg_color;
    color: @window_fg_color;
    border-radius: 16px;
}

#calendar {
    padding: 20px;
}

#header {
    margin-bottom: 14px;
}

#month-label {
    font-size: 18px;
    font-weight: 600;
}

button {
    background-color: transparent;
    background-image: none;
    color: @window_fg_color;
    border: none;
    border-image: none;
    border-radius: 8px;
    box-shadow: none;
    text-shadow: none;
    padding: 6px 10px;
}

button:hover {
    background-color: alpha(@accent_color, 0.14);
    background-image: none;
    box-shadow: none;
}

#today {
    color: @accent_color;
    font-weight: 600;
    padding: 6px 8px;
}

.weekday {
    color: alpha(@window_fg_color, 0.55);
    font-size: 12px;
    font-weight: 600;
}

.day {
    background-color: alpha(@window_fg_color, 0.06);
    background-image: none;
    color: @window_fg_color;
    min-width: 34px;
    min-height: 42px;
    border: 2px solid transparent;
    padding: 0;
}

.day:hover {
    background-color: alpha(@accent_color, 0.16);
    background-image: none;
}

.today {
    background-color: @accent_color;
    background-image: none;
    color: @accent_fg_color;
    font-weight: 600;
}

.today:hover {
    background-color: @accent_color;
    background-image: none;
    color: @accent_fg_color;
}

.outside-month {
    color: alpha(@window_fg_color, 0.25);
    background-color: alpha(@window_fg_color, 0.025);
}

.outside-month:hover {
    color: alpha(@window_fg_color, 0.25);
    background-color: alpha(@window_fg_color, 0.025);
}
"""


class CalendarWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Kumina Calendar")

        self.set_default_size(740, 480)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.preferences = region.read_preferences()
        self.current_date = region.local_now().date()
        self.selected_date = self.current_date
        self._destroyed = False
        self._event_generation = 0
        self._marked_days = set()
        self._day_buttons = {}
        self.display_year = self.current_date.year
        self.display_month = self.current_date.month

        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", Gtk.main_quit)

        self.load_css()
        self.build_ui()
        self.render_calendar()
        self.agenda.set_day(self.selected_date)
        self.refresh_clock()
        self._clock_timer = GLib.timeout_add_seconds(1, self.refresh_clock)
        self.connect("destroy", self.stop_clock)

    def stop_clock(self, _window):
        self._destroyed = True
        self._event_generation += 1
        GLib.source_remove(self._clock_timer)

    def refresh_clock(self):
        now = region.local_now()
        preferences = region.read_preferences()
        changed = now.date() != self.current_date or preferences != self.preferences
        self.current_date = now.date()
        self.preferences = preferences
        self.clock_label.set_text(f"{region.format_date(now, preferences)} · {region.format_time(now, preferences)}")
        if changed:
            self.render_calendar()
            self.agenda.heading.set_text(region.format_date(self.selected_date, self.preferences))
        return GLib.SOURCE_CONTINUE

    def load_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())

        screen = Gdk.Screen.get_default()

        Gtk.StyleContext.add_provider_for_screen(
            screen,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def build_ui(self):
        root = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=0,
        )
        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        outer.set_name("calendar")
        root.set_size_request(330, -1)
        outer.pack_start(root, False, False, 0)
        self.agenda = Agenda(self.select_day)
        self.agenda.set_size_request(320, -1)
        outer.pack_start(self.agenda, True, True, 0)
        self.add(outer)

        header = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=4,
        )
        header.set_name("header")

        previous = Gtk.Button(label="‹")
        previous.set_tooltip_text(tr("Previous month"))
        previous.connect("clicked", self.previous_month)

        next_button = Gtk.Button(label="›")
        next_button.set_tooltip_text(tr("Next month"))
        next_button.connect("clicked", self.next_month)

        today = Gtk.Button(label=tr("Today"))
        today.set_name("today")
        today.connect("clicked", self.go_today)

        self.month_label = Gtk.Label()
        self.month_label.set_name("month-label")
        self.month_label.set_hexpand(True)
        self.month_label.set_halign(Gtk.Align.CENTER)

        header.pack_start(previous, False, False, 0)
        header.pack_start(self.month_label, True, True, 0)
        header.pack_start(next_button, False, False, 0)
        header.pack_end(today, False, False, 0)

        root.pack_start(header, False, False, 0)

        self.calendar_grid = Gtk.Grid()
        self.calendar_grid.set_row_spacing(4)
        self.calendar_grid.set_column_spacing(4)
        self.calendar_grid.set_hexpand(True)
        self.calendar_grid.set_vexpand(True)

        root.pack_start(self.calendar_grid, True, True, 0)

        self.clock_label = Gtk.Label()
        self.clock_label.set_margin_top(12)
        root.pack_start(self.clock_label, False, False, 0)
        self.event_status = Gtk.Label()
        self.event_status.set_line_wrap(True)
        self.event_status.set_max_width_chars(32)
        root.pack_start(self.event_status, False, False, 0)

    def render_calendar(self):
        self._day_buttons = {}
        for child in self.calendar_grid.get_children():
            self.calendar_grid.remove(child)

        self.month_label.set_text(
            f"{MONTHS[self.display_month - 1]} {self.display_year}"
        )

        first = region.first_weekday(self.preferences)
        weekdays = WEEKDAYS[first:] + WEEKDAYS[:first]
        for column, weekday in enumerate(weekdays):
            label = Gtk.Label(label=weekday)
            label.get_style_context().add_class("weekday")
            label.set_halign(Gtk.Align.CENTER)

            self.calendar_grid.attach(label, column, 0, 1, 1)

        days = month_days(self.display_year, self.display_month, first)
        self._visible_days = [day for day in days if day is not None]

        for index, day_date in enumerate(days):
            row = (index // 7) + 1
            column = index % 7

            button = Gtk.Button(label=" ")
            button.get_style_context().add_class("day")
            if day_date is None:
                button.set_sensitive(False)
                self.calendar_grid.attach(button, column, row, 1, 1)
                continue
            self._day_buttons[day_date] = button
            self.update_day_button(day_date, button)

            is_current_month = (
                day_date.year == self.display_year
                and day_date.month == self.display_month
            )

            if not is_current_month:
                button.get_style_context().add_class("outside-month")

            if day_date == self.current_date:
                button.get_style_context().add_class("today")

            button.connect("clicked", lambda _button, day=day_date: self.select_day(day))

            self.calendar_grid.attach(
                button,
                column,
                row,
                1,
                1,
            )

        self.calendar_grid.show_all()
        self.refresh_markers()

    def previous_month(self, _button):
        if self.display_year == 1 and self.display_month == 1:
            return
        if self.display_month == 1:
            self.display_month = 12
            self.display_year -= 1
        else:
            self.display_month -= 1

        self.select_day(date(self.display_year, self.display_month, 1))

    def next_month(self, _button):
        if self.display_year == 9999 and self.display_month == 12:
            return
        if self.display_month == 12:
            self.display_month = 1
            self.display_year += 1
        else:
            self.display_month += 1

        self.select_day(date(self.display_year, self.display_month, 1))

    def go_today(self, _button):
        self.select_day(region.local_now().date())

    def select_day(self, day):
        if self._destroyed:
            return
        self.selected_date = day
        self.display_year, self.display_month = day.year, day.month
        self.render_calendar()
        self.agenda.set_day(day)

    def update_day_button(self, day, button):
        has_events = day.isoformat() in self._marked_days
        button.set_label(f"{day.day}\n{'•' if has_events else ' '}")
        tooltip = region.format_date(day, self.preferences)
        if has_events:
            tooltip += " · " + tr("Has events")
        button.set_tooltip_text(tooltip)
        context = button.get_style_context()
        if day == self.selected_date:
            context.add_class("selected-day")
        else:
            context.remove_class("selected-day")

    def refresh_markers(self):
        self._event_generation += 1
        generation = self._event_generation
        start, end = self._visible_days[0].isoformat(), self._visible_days[-1].isoformat()
        self.event_status.set_text(tr("Loading events…"))
        run_async(lambda: events.list_range(start, end),
                  lambda rows: self.markers_loaded(rows, generation),
                  lambda error: self.markers_failed(error, generation))

    def markers_loaded(self, rows, generation):
        if self._destroyed or generation != self._event_generation:
            return False
        self._marked_days = {event.day for event in rows}
        for day, button in self._day_buttons.items():
            self.update_day_button(day, button)
        self.event_status.set_text("")
        self.event_status.set_tooltip_text(None)
        return False

    def markers_failed(self, error, generation):
        if self._destroyed or generation != self._event_generation:
            return False
        self._marked_days.clear()
        for day, button in self._day_buttons.items():
            self.update_day_button(day, button)
        self.event_status.set_text(tr("Could not load event markers."))
        self.event_status.set_tooltip_text(str(error))
        return False

    def on_key_press(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True

        return False


window = CalendarWindow()
window.show_all()

Gtk.main()
