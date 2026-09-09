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
            spacing=18,
        )

        self.get_style_context().add_class(
            "content"
        )

        title = Gtk.Label(
            label="Input",
            xalign=0,
        )

        title.get_style_context().add_class(
            "page-title"
        )

        description = Gtk.Label(
            label=(
                "Configure keyboard, pointer "
                "and scrolling behaviour."
            ),
            xalign=0,
        )

        description.set_line_wrap(
            True
        )

        description.get_style_context().add_class(
            "page-description"
        )

        self.pack_start(
            title,
            False,
            False,
            0,
        )

        self.pack_start(
            description,
            False,
            False,
            0,
        )

        self.keyboard_view = (
            KeyboardView(
                embedded=True
            )
        )

        self.mouse_view = (
            MouseView(
                embedded=True
            )
        )

        sections = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=24,
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