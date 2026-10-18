import QtQuick
import org.kde.plasma.networkmanagement as PlasmaNM
import org.kde.plasma.workspace.dbus as DBus

// Own the request independently of list delegates, which can move during scans.
Item {
    id: root
    visible: false

    property var bus: DBus.SystemBus
    property var newConnectionRunner: newConnection
    property bool busy: false
    property string networkName: ""
    property string message: ""
    property string error: ""
    property string activePath: "/"
    property bool cancelRequested: false
    property int requestId: 0
    property int timeoutInterval: 90000
    readonly property string service: "org.freedesktop.NetworkManager"
    readonly property int activeState: Number(activeProperties.properties.State ?? 0)

    function finish(text, failure) {
        busy = false
        deadline.stop()
        message = failure ? "" : text
        error = failure ? text : ""
    }

    function connectNetwork(network) {
        if (busy || network.ConnectionState === PlasmaNM.Enums.Activated) {
            return
        }
        error = ""
        message = ""
        networkName = network.Ssid || network.ItemUniqueName || "Wi-Fi network"
        if (!network.DevicePath || !network.SpecificPath || network.SpecificPath === "/") {
            finish("This network is no longer available. Refresh the list and try again.", true)
            return
        }
        // New enterprise profiles need certificates/identity settings first.
        if (!network.Uuid && [PlasmaNM.Enums.DynamicWep, PlasmaNM.Enums.Leap, PlasmaNM.Enums.WpaEap,
                               PlasmaNM.Enums.Wpa2Eap, PlasmaNM.Enums.Wpa3SuiteB192].includes(network.SecurityType)) {
            finish("Configure this enterprise network in Plasma Network Settings first, then connect here.", true)
            return
        }

        busy = true
        cancelRequested = false
        activePath = "/"
        message = "Connecting to " + networkName + "… Complete any Plasma password or authorization dialog."
        const serial = ++requestId
        const saved = Boolean(network.Uuid && network.ConnectionPath && network.ConnectionPath !== "/")
        deadline.restart()
        try {
            if (!saved) {
                newConnectionRunner.start(network.DevicePath, network.SpecificPath, serial)
                return
            }
            bus.asyncCall({
                service: service,
                path: "/org/freedesktop/NetworkManager",
                iface: service,
                member: "ActivateConnection",
                signature: "(ooo)",
                arguments: [network.ConnectionPath, network.DevicePath, network.SpecificPath]
            }, function(reply) {
                root.activationFinished(serial, String(reply.values[0]), "")
            }, function(failure) {
                root.activationFinished(serial, "/", failure.error.message)
            })
        } catch (failure) {
            finish("Could not start connection: " + failure.message, true)
        }
    }

    function activationFinished(serial, path, failure) {
        if (serial !== requestId) {
            return
        }
        if (failure.length > 0) {
            finish("Could not connect to " + networkName + ": " + failure, true)
            return
        }
        activePath = path
        if (cancelRequested) {
            cancel()
        } else {
            observeState(activeState)
        }
    }

    function observeState(state) {
        if (!busy || activePath === "/" || cancelRequested) {
            return
        }
        if (state === 2) {
            finish("Connected to " + networkName, false)
        } else if (state === 4) {
            finish("Could not connect to " + networkName + ". Authentication may have been cancelled or the network became unavailable. Try again.", true)
        }
    }

    function cancel() {
        if (!busy) {
            return
        }
        cancelRequested = true
        message = "Cancelling connection…"
        if (activePath === "/") {
            return // Cancel once the in-flight activation returns its object path.
        }
        const serial = requestId
        bus.asyncCall({
            service: service,
            path: "/org/freedesktop/NetworkManager",
            iface: service,
            member: "DeactivateConnection",
            signature: "(o)",
            arguments: [activePath]
        }, function() {
            if (serial === root.requestId) {
                root.finish("Connection cancelled", false)
                ++root.requestId
                root.activePath = "/"
            }
        }, function(failure) {
            if (serial === root.requestId) {
                root.cancelRequested = false
                root.error = "Could not cancel connection: " + failure.error.message
                root.message = "Waiting for the connection result…"
                root.observeState(root.activeState)
            }
        })
    }

    onActiveStateChanged: observeState(activeState)

    WiFiNewConnection {
        id: newConnection
        onFinished: function(serial, path, failure) {
            root.activationFinished(serial, path, failure)
        }
    }

    DBus.Properties {
        id: activeProperties
        busType: DBus.BusType.System
        service: root.service
        path: root.activePath
        iface: "org.freedesktop.NetworkManager.Connection.Active"
    }

    Timer {
        id: deadline
        interval: root.timeoutInterval
        onTriggered: {
            // Do not claim the request stopped: NetworkManager may still be working.
            root.error = "The connection is taking longer than expected. Complete any authentication dialog, or cancel and retry."
            root.message = "Waiting for " + root.networkName + "…"
        }
    }
}
