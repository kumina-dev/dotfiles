from pathlib import Path

from gi.repository import Gdk, Gtk


STYLE_PATH = (
    Path(__file__).parent
    / "style.css"
)


def load():
    screen = Gdk.Screen.get_default()

    if screen is None:
        return

    provider = Gtk.CssProvider()

    provider.load_from_path(
        str(STYLE_PATH)
    )

    Gtk.StyleContext.add_provider_for_screen(
        screen,
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )