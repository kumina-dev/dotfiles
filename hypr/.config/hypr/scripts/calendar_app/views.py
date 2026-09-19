from datetime import date
from gi.repository import Gtk, Pango

from calendar_app import events
from kumina_common import region
from kumina_common.async_utils import run_async
from kumina_common.i18n import translate as tr


def wrapped_label(text):
    label = Gtk.Label(label=text, xalign=0)
    label.set_line_wrap(True)
    label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    label.set_max_width_chars(36)
    return label


class EventEditor(Gtk.Dialog):
    def __init__(self, parent, day, on_saved, event=None):
        super().__init__(title=tr('Edit event') if event else tr('Add event'), transient_for=parent, modal=True)
        self.set_default_size(440, 360)
        self.set_destroy_with_parent(True)
        self.event = event
        self.on_saved = on_saved
        self._saving = False
        self._destroyed = False
        self.connect('destroy', self.destroyed)
        self.connect('delete-event', lambda *_: self._saving)
        self.add_button(tr('Cancel'), Gtk.ResponseType.CANCEL)
        self.add_button(tr('Save'), Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)
        content = self.get_content_area()
        content.set_border_width(16)
        content.set_spacing(10)
        content.pack_start(wrapped_label(tr('Title')), False, False, 0)
        self.title_entry = Gtk.Entry()
        self.title_entry.set_max_length(160)
        self.title_entry.set_activates_default(True)
        self.title_entry.set_text(event.title if event else '')
        content.pack_start(self.title_entry, False, False, 0)
        content.pack_start(wrapped_label(tr('Date (YYYY-MM-DD)')), False, False, 0)
        self.date_entry = Gtk.Entry()
        self.date_entry.set_text(event.day if event else day.isoformat())
        content.pack_start(self.date_entry, False, False, 0)
        content.pack_start(wrapped_label(tr('Notes (optional, up to 2000 characters)')), False, False, 0)
        self.notes = Gtk.TextView()
        self.notes.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.notes.get_buffer().set_text(event.notes if event else '')
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(100)
        scroll.add(self.notes)
        content.pack_start(scroll, True, True, 0)
        self.status = wrapped_label(tr('All-day event'))
        content.pack_start(self.status, False, False, 0)
        self.connect('response', self.respond)
        self.show_all()
        self.title_entry.grab_focus()

    def destroyed(self, _widget):
        self._destroyed = True

    def respond(self, _dialog, response):
        if self._saving:
            return
        if response != Gtk.ResponseType.OK:
            self.destroy()
            return
        buffer = self.notes.get_buffer()
        try:
            values = events.validate_event(
                self.date_entry.get_text().strip(), self.title_entry.get_text(),
                buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True),
            )
        except events.CalendarError as error:
            self.status.set_text(str(error))
            return
        self._saving = True
        self.get_content_area().set_sensitive(False)
        self.set_response_sensitive(Gtk.ResponseType.OK, False)
        self.set_response_sensitive(Gtk.ResponseType.CANCEL, False)
        self.status.set_text(tr('Saving…'))
        event_id = self.event.id if self.event else None
        run_async(lambda: events.save(*values, event_id=event_id), self.saved, self.failed)

    def saved(self, event):
        if self._destroyed:
            return False
        self.on_saved(date.fromisoformat(event.day))
        self.destroy()
        return False

    def failed(self, error):
        if self._destroyed:
            return False
        self._saving = False
        self.get_content_area().set_sensitive(True)
        self.set_response_sensitive(Gtk.ResponseType.OK, True)
        self.set_response_sensitive(Gtk.ResponseType.CANCEL, True)
        self.status.set_text(str(error))
        return False


