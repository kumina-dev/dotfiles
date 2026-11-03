import QtQuick
import org.kde.bluezqt as BluezQt
import org.kde.plasma.workspace.dbus as DBus

QtObject {
    id: root
    property var manager: BluezQt.Manager
    property var adapter: manager.usableAdapter || manager.adapters[0] || null
    readonly property bool available: Boolean(manager.operational && adapter)
    readonly property bool powered: available && Boolean(adapter.powered)
    readonly property bool blocked: Boolean(manager.bluetoothBlocked)
    readonly property string connectedName: {
        if (!available || !powered) return ""
        const names = []
        for (const device of adapter.devices) {
            if (device.connected) names.push(String(device.friendlyName || device.name || "Bluetooth device"))
        }
        return names.join(", ")
    }
    readonly property string subtitle: !manager.operational ? "Unavailable"
        : !adapter ? "No adapter" : blocked ? "Blocked — open Bluetooth settings"
        : change.busy ? "Applying…" : !powered ? "Off" : connectedName ? "Connected" : "On"
    property alias bus: change.bus
    property alias timeoutMs: change.timeoutMs
    readonly property bool busy: change.busy
    readonly property string error: change.error
    property BackendChange change: BackendChange {
        id: change
        label: "Bluetooth"
        available: root.available
        identity: root.adapter ? root.adapter.ubi : ""
        observed: root.powered
        makeMessage: function(value) {
            return {service:"org.bluez", path:root.adapter.ubi,
                iface:"org.freedesktop.DBus.Properties", member:"Set", signature:"(ssv)",
                arguments:["org.bluez.Adapter1", "Powered", new DBus.variant(value)]}
        }
    }
    function toggle() {
        if (blocked) { change.error = "Bluetooth is blocked. Unblock it in Bluetooth settings or with the hardware switch."; return }
        change.set(!powered)
    }
}
