#!/usr/bin/env python3

import calendar
from datetime import date, timedelta

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


MONTHS = [
    "Tammikuu",
    "Helmikuu",
    "Maaliskuu",
    "Huhtikuu",
    "Toukokuu",
    "Kesäkuu",
    "Heinäkuu",
    "Elokuu",
    "Syyskuu",
    "Lokakuu",
    "Marraskuu",
    "Joulukuu",
]

WEEKDAYS = [
    "Ma",
    "Ti",
    "Ke",
    "To",
    "Pe",
    "La",
    "Su",
]


CSS = """
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
    min-height: 34px;
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

        self.set_default_size(340, 350)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.current_date = date.today()
        self.display_year = self.current_date.year
        self.display_month = self.current_date.month

        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", Gtk.main_quit)

        self.load_css()
        self.build_ui()
        self.render_calendar()

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
        root.set_name("calendar")
        self.add(root)

        header = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=4,
        )
        header.set_name("header")

        previous = Gtk.Button(label="‹")
        previous.set_tooltip_text("Edellinen kuukausi")
        previous.connect("clicked", self.previous_month)

        next_button = Gtk.Button(label="›")
        next_button.set_tooltip_text("Seuraava kuukausi")
        next_button.connect("clicked", self.next_month)

        today = Gtk.Button(label="Tänään")
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

    def render_calendar(self):
        for child in self.calendar_grid.get_children():
            self.calendar_grid.remove(child)

        self.month_label.set_text(
            f"{MONTHS[self.display_month - 1]} {self.display_year}"
        )

        for column, weekday in enumerate(WEEKDAYS):
            label = Gtk.Label(label=weekday)
            label.get_style_context().add_class("weekday")
            label.set_halign(Gtk.Align.CENTER)

            self.calendar_grid.attach(label, column, 0, 1, 1)

        cal = calendar.Calendar(firstweekday=0)

        days = list(
            cal.itermonthdates(
                self.display_year,
                self.display_month,
            )
        )

        # Always render exactly six weeks / 42 days.
        while len(days) < 42:
            days.append(days[-1] + timedelta(days=1))

        for index, day_date in enumerate(days):
            row = (index // 7) + 1
            column = index % 7

            button = Gtk.Button(label=str(day_date.day))
            button.get_style_context().add_class("day")

            is_current_month = (
                day_date.year == self.display_year
                and day_date.month == self.display_month
            )

            if not is_current_month:
                button.get_style_context().add_class("outside-month")

            if day_date == self.current_date:
                button.get_style_context().add_class("today")

            if is_current_month:
                button.connect(
                    "clicked",
                    self.day_clicked,
                    day_date.year,
                    day_date.month,
                    day_date.day,
                )

            self.calendar_grid.attach(
                button,
                column,
                row,
                1,
                1,
            )

        self.calendar_grid.show_all()

    def previous_month(self, _button):
        if self.display_month == 1:
            self.display_month = 12
            self.display_year -= 1
        else:
            self.display_month -= 1

        self.render_calendar()

    def next_month(self, _button):
        if self.display_month == 12:
            self.display_month = 1
            self.display_year += 1
        else:
            self.display_month += 1

        self.render_calendar()

    def go_today(self, _button):
        self.display_year = self.current_date.year
        self.display_month = self.current_date.month
        self.render_calendar()

    def day_clicked(self, _button, year, month, day):
        print(f"{year:04d}-{month:02d}-{day:02d}")

    def on_key_press(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True

        return False


window = CalendarWindow()
window.show_all()

Gtk.main()