class Agenda(Gtk.Box):
    def __init__(self, on_changed):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.on_changed = on_changed
        self.day = region.local_now().date()
        self._generation = 0
        self._destroyed = False
        self._deleting = False
        self.connect('destroy', self.destroyed)
        self.heading = wrapped_label('')
        self.heading.get_style_context().add_class('agenda-heading')
        self.pack_start(self.heading, False, False, 0)
        self.pack_start(wrapped_label(tr('Local all-day events')), False, False, 0)
        buttons = Gtk.Box(spacing=8)
        self.add_button = Gtk.Button(label=tr('Add event'))
        self.add_button.connect('clicked', lambda *_: self.edit())
        buttons.pack_start(self.add_button, True, True, 0)
        self.refresh_button = Gtk.Button(label=tr('Refresh'))
        self.refresh_button.connect('clicked', lambda *_: self.on_changed(self.day))
        buttons.pack_start(self.refresh_button, False, False, 0)
        self.pack_start(buttons, False, False, 0)
        self.list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.list_box)
        self.pack_start(scroll, True, True, 0)
        self.status = wrapped_label('')
        self.pack_start(self.status, False, False, 0)

    def destroyed(self, _widget):
        self._destroyed = True
        self._generation += 1

    def set_day(self, day):
        self.day = day
        self.heading.set_text(region.format_date(day, region.read_preferences()))
        self._generation += 1
        generation = self._generation
        for child in self.list_box.get_children():
            child.destroy()
        self.status.set_text(tr('Loading…'))
        self.refresh_button.set_sensitive(False)
        key = day.isoformat()
        run_async(lambda: events.list_range(key, key),
                  lambda rows: self.loaded(rows, generation),
                  lambda error: self.failed(error, generation))

    def loaded(self, rows, generation):
        if self._destroyed or generation != self._generation:
            return False
        self.refresh_button.set_sensitive(True)
        self.status.set_text('' if rows else tr('No events for this day.'))
        for event in rows:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            card.get_style_context().add_class('event-card')
            title = wrapped_label(event.title)
            title.set_selectable(True)
            card.pack_start(title, False, False, 0)
            if event.notes:
                note = wrapped_label(event.notes)
                note.set_lines(3)
                note.set_ellipsize(Pango.EllipsizeMode.END)
                note.set_tooltip_text(event.notes)
                card.pack_start(note, False, False, 0)
            actions = Gtk.Box(spacing=4)
            edit = Gtk.Button(label=tr('Edit'))
            edit.connect('clicked', lambda _button, item=event: self.edit(item))
            remove = Gtk.Button(label=tr('Delete'))
            remove.connect('clicked', lambda _button, item=event: self.confirm_delete(item))
            actions.pack_end(remove, False, False, 0)
            actions.pack_end(edit, False, False, 0)
            card.pack_start(actions, False, False, 0)
            self.list_box.pack_start(card, False, False, 0)
        self.list_box.show_all()
        return False

    def failed(self, error, generation):
        if self._destroyed or generation != self._generation:
            return False
        self.refresh_button.set_sensitive(True)
        self.status.set_text(str(error))
        return False

    def edit(self, event=None):
        EventEditor(self.get_toplevel(), self.day, self.on_changed, event)

    def confirm_delete(self, event):
        if self._deleting:
            return
        dialog = Gtk.MessageDialog(transient_for=self.get_toplevel(), modal=True,
                                   message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.NONE, text=tr('Delete event?'))
        dialog.format_secondary_text(event.title)
        dialog.add_button(tr('Cancel'), Gtk.ResponseType.CANCEL)
        dialog.add_button(tr('Delete'), Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        response = dialog.run()
        dialog.destroy()
        if response != Gtk.ResponseType.OK or self._destroyed:
            return
        self._deleting = True
        self.set_sensitive(False)
        self.status.set_text(tr('Deleting…'))
        run_async(lambda: events.delete(event.id), self.deleted, self.delete_failed)

    def deleted(self, _result):
        if self._destroyed:
            return False
        self._deleting = False
        self.set_sensitive(True)
        self.on_changed(self.day)
        return False

    def delete_failed(self, error):
        if self._destroyed:
            return False
        self._deleting = False
        self.set_sensitive(True)
        self.status.set_text(str(error))
        return False
