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
    property string operation: "connect"
    property string devicePath: "/"
    property bool disconnectAccepted: false
    property string networkName: ""
    property string message: ""
    property string error: ""
    property string failureDetail: ""
    property string activePath: "/"
    property bool cancelRequested: false
    property bool cancelAccepted: false
    property bool cancelInFlight: false
    property int requestId: 0
    property int timeoutInterval: 90000
    readonly property string service: "org.freedesktop.NetworkManager"
    readonly property int deviceState: Number(deviceProperties.properties.State ?? 0)
    readonly property int activeState: Number(activeProperties.properties.State ?? 0)

    function finish(text, failure) {
        busy = false
        cancelInFlight = false
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

        operation = "connect"
        devicePath = network.DevicePath
        failureDetail = ""
        busy = true
        cancelRequested = false
        cancelAccepted = false
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

    function disconnectNetwork(network) {
        if (busy || network.ConnectionState !== PlasmaNM.Enums.Activated) {
            return
        }
        operation = "disconnect"
        networkName = network.Ssid || network.ItemUniqueName || "Wi-Fi network"
        error = ""
        if (!network.DevicePath || network.DevicePath === "/") {
            finish("This Wi-Fi adapter is no longer available.", true)
            return
        }
        disconnectAccepted = false
        devicePath = network.DevicePath
        activePath = "/"
        busy = true
        cancelRequested = false
        message = "Disconnecting from " + networkName + "…"
        const serial = ++requestId
        deadline.restart()
        try {
            bus.asyncCall({
                service: service,
                path: devicePath,
                iface: "org.freedesktop.NetworkManager.Device",
                member: "Disconnect",
                arguments: []
            }, function() {
                if (serial === root.requestId) {
                    root.disconnectAccepted = true
                    root.observeDeviceState(root.deviceState)
                }
            }, function(failure) {
                if (serial === root.requestId) {
                    root.finish("Could not disconnect from " + root.networkName + ": " + failure.error.message, true)
                }
            })
        } catch (failure) {
            finish("Could not start disconnection: " + failure.message, true)
        }
    }

    function observeDeviceState(state) {
        if (!busy || operation !== "disconnect" || !disconnectAccepted) {
            return
        }
        // NetworkManager device states: unavailable, disconnected, failed.
        if (state === 20 || state === 30) {
            finish("Disconnected from " + networkName, false)
        } else if (state === 120) {
            finish("The Wi-Fi adapter reported an error while disconnecting. Check its current state and retry.", true)
        }
    }

    function observeState(state) {
        if (!busy || operation !== "connect" || activePath === "/") {
            return
        }
        if (cancelRequested) {
            if (cancelAccepted && state === 4) {
                finish("Connection cancelled", false)
                ++requestId
                activePath = "/"
            }
            return
        }
        if (state === 2) {
            finish("Connected to " + networkName, false)
        } else if (state === 4) {
            // Device.StateChanged carries the useful reason, often in the same
            // event batch as the active connection's terminal state.
            const serial = requestId
            Qt.callLater(function() {
                if (root.busy && serial === root.requestId && !root.cancelRequested) {
                    root.finish("Could not connect to " + root.networkName + ". "
                        + (root.failureDetail || "The connection ended before it was ready. Try again."), true)
                }
            })
        }
    }

    function recordDeviceReason(state, reason) {
        if (!busy || operation !== "connect" || (state !== 120 && reason !== 7)) {
            return
        }
        switch (reason) {
        case 7:
            failureDetail = "Authentication was cancelled or no password was provided."
            break
        case 8: case 9: case 10:
            failureDetail = "Wi-Fi authentication failed. Check the password and network security settings."
            break
        case 11:
            failureDetail = "Wi-Fi authentication timed out. Check the password and signal, then retry."
            break
        case 53:
            failureDetail = "The access point could not be reached. Refresh the network list and retry."
            break
        case 5: case 6: case 15: case 16: case 17:
            failureDetail = "An IP address could not be obtained. Check the network's address settings and retry."
            break
        default:
            if (reason > 1) failureDetail = "NetworkManager reported a device error (reason " + reason + ")."
        }
    }

    function cancel() {
        if (!busy || operation !== "connect" || cancelInFlight) {
            return
        }
        cancelRequested = true
        message = "Cancelling connection…"
        if (activePath === "/") {
            return // Cancel once the in-flight activation returns its object path.
        }
        const serial = requestId
        cancelInFlight = true
        try {
            bus.asyncCall({
                service: service,
                path: "/org/freedesktop/NetworkManager",
                iface: service,
                member: "DeactivateConnection",
                signature: "(o)",
                arguments: [activePath]
            }, function() {
                if (serial === root.requestId) {
                    root.cancelAccepted = true
                    root.observeState(root.activeState)
                }
            }, function(failure) {
                if (serial === root.requestId) {
                    root.cancelInFlight = false
                    root.cancelRequested = false
                    root.error = "Could not cancel connection: " + failure.error.message
                    root.message = "Waiting for the connection result…"
                    root.observeState(root.activeState)
                }
            })
        } catch (failure) {
            cancelInFlight = false
            cancelRequested = false
            error = "Could not cancel connection: " + failure.message
        }
    }

    onActiveStateChanged: observeState(activeState)
    onDeviceStateChanged: observeDeviceState(deviceState)

    DBus.SignalWatcher {
        enabled: root.busy && root.operation === "connect"
        busType: DBus.BusType.System
        service: root.service
        path: root.devicePath
        iface: "org.freedesktop.NetworkManager.Device"
        function dbusStateChanged(state, oldState, reason) {
            root.recordDeviceReason(Number(state), Number(reason))
        }
    }

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

    DBus.Properties {
        id: deviceProperties
        busType: DBus.BusType.System
        service: root.service
        path: root.devicePath
        iface: "org.freedesktop.NetworkManager.Device"
    }

    Timer {
        id: deadline
        interval: root.timeoutInterval
        onTriggered: {
            if (root.operation === "disconnect") {
                root.finish("Disconnect did not complete in time. Check the current network state and retry.", true)
                ++root.requestId
                return
            }
            // Do not claim the request stopped: NetworkManager may still be working.
            root.error = "The connection is taking longer than expected. Complete any authentication dialog, or cancel and retry."
            root.message = "Waiting for " + root.networkName + "…"
        }
    }
}
