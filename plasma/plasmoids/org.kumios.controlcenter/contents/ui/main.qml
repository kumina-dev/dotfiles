import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls

import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import org.kde.plasma.workspace.dbus as DBus

PlasmoidItem {
    id: root

    readonly property string audioService: "org.kumios.Audio"
    readonly property string audioPath: "/org/kumios/Audio"
    readonly property string audioInterface: "org.kumios.Audio"

    readonly property real volume:
        Number(audioProperties.properties.Volume ?? 0.0)

    readonly property bool muted:
        Boolean(audioProperties.properties.Muted ?? false)

    readonly property string deviceName:
        String(
            audioProperties.properties.DeviceName
            ?? "No audio output"
        )
    
    property bool audioAvailable: false

    readonly property string nmService:
        "org.freedesktop.NetworkManager"

    readonly property string nmPath:
        "/org/freedesktop/NetworkManager"

    readonly property string nmInterface:
        "org.freedesktop.NetworkManager"

    readonly property bool wifiEnabled:
        Boolean(networkManagerProperties.properties.WirelessEnabled ?? false)

    readonly property int networkState:
        Number(networkManagerProperties.properties.State ?? 0)

    readonly property bool networkConnected:
        networkState >= 60

    readonly property string primaryConnectionPath:
        String(
            networkManagerProperties.properties.PrimaryConnection
            ?? "/"
        )

    readonly property bool primaryIsWifi:
        String(
            networkManagerProperties.properties.PrimaryConnectionType
            ?? ""
        ) === "802-11-wireless"

    readonly property string activeAccessPointPath:
        primaryIsWifi
            ? String(
                activeConnectionProperties.properties.SpecificObject
                ?? "/"
            )
            : "/"

    readonly property string connectedSsid:
        decodeSsid(
            accessPointProperties.properties.Ssid
        )

    readonly property string bluetoothService:
        "org.bluez"

    readonly property string bluetoothPath:
        "/org/bluez/hci0"

    readonly property string bluetoothInterface:
        "org.bluez.Adapter1"

    property bool bluetoothAvailable: false

    readonly property bool bluetoothPowered:
        bluetoothAvailable
            && Boolean(
                bluetoothProperties.properties.Powered
                ?? false
            )

    property string connectedBluetoothName: ""

    readonly property string bluetoothTitle:
        connectedBluetoothName.length > 0
            ? connectedBluetoothName
            : "Bluetooth"

    readonly property string bluetoothSubtitle:
        !bluetoothAvailable
            ? "Unavailable"
            : !bluetoothPowered
                ? "Off"
                : connectedBluetoothName.length > 0
                    ? "Connected"
                    : "On"

    property DBus.dbusMessage bluetoothObjectsMessage: ({
        service: root.bluetoothService,
        path: "/",
        iface: "org.freedesktop.DBus.ObjectManager",
        member: "GetManagedObjects",
        arguments: []
    })

    property DBus.dbusMessage brightnessSetMessage: ({
        service: root.brightnessService,
        path: root.brightnessDisplayPath,
        iface: root.brightnessDisplayInterface,
        member: "SetBrightness",
        signature: "(iu)",
        arguments: [
            new DBus.int32(0),
            new DBus.uint32(1)
        ]
    })

    readonly property string brightnessService:
        "org.kde.ScreenBrightness"

    readonly property string brightnessRootPath:
        "/org/kde/ScreenBrightness"

    readonly property string brightnessRootInterface:
        "org.kde.ScreenBrightness"

    readonly property string brightnessDisplayInterface:
        "org.kde.ScreenBrightness.Display"

    readonly property string brightnessDisplayName:
        String(
            brightnessRootProperties.properties.DisplaysDBusNames?.[0]
            ?? ""
        )

    readonly property string brightnessDisplayPath:
        brightnessDisplayName.length > 0
            ? root.brightnessRootPath + "/" + brightnessDisplayName
            : "/"

    readonly property int brightnessValue:
        Number(
            brightnessDisplayProperties.properties.Brightness
            ?? 0
        )

    readonly property int brightnessMax:
        Number(
            brightnessDisplayProperties.properties.MaxBrightness
            ?? 0
        )

    readonly property bool brightnessAvailable:
        brightnessDisplayName.length > 0
            && brightnessMax > 0

    readonly property int brightnessPercent:
        brightnessAvailable
            ? Math.round(
                (brightnessValue / brightnessMax) * 100
            )
            : 0

    readonly property string displayLabel:
        String(
            brightnessDisplayProperties.properties.Label
            ?? "Display"
        )

    preferredRepresentation: compactRepresentation

    function volumeIcon() {
        if (!audioAvailable) {
            return "audio-volume-muted"
        }

        if (muted || volume <= 0.001) {
            return "audio-volume-muted"
        }

        if (volume < 0.33) {
            return "audio-volume-low"
        }

        if (volume < 0.66) {
            return "audio-volume-medium"
        }

        return "audio-volume-high"
    }

    function volumePercent() {
        return Math.round(volume * 100)
    }

    function setVolume(value) {
        const clamped = Math.max(
            0.0,
            Math.min(1.0, value)
        )

        const reply = DBus.SessionBus.asyncCall({
            service: root.audioService,
            path: root.audioPath,
            iface: root.audioInterface,
            member: "SetVolume",
            signature: "d",
            arguments: [
                clamped
            ]
        })

        reply.finished.connect(function() {
            if (reply.isError) {
                console.warn(
                    "KumiOS Control Center: SetVolume failed:",
                    reply.error.message
                )
            }

            reply.destroy()
        })
    }

    function toggleMuted() {
        const reply = DBus.SessionBus.asyncCall({
            service: root.audioService,
            path: root.audioPath,
            iface: root.audioInterface,
            member: "ToggleMuted",
            arguments: []
        })

        reply.finished.connect(function() {
            if (reply.isError) {
                console.warn(
                    "KumiOS Control Center: ToggleMuted failed:",
                    reply.error.message
                )
            }

            reply.destroy()
        })
    }

    function wifiSubtitle() {
        if (!wifiEnabled) {
            return "Off"
        }

        if (networkState === 40) {
            return "Connecting..."
        }

        if (primaryIsWifi && networkState >= 60) {
            return "Connected"
        }

        return "Not Connected"
    }

    function wifiIcon() {
        if (!wifiEnabled) {
            return "network-wireless-off"
        }

        if (networkConnected) {
            return "network-wireless"
        }

        return "network-wireless-disconnected"
    }

    function toggleWifi() {
        networkManagerProperties.properties.WirelessEnabled =
            !root.wifiEnabled
    }

    function decodeSsid(value) {
        if (!value || value.length === 0) {
            return ""
        }

        try {
            const bytes = []

            for (let i = 0; i < value.length; ++i) {
                const item = value[i]

                if (typeof item === "number") {
                    bytes.push(item)
                } else if (item && item.value !== undefined) {
                    bytes.push(Number(item.value))
                } else {
                    return ""
                }
            }

            let result = ""

            for (let i = 0; i < bytes.length; ++i) {
                result += String.fromCharCode(bytes[i])
            }

            return result
        } catch (error) {
            console.warn(
                "KumiOS Control Center: failed to decode SSID:",
                error
            )

            return ""
        }
    }

    function toggleBluetooth() {
        if (!root.bluetoothAvailable) {
            return
        }

        bluetoothProperties.properties.Powered =
            !root.bluetoothPowered
    }

    function refreshBluetoothDevices() {
        if (!root.bluetoothAvailable) {
            root.connectedBluetoothName = ""
            return
        }

        const reply = DBus.SystemBus.asyncCall(
            root.bluetoothObjectsMessage
        )

        reply.finished.connect(function() {
            if (reply.isError) {
                console.warn(
                    "KumiOS Control Center: failed to read Bluetooth devices:",
                    reply.error.message
                )

                root.connectedBluetoothName = ""
                reply.destroy()
                return
            }

            const objects = reply.value
            let connectedName = ""

            for (const objectPath in objects) {
                const interfaces = objects[objectPath]

                if (!interfaces) {
                    continue
                }

                const device = interfaces["org.bluez.Device1"]

                if (!device) {
                    continue
                }

                const connectedValue = device.Connected

                const connected =
                    connectedValue
                    && connectedValue.value !== undefined
                        ? Boolean(connectedValue.value)
                        : Boolean(connectedValue)

                if (!connected) {
                    continue
                }

                const aliasValue = device.Alias

                if (
                    aliasValue
                    && aliasValue.value !== undefined
                ) {
                    connectedName = String(aliasValue.value)
                } else if (aliasValue !== undefined) {
                    connectedName = String(aliasValue)
                }

                if (connectedName.length > 0) {
                    break
                }
            }

            root.connectedBluetoothName = connectedName

            reply.destroy()
        })
    }

    function setBrightness(ratio) {
        if (!root.brightnessAvailable) {
            return
        }

        const clamped = Math.max(
            0.0,
            Math.min(1.0, ratio)
        )

        const target = Math.round(
            clamped * root.brightnessMax
        )

        root.brightnessSetMessage.path =
            root.brightnessDisplayPath

        root.brightnessSetMessage.arguments = [
            new DBus.int32(target),
            new DBus.uint32(1)
        ]

        const reply = DBus.SessionBus.asyncCall(
            root.brightnessSetMessage
        )

        reply.finished.connect(function() {
            if (reply.isError) {
                console.warn(
                    "KumiOS Control Center: brightness change failed:",
                    reply.error.message
                )
            }

            reply.destroy()
        })
    }

    DBus.DBusServiceWatcher {
        id: audioServiceWatcher

        busType: DBus.BusType.Session
        watchedService: root.audioService

        onRegisteredChanged: {
            root.audioAvailable = registered

            if (registered) {
                audioProperties.updateAll()
            }
        }
    }

    DBus.Properties {
        id: audioProperties

        busType: DBus.BusType.Session
        service: root.audioService
        path: root.audioPath
        iface: root.audioInterface

        onRefreshed: {
            root.audioAvailable = true
        }

        onPropertiesChanged: function(
            interfaceName,
            changedProperties,
            invalidatedProperties
        ) {
            if (interfaceName === root.audioInterface) {
                root.audioAvailable = true
            }
        }
    }

    DBus.Properties {
        id: networkManagerProperties

        busType: DBus.BusType.System
        service: root.nmService
        path: root.nmPath
        iface: root.nmInterface
    }

    DBus.Properties {
        id: activeConnectionProperties

        busType: DBus.BusType.System
        service: root.nmService

        path: root.primaryIsWifi
            ? root.primaryConnectionPath
            : "/"

        iface:
            "org.freedesktop.NetworkManager.Connection.Active"
    }

    DBus.Properties {
        id: accessPointProperties

        busType: DBus.BusType.System
        service: root.nmService

        path: root.activeAccessPointPath

        iface:
            "org.freedesktop.NetworkManager.AccessPoint"
    }

    DBus.DBusServiceWatcher {
        id: bluetoothServiceWatcher

        busType: DBus.BusType.System
        watchedService: root.bluetoothService

        onRegisteredChanged: {
            root.bluetoothAvailable = registered

            if (registered) {
                bluetoothProperties.updateAll()
                root.refreshBluetoothDevices()
            } else {
                root.connectedBluetoothName = ""
            }
        }
    }

    DBus.Properties {
        id: bluetoothProperties

        busType: DBus.BusType.System
        service: root.bluetoothService
        path: root.bluetoothPath
        iface: root.bluetoothInterface

        onRefreshed: {
            root.bluetoothAvailable = true
            root.refreshBluetoothDevices()
        }

        onPropertiesChanged: function(
            interfaceName,
            changedProperties,
            invalidatedProperties
        ) {
            if (interfaceName === root.bluetoothInterface) {
                root.bluetoothAvailable = true
                root.refreshBluetoothDevices()
            }
        }
    }

    DBus.SignalWatcher {
        busType: DBus.BusType.System
        service: root.bluetoothService
        path: "/"
        iface: "org.freedesktop.DBus.ObjectManager"

        function dbusInterfacesAdded(
            objectPath,
            interfaces
        ) {
            root.refreshBluetoothDevices()
        }

        function dbusInterfacesRemoved(
            objectPath,
            interfaces
        ) {
            root.refreshBluetoothDevices()
        }
    }

    Timer {
        interval: 2000
        repeat: true
        running: root.bluetoothAvailable
            && root.bluetoothPowered

        onTriggered: {
            root.refreshBluetoothDevices()
        }
    }

    DBus.Properties {
        id: brightnessRootProperties

        busType: DBus.BusType.Session
        service: root.brightnessService
        path: root.brightnessRootPath
        iface: root.brightnessRootInterface
    }

    DBus.Properties {
        id: brightnessDisplayProperties

        busType: DBus.BusType.Session
        service: root.brightnessService

        path: root.brightnessDisplayName.length > 0
            ? root.brightnessDisplayPath
            : "/"

        iface: root.brightnessDisplayInterface
    }

    compactRepresentation: Controls.ToolButton {
        implicitWidth: 36
        implicitHeight: 30

        onClicked: root.expanded = !root.expanded

        contentItem: RowLayout {
            spacing: 4

            Kirigami.Icon {
                source: root.wifiIcon()

                implicitWidth: 15
                implicitHeight: 15
            }

            Kirigami.Icon {
                source: root.volumeIcon()

                implicitWidth: 15
                implicitHeight: 15
            }
        }
    }

    fullRepresentation: Item {
        Layout.preferredWidth: 320
        Layout.minimumWidth: 320
        Layout.maximumWidth: 320

        Layout.preferredHeight: 440
        Layout.minimumHeight: 440

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing

            spacing: Kirigami.Units.mediumSpacing

            Controls.Label {
                text: "Control Center"

                font.pixelSize: 18
                font.weight: Font.DemiBold
            }

            GridLayout {
                Layout.fillWidth: true

                columns: 2

                columnSpacing: Kirigami.Units.mediumSpacing
                rowSpacing: Kirigami.Units.mediumSpacing

                QuickTile {
                    title: root.connectedSsid.length > 0
                        ? root.connectedSsid
                        : "Wi-Fi"
                    subtitle: root.wifiSubtitle()
                    iconName: root.wifiIcon()

                    onClicked: root.toggleWifi()
                }

                QuickTile {
                    title: root.bluetoothTitle
                    subtitle: root.bluetoothSubtitle
                    iconName: "bluetooth"

                    enabled: root.bluetoothAvailable

                    onClicked: root.toggleBluetooth()
                }

                QuickTile {
                    title: "Sound"

                    subtitle: root.audioAvailable
                        ? (
                            root.muted
                                ? "Muted"
                                : root.volumePercent() + "%"
                        )
                        : "Unavailable"

                    iconName: root.volumeIcon()

                    onClicked: root.toggleMuted()
                }

                QuickTile {
                    title: "Display"

                    subtitle: root.brightnessAvailable
                        ? root.brightnessPercent + "%"
                        : "Unavailable"

                    iconName: "video-display"

                    enabled: root.brightnessAvailable
                }
            }

            ColumnLayout {
                Layout.fillWidth: true

                spacing: Kirigami.Units.smallSpacing

                RowLayout {
                    Layout.fillWidth: true

                    Controls.Label {
                        text: "Sound"
                        font.weight: Font.DemiBold
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    Controls.Label {
                        text: root.audioAvailable
                            ? root.volumePercent() + "%"
                            : "Unavailable"

                        opacity: 0.65
                    }
                }

                RowLayout {
                    Layout.fillWidth: true

                    spacing: Kirigami.Units.mediumSpacing

                    Controls.ToolButton {
                        enabled: root.audioAvailable

                        onClicked: root.toggleMuted()

                        contentItem: Kirigami.Icon {
                            source: root.volumeIcon()

                            implicitWidth: 20
                            implicitHeight: 20
                        }
                    }

                    Controls.Slider {
                        id: volumeSlider

                        Layout.fillWidth: true

                        enabled: root.audioAvailable

                        from: 0.0
                        to: 1.0
                        stepSize: 0.01

                        value: root.volume

                        onMoved: {
                            root.setVolume(value)
                        }
                    }
                }

                Controls.Label {
                    Layout.fillWidth: true

                    text: root.deviceName

                    opacity: 0.6
                    font.pixelSize: 11

                    elide: Text.ElideRight
                }
            }

            ColumnLayout {
                Layout.fillWidth: true

                spacing: Kirigami.Units.smallSpacing

                RowLayout {
                    Layout.fillWidth: true

                    Controls.Label {
                        text: "Display"
                        font.weight: Font.DemiBold
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    Controls.Label {
                        text: root.brightnessAvailable
                            ? root.brightnessPercent + "%"
                            : "Unavailable"

                        opacity: 0.65
                    }
                }

                RowLayout {
                    Layout.fillWidth: true

                    spacing: Kirigami.Units.mediumSpacing

                    Kirigami.Icon {
                        source: "brightness-low"

                        implicitWidth: 20
                        implicitHeight: 20
                    }

                    Controls.Slider {
                        Layout.fillWidth: true

                        enabled: root.brightnessAvailable

                        from: 0.0
                        to: 1.0
                        stepSize: 0.01

                        value: root.brightnessAvailable
                            ? root.brightnessValue
                                / root.brightnessMax
                            : 0.0

                        onMoved: {
                            root.setBrightness(value)
                        }
                    }

                    Kirigami.Icon {
                        source: "brightness-high"

                        implicitWidth: 20
                        implicitHeight: 20
                    }
                }

                Controls.Label {
                    Layout.fillWidth: true

                    text: root.displayLabel

                    opacity: 0.6
                    font.pixelSize: 11

                    elide: Text.ElideRight
                }
            }

            Item {
                Layout.fillHeight: true
            }
        }
    }

    component QuickTile: Controls.AbstractButton {
        required property string title
        required property string subtitle
        required property string iconName

        Layout.fillWidth: true

        implicitHeight: 72

        contentItem: RowLayout {
            spacing: Kirigami.Units.mediumSpacing

            Kirigami.Icon {
                source: iconName

                implicitWidth: 26
                implicitHeight: 26
            }

            ColumnLayout {
                spacing: 1

                Controls.Label {
                    text: title
                    font.weight: Font.DemiBold
                }

                Controls.Label {
                    text: subtitle

                    opacity: 0.65
                    font.pixelSize: 11
                }
            }
        }
    }
}