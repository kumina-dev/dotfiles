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
        const reply = DBus.SystemBus.asyncCall({
            service: root.nmService,
            path: root.nmPath,
            iface: "org.freedesktop.DBus.Properties",
            member: "Set",
            signature: "ssv",
            arguments: [
                root.nmInterface,
                "WirelessEnabled",
                !root.wifiEnabled
            ]
        })

        reply.finished.connect(function() {
            if (reply.isError) {
                console.warn(
                    "KumiOS Control Center: Wi-Fi toggle failed:",
                    reply.error.message
                )
            }

            reply.destroy()
        })
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

        Layout.preferredHeight: 360
        Layout.minimumHeight: 360

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
                    title: "Bluetooth"
                    subtitle: "On"
                    iconName: "bluetooth"
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
                    subtitle: "Brightness"
                    iconName: "video-display"
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