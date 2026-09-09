from gi.repository import Gtk

from settings_app.views.keyboard import (
    KeyboardView,
)

from settings_app.views.mouse import (
    MouseView,
)


class InputView(Gtk.Box):
    def __init__(self):
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=0,
        )

        self.get_style_context().add_class(
            "content"
        )

        self.keyboard_view = (
            KeyboardView()
        )

        self.mouse_view = (
            MouseView()
        )

        # Input owns the page padding.
        # The existing views become sections
        # inside this page.
        self.keyboard_view.get_style_context().remove_class(
            "content"
        )

        self.mouse_view.get_style_context().remove_class(
            "content"
        )

        sections = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=28,
        )

        sections.pack_start(
            self.keyboard_view,
            False,
            False,
            0,
        )

        sections.pack_start(
            self.mouse_view,
            False,
            False,
            0,
        )

        scroller = Gtk.ScrolledWindow()

        scroller.set_policy(
            Gtk.PolicyType.NEVER,
            Gtk.PolicyType.AUTOMATIC,
        )

        scroller.set_overlay_scrolling(
            True
        )

        scroller.add(
            sections
        )

        self.pack_start(
            scroller,
            True,
            True,
            0,
        )

    def refresh(self):
        self.keyboard_view.refresh()
        self.mouse_view.refresh()