from gi.repository import Gtk, Gdk


class CompactSwitch(Gtk.EventBox):
    WIDTH = 38
    HEIGHT = 22
    KNOB = 16
    PADDING = 3

    def __init__(self):
        super().__init__()

        self._active = False
        self._callbacks = []

        self.set_size_request(
            self.WIDTH,
            self.HEIGHT,
        )

        self.set_above_child(True)

        self.area = Gtk.DrawingArea()

        self.area.set_size_request(
            self.WIDTH,
            self.HEIGHT,
        )

        self.add(self.area)

        self.area.connect(
            "draw",
            self.on_draw,
        )

        self.connect(
            "button-release-event",
            self.on_click,
        )

    def get_active(self):
        return self._active

    def set_active(
        self,
        active,
        emit=True,
    ):
        active = bool(active)

        if self._active == active:
            return

        self._active = active

        self.area.queue_draw()

        if emit:
            for callback in self._callbacks:
                callback(self)

    def connect_toggled(
        self,
        callback,
    ):
        self._callbacks.append(
            callback
        )

    def on_click(
        self,
        _widget,
        _event,
    ):
        self.set_active(
            not self._active
        )

        return True

    def on_draw(
        self,
        _widget,
        cr,
    ):
        context = self.get_style_context()

        fg = context.get_color(
            Gtk.StateFlags.NORMAL
        )

        if self._active:
            track = Gdk.RGBA()
            track.parse("#3584e4")
        else:
            track = Gdk.RGBA()
            track.red = fg.red
            track.green = fg.green
            track.blue = fg.blue
            track.alpha = 0.18

        radius = self.HEIGHT / 2

        self.rounded_rect(
            cr,
            0,
            0,
            self.WIDTH,
            self.HEIGHT,
            radius,
        )

        cr.set_source_rgba(
            track.red,
            track.green,
            track.blue,
            track.alpha,
        )

        cr.fill()

        if self._active:
            knob_x = (
                self.WIDTH
                - self.PADDING
                - self.KNOB
            )
        else:
            knob_x = self.PADDING

        knob_y = (
            self.HEIGHT - self.KNOB
        ) / 2

        cr.arc(
            knob_x + self.KNOB / 2,
            knob_y + self.KNOB / 2,
            self.KNOB / 2,
            0,
            2 * 3.141592653589793,
        )

        cr.set_source_rgba(
            1,
            1,
            1,
            1,
        )

        cr.fill()

        return False

    @staticmethod
    def rounded_rect(
        cr,
        x,
        y,
        width,
        height,
        radius,
    ):
        pi = 3.141592653589793

        cr.new_sub_path()

        cr.arc(
            x + width - radius,
            y + radius,
            radius,
            -pi / 2,
            0,
        )

        cr.arc(
            x + width - radius,
            y + height - radius,
            radius,
            0,
            pi / 2,
        )

        cr.arc(
            x + radius,
            y + height - radius,
            radius,
            pi / 2,
            pi,
        )

        cr.arc(
            x + radius,
            y + radius,
            radius,
            pi,
            3 * pi / 2,
        )

        cr.close_path()