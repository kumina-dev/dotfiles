#!/usr/bin/env python3

import subprocess

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib


def run(command):
    return subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True,
    )


def command_output(command):
    result = run(command)

    if result.returncode != 0:
        return ""

    return result.stdout.strip()


class ControlCenter(Gtk.Window):
    def __init__(self):
        super().__init__(title="Kumina Control Center")

        self.set_default_size(420, 520)
        self.set_resizable(False)
        self.set_border_width(18)

        self.connect("destroy", Gtk.main_quit)

        self.load_css()

        root = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=14,
        )

        self.add(root)

        header = Gtk.Label(label="Control Center")
        header.set_halign(Gtk.Align.START)
        header.get_style_context().add_class("title")

        root.pack_start(header, False, False, 0)

        root.pack_start(
            self.create_connectivity(),
            False,
            False,
            0,
        )

        root.pack_start(
            self.create_volume(),
            False,
            False,
            0,
        )

        root.pack_start(
            self.create_media(),
            False,
            False,
            0,
        )

        GLib.timeout_add_seconds(
            2,
            self.refresh_state,
        )

    def load_css(self):
        css = """
        window {
            background-color: @window_bg_color;
            color: @window_fg_color;
        }

        .title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .card {
            background-color: alpha(@window_fg_color, 0.06);
            border-radius: 14px;
            padding: 14px;
        }

        .section-title {
            font-weight: 600;
            font-size: 15px;
        }

        .secondary {
            color: alpha(@window_fg_color, 0.62);
        }

        button {
            background-image: none;
            background-color: alpha(@window_fg_color, 0.07);
            color: @window_fg_color;
            border: none;
            border-radius: 10px;
            box-shadow: none;
            text-shadow: none;
            outline: none;
            padding: 9px 12px;
        }

        button:hover {
            background-image: none;
            background-color: alpha(@accent_color, 0.14);
            color: @window_fg_color;
            box-shadow: none;
        }

        button:focus {
            background-image: none;
            background-color: alpha(@window_fg_color, 0.07);
            color: @window_fg_color;
            box-shadow: none;
            outline: none;
        }

        button:active {
            background-image: none;
            background-color: alpha(@accent_color, 0.20);
            color: @window_fg_color;
            box-shadow: none;
        }

        button.active,
        button.active:focus {
            background-image: none;
            background-color: @accent_color;
            color: @accent_fg_color;
            box-shadow: none;
        }

        scale trough {
            background-color: alpha(@window_fg_color, 0.12);
            border-radius: 8px;
            min-height: 6px;
        }

        scale highlight {
            background-color: @accent_color;
            border-radius: 8px;
        }

        scale slider {
            background-color: @window_fg_color;
            border: none;
            min-width: 16px;
            min-height: 16px;
            border-radius: 999px;
        }
        """

        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())

        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def create_card(self):
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
        )

        box.get_style_context().add_class("card")

        return box

    def create_connectivity(self):
        card = self.create_card()

        title = Gtk.Label(label="Connectivity")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("section-title")

        card.pack_start(title, False, False, 0)

        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        wifi_button = Gtk.Button()
        bluetooth_button = Gtk.Button()

        self.wifi_button = wifi_button
        self.bluetooth_button = bluetooth_button

        wifi_button.set_hexpand(True)
        bluetooth_button.set_hexpand(True)

        wifi_button.connect(
            "clicked",
            self.toggle_wifi,
        )

        bluetooth_button.connect(
            "clicked",
            self.toggle_bluetooth,
        )

        row.pack_start(
            wifi_button,
            True,
            True,
            0,
        )

        row.pack_start(
            bluetooth_button,
            True,
            True,
            0,
        )

        card.pack_start(
            row,
            False,
            False,
            0,
        )

        self.refresh_connectivity()

        return card

    def refresh_connectivity(self):
        wifi_state = command_output(
            "nmcli radio wifi"
        )

        wifi_active = wifi_state == "enabled"

        if wifi_active:
            wifi_name = command_output(
                "nmcli -t -f active,ssid dev wifi "
                "| grep '^yes:' "
                "| head -n1 "
                "| cut -d: -f2-"
            )

            if wifi_name:
                wifi_label = f"󰤨 {wifi_name}"
            else:
                wifi_label = "󰤨  Wi-Fi"
        else:
            wifi_label = "󰤭  Wi-Fi"

        self.wifi_button.set_label(wifi_label)

        self.set_active_style(
            self.wifi_button,
            wifi_active,
        )

        bluetooth_state = command_output(
            "bluetoothctl show "
            "| grep 'Powered:' "
            "| awk '{print $2}'"
        )

        bluetooth_active = (
            bluetooth_state == "yes"
        )

        if bluetooth_active:
            device = command_output(
                "bluetoothctl devices Connected "
                "| head -n1 "
                "| cut -d' ' -f3-"
            )

            if device:
                bluetooth_label = f"  {device}"
            else:
                bluetooth_label = "  Bluetooth"
        else:
            bluetooth_label = "󰂲  Bluetooth"

        self.bluetooth_button.set_label(
            bluetooth_label
        )

        self.set_active_style(
            self.bluetooth_button,
            bluetooth_active,
        )

    def set_active_style(
        self,
        button,
        active,
    ):
        context = button.get_style_context()

        if active:
            context.add_class("active")
        else:
            context.remove_class("active")

    def toggle_wifi(self, _button):
        state = command_output(
            "nmcli radio wifi"
        )

        if state == "enabled":
            run("nmcli radio wifi off")
        else:
            run("nmcli radio wifi on")

        self.refresh_connectivity()

    def toggle_bluetooth(self, _button):
        state = command_output(
            "bluetoothctl show | grep 'Powered:' | awk '{print $2}'"
        )

        if state == "yes":
            run("bluetoothctl power off")
        else:
            run("bluetoothctl power on")

        self.refresh_connectivity()

    def create_volume(self):
        card = self.create_card()

        header = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )

        title = Gtk.Label(label="Sound")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("section-title")

        self.volume_label = Gtk.Label()
        self.volume_label.set_halign(Gtk.Align.END)

        self.mute_button = Gtk.Button()
        self.mute_button.connect(
            "clicked",
            self.toggle_mute,
        )

        header.pack_start(
            title,
            True,
            True,
            0,
        )

        header.pack_end(
            self.mute_button,
            False,
            False,
            0,
        )

        header.pack_end(
            self.volume_label,
            False,
            False,
            0,
        )

        card.pack_start(
            header,
            False,
            False,
            0,
        )

        self.volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            0,
            100,
            1,
        )

        self.volume_scale.set_draw_value(False)

        volume = self.get_volume()

        self.volume_scale.set_value(volume)
        self.volume_label.set_text(f"{volume}%")

        self.volume_scale.connect(
            "value-changed",
            self.volume_changed,
        )

        card.pack_start(
            self.volume_scale,
            False,
            False,
            0,
        )

        self.refresh_volume()

        return card

    def get_volume(self):
        output = command_output(
            "wpctl get-volume @DEFAULT_AUDIO_SINK@"
        )

        try:
            value = float(
                output.split()[1]
            )

            return round(value * 100)
        except (IndexError, ValueError):
            return 0

    def volume_changed(self, scale):
        value = int(scale.get_value())

        self.volume_label.set_text(
            f"{value}%"
        )

        run(
            f"wpctl set-volume "
            f"@DEFAULT_AUDIO_SINK@ "
            f"{value}%"
        )

    def get_player(self):
        players = command_output(
            "playerctl -l"
        ).splitlines()

        if not players:
            return ""

        # Prefer a player that is currently playing.
        for player in players:
            status = command_output(
                f"playerctl --player={player} status"
            )

            if status == "Playing":
                return player

        # If nothing is playing, prefer a paused player.
        for player in players:
            status = command_output(
                f"playerctl --player='{player}' status"
            )

            if status == "Paused":
                return player

        # Last resort: first available MPRIS player.
        return players[0]

    def create_media(self):
        card = self.create_card()

        title = Gtk.Label(label="Media")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("section-title")

        card.pack_start(
            title,
            False,
            False,
            0,
        )

        metadata = command_output(
            "playerctl metadata "
            "--format '{{artist}} — {{title}}'"
        )

        if not metadata:
            metadata = "Nothing playing"

        self.media_label = Gtk.Label(
            label=metadata
        )

        self.media_label.set_halign(
            Gtk.Align.START
        )

        self.media_label.set_ellipsize(
            3
        )

        self.media_label.get_style_context().add_class(
            "secondary"
        )

        card.pack_start(
            self.media_label,
            False,
            False,
            0,
        )

        controls = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
        )

        previous = Gtk.Button(label="󰒮")
        self.play_pause_button = Gtk.Button(label="󰐎")
        next_button = Gtk.Button(label="󰒭")

        previous.set_can_focus(False)
        self.play_pause_button.set_can_focus(False)
        next_button.set_can_focus(False)

        previous.connect(
            "clicked",
            lambda _: self.media_command(
                "previous"
            ),
        )

        self.play_pause_button.connect(
            "clicked",
            self.media_play_pause,
        )

        next_button.connect(
            "clicked",
            lambda _: self.media_command(
                "next"
            ),
        )

        controls.pack_start(
            previous,
            True,
            True,
            0,
        )

        controls.pack_start(
            self.play_pause_button,
            True,
            True,
            0,
        )

        controls.pack_start(
            next_button,
            True,
            True,
            0,
        )

        card.pack_start(
            controls,
            False,
            False,
            0,
        )

        return card

    def refresh_media(self):
        player = self.get_player()

        if not player:
            self.media_label.set_text(
                "Nothing playing"
            )
            self.play_pause_button.set_label(
                "󰐊"
            )
            return

        metadata = command_output(
            f"playerctl --player='{player}' "
            "metadata "
            "--format '{{artist}} — {{title}}'"
        )

        status = command_output(
            f"playerctl --player='{player}' status"
        )

        self.media_label.set_text(
            metadata or "Nothing playing"
        )

        if status == "Playing":
            self.play_pause_button.set_label(
                "󰏤"
            )
        else:
            self.play_pause_button.set_label(
                "󰐊"
            )

    def media_play_pause(self, _button):
        self.media_command("play-pause")

    def media_command(self, command):
        player = self.get_player()

        if not player:
            return

        run(
            f"playerctl --player='{player}' "
            f"{command}"
        )

        GLib.timeout_add(
            150,
            self.refresh_media_once,
        )


    def refresh_media_once(self):
        self.refresh_media()
        return False

    def refresh_state(self):
        self.refresh_connectivity()
        self.refresh_volume()
        self.refresh_media()

        return True

    def refresh_volume(self):
        output = command_output(
            "wpctl get-volume @DEFAULT_AUDIO_SINK@"
        )

        muted = "[MUTED]" in output
        volume = self.get_volume()

        if not self.volume_scale.has_focus():
            self.volume_scale.set_value(volume)

        self.volume_label.set_text(
            f"{volume}%"
        )

        self.mute_button.set_label(
            "󰝟" if muted else ""
        )


    def toggle_mute(self, _button):
        run(
            "wpctl set-mute "
            "@DEFAULT_AUDIO_SINK@ toggle"
        )

        self.refresh_volume()


window = ControlCenter()
window.show_all()

Gtk.main()