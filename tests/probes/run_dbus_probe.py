#!/usr/bin/env python3
"""Private D-Bus service for the typed property round-trip probe. No real device writes."""
import os
from pathlib import Path
import subprocess
import sys
import threading
import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

if '--session' not in sys.argv:
    raise SystemExit(subprocess.call(['dbus-run-session', '--', sys.executable, __file__, '--session']))

connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
connection.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
                     'org.freedesktop.DBus', 'RequestName',
                     GLib.Variant('(su)', ('org.kumios.Probe', 0)), None,
                     Gio.DBusCallFlags.NONE, 3000, None)
xml = '''<node><interface name="org.kumios.Probe">
<method name="Set"><arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="v" direction="in"/></method>
<method name="SetBrightness"><arg type="i" direction="in"/><arg type="u" direction="in"/></method>
<property name="Enabled" type="b" access="read"/><property name="Brightness" type="i" access="read"/>
</interface></node>'''
enabled = False
brightness = 10

def method(conn, sender, path, iface, member, parameters, invocation):
    global enabled, brightness
    if member == 'SetBrightness':
        value, flags = parameters.unpack()
        if flags != 1 or value < 0:
            invocation.return_dbus_error('org.kumios.Probe.InvalidType', 'Expected typed brightness and flags')
            return
        brightness = value
        changed = {'Brightness': GLib.Variant('i', brightness)}
    else:
        target, key, value = parameters.unpack()
        if key == 'Denied':
            invocation.return_dbus_error('org.kumios.Probe.NotAuthorized', 'Permission denied by test backend')
            return
        if target != 'org.kumios.Probe' or key != 'Enabled' or not isinstance(value, bool):
            invocation.return_dbus_error('org.kumios.Probe.InvalidType', 'Expected boolean variant')
            return
        enabled = value
        changed = {'Enabled': GLib.Variant('b', enabled)}
    connection.emit_signal(None, '/Probe', 'org.freedesktop.DBus.Properties', 'PropertiesChanged',
        GLib.Variant('(sa{sv}as)', ('org.kumios.Probe', changed, [])))
    invocation.return_value(None)

def get_property(conn, sender, path, iface, key):
    return GLib.Variant('b', enabled) if key == 'Enabled' else GLib.Variant('i', brightness)

connection.register_object('/Probe', Gio.DBusNodeInfo.new_for_xml(xml).interfaces[0], method, get_property, None)
loop = GLib.MainLoop()
result = [1]
def run_tests():
    try:
        runner = Path('/usr/lib/qt6/bin/qmltestrunner')
        result[0] = subprocess.call([str(runner), '-input', str(Path(__file__).with_name('tst_DBusRoundTrip.qml')), '-o', '-,txt'],
            env={**os.environ, 'QT_QPA_PLATFORM':'offscreen', 'QT_QUICK_BACKEND':'software'}, timeout=15)
    finally:
        GLib.idle_add(loop.quit)
threading.Thread(target=run_tests).start()
loop.run()
raise SystemExit(result[0])
