from gi.repository import Gtk

from control_center.widgets.sound import SoundCard


class SoundView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.get_style_context().add_class("content")

        title = Gtk.Label(label="Sound", xalign=0)
        title.get_style_context().add_class("page-title")
        description = Gtk.Label(
            label="Choose your output and microphone, then adjust their volume.",
            xalign=0,
        )
        description.set_line_wrap(True)
        description.get_style_context().add_class("page-description")
        self.pack_start(title, False, False, 0)
        self.pack_start(description, False, False, 0)

        self.sound = SoundCard(card_class="settings-card")
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.add(self.sound)
        self.pack_start(scroller, True, True, 0)

    def refresh(self):
        return self.sound.refresh()
