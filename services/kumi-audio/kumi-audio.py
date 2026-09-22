#!/usr/bin/env python3

import threading

import gi
import pulsectl

gi.require_version("GLib", "2.0")
gi.require_version("Gio", "2.0")

from gi.repository import GLib, Gio


BUS_NAME = "org.kumios.Audio"
OBJECT_PATH = "/org/kumios/Audio"
INTERFACE = "org.kumios.Audio"


INTROSPECTION_XML = f"""
<node>
  <interface name="{INTERFACE}">
    <property name="Volume" type="d" access="read"/>
    <property name="Muted" type="b" access="read"/>
    <property name="DeviceName" type="s" access="read"/>

    <method name="SetVolume">
      <arg name="volume" type="d" direction="in"/>
    </method>

    <method name="SetMuted">
      <arg name="muted" type="b" direction="in"/>
    </method>

    <method name="ToggleMuted"/>
  </interface>
</node>
"""


class KumiAudioService:
    def __init__(self):
        self.loop = GLib.MainLoop()

        self.connection = None
        self.registration_id = None

        self.volume = 0.0
        self.muted = False
        self.device_name = "No audio output"

        self.default_sink_name = None

        self.pulse = pulsectl.Pulse("kumios-audio")

        self.node_info = Gio.DBusNodeInfo.new_for_xml(
            INTROSPECTION_XML
        )
        self.interface_info = self.node_info.interfaces[0]

        self.refresh_state()

    # -----------------------------------------------------
    # Startup
    # -----------------------------------------------------

    def start(self):
        Gio.bus_own_name(
            Gio.BusType.SESSION,
            BUS_NAME,
            Gio.BusNameOwnerFlags.NONE,
            self.on_bus_acquired,
            None,
            None,
        )

        self.start_event_listener()

        print("KumiAudio ready")
        print(f"Device: {self.device_name}")
        print(f"Volume: {self.volume:.2f}")
        print(f"Muted: {self.muted}")

        self.loop.run()

    def on_bus_acquired(self, connection, name):
        self.connection = connection

        self.registration_id = connection.register_object(
            OBJECT_PATH,
            self.interface_info,
            self.handle_method_call,
            self.handle_get_property,
            None,
        )

    # -----------------------------------------------------
    # PulseAudio / PipeWire state
    # -----------------------------------------------------

    def get_default_sink(self):
        info = self.pulse.server_info()

        self.default_sink_name = info.default_sink_name

        if not self.default_sink_name:
            return None

        try:
            return self.pulse.get_sink_by_name(
                self.default_sink_name
            )
        except pulsectl.PulseError:
            return None

    def refresh_state(self):
        sink = self.get_default_sink()

        if sink is None:
            self.update_state(
                volume=0.0,
                muted=False,
                device_name="No audio output",
            )
            return

        self.update_state(
            volume=float(sink.volume.value_flat),
            muted=bool(sink.mute),
            device_name=(
                sink.description
                or sink.name
                or "Audio output"
            ),
        )

    # -----------------------------------------------------
    # State changes
    # -----------------------------------------------------

    def update_state(
        self,
        *,
        volume,
        muted,
        device_name,
    ):
        changed = {}

        volume = max(
            0.0,
            min(1.0, float(volume)),
        )

        muted = bool(muted)
        device_name = str(device_name)

        if abs(volume - self.volume) > 0.0001:
            self.volume = volume

            changed["Volume"] = GLib.Variant(
                "d",
                self.volume,
            )

        if muted != self.muted:
            self.muted = muted

            changed["Muted"] = GLib.Variant(
                "b",
                self.muted,
            )

        if device_name != self.device_name:
            self.device_name = device_name

            changed["DeviceName"] = GLib.Variant(
                "s",
                self.device_name,
            )

        if changed:
            self.emit_properties_changed(changed)

    def emit_properties_changed(self, changed):
        if self.connection is None:
            return

        self.connection.emit_signal(
            None,
            OBJECT_PATH,
            "org.freedesktop.DBus.Properties",
            "PropertiesChanged",
            GLib.Variant(
                "(sa{sv}as)",
                (
                    INTERFACE,
                    changed,
                    [],
                ),
            ),
        )

    # -----------------------------------------------------
    # Pulse event listener
    # -----------------------------------------------------

    def start_event_listener(self):
        thread = threading.Thread(
            target=self.event_loop,
            daemon=True,
        )

        thread.start()

    def event_loop(self):
        event_pulse = pulsectl.Pulse(
            "kumios-audio-events"
        )

        event_pulse.event_mask_set(
            "sink",
            "server",
        )

        def on_event(event):
            GLib.idle_add(
                self.refresh_state
            )

        event_pulse.event_callback_set(
            on_event
        )

        try:
            event_pulse.event_listen()
        except pulsectl.PulseError as exc:
            print(
                f"Audio event listener stopped: {exc}"
            )

    # -----------------------------------------------------
    # Audio controls
    # -----------------------------------------------------

    def set_volume(self, value):
        sink = self.get_default_sink()

        if sink is None:
            return

        value = max(
            0.0,
            min(1.0, float(value)),
        )

        self.pulse.volume_set_all_chans(
            sink,
            value,
        )

        self.refresh_state()

    def set_muted(self, muted):
        sink = self.get_default_sink()

        if sink is None:
            return

        self.pulse.mute(
            sink,
            bool(muted),
        )

        self.refresh_state()

    def toggle_muted(self):
        self.set_muted(
            not self.muted
        )

    # -----------------------------------------------------
    # D-Bus methods
    # -----------------------------------------------------

    def handle_method_call(
        self,
        connection,
        sender,
        object_path,
        interface_name,
        method_name,
        parameters,
        invocation,
    ):
        try:
            if method_name == "SetVolume":
                value = parameters.unpack()[0]

                self.set_volume(value)

            elif method_name == "SetMuted":
                muted = parameters.unpack()[0]

                self.set_muted(muted)

            elif method_name == "ToggleMuted":
                self.toggle_muted()

            else:
                invocation.return_dbus_error(
                    f"{INTERFACE}.UnknownMethod",
                    f"Unknown method: {method_name}",
                )
                return

            invocation.return_value(None)

        except Exception as exc:
            invocation.return_dbus_error(
                f"{INTERFACE}.Error",
                str(exc),
            )

    # -----------------------------------------------------
    # D-Bus properties
    # -----------------------------------------------------

    def handle_get_property(
        self,
        connection,
        sender,
        object_path,
        interface_name,
        property_name,
    ):
        if property_name == "Volume":
            return GLib.Variant(
                "d",
                self.volume,
            )

        if property_name == "Muted":
            return GLib.Variant(
                "b",
                self.muted,
            )

        if property_name == "DeviceName":
            return GLib.Variant(
                "s",
                self.device_name,
            )

        raise GLib.Error(
            f"Unknown property: {property_name}"
        )


if __name__ == "__main__":
    service = KumiAudioService()

    try:
        service.start()
    except KeyboardInterrupt:
        pass