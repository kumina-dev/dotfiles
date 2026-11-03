import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls

import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.workspace.dbus as DBus

PlasmoidItem {
    id: root

    NativeAudio { id: audio }
    readonly property real volume: audio.output.volume
    readonly property bool muted: audio.output.muted
    readonly property string deviceName: audio.output.deviceName
    readonly property bool audioAvailable: audio.output.available

    readonly property string nmService:
        "org.freedesktop.NetworkManager"

    readonly property string nmPath:
        "/org/freedesktop/NetworkManager"

    readonly property string nmInterface:
        "org.freedesktop.NetworkManager"

    readonly property bool wifiEnabled:
        Boolean(networkManagerProperties.properties.WirelessEnabled ?? false)

    WiFiStatus { id: wifiStatus; radioEnabled: root.wifiEnabled }
    readonly property bool networkConnected: wifiStatus.connected
    readonly property string connectedSsid: wifiStatus.ssid

    BluetoothControl { id: bluetooth }
    readonly property bool bluetoothAvailable: bluetooth.available
    readonly property string bluetoothTitle: bluetooth.connectedName || "Bluetooth"
    readonly property string bluetoothSubtitle: bluetooth.subtitle

    property string currentPage: "home"

    function openPage(page) {
        currentPage = page
    }

    function goHome() {
        currentPage = "home"
    }

    onExpandedChanged: {
        if (!root.expanded) {
            goHome()
        }
    }

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

    function setVolume(value) { audio.output.setVolume(value) }
    function toggleMuted() { audio.output.toggleMuted() }

    function wifiSubtitle() {
        if (!nmWatcher.registered) return "Unavailable"
        if (wifiChange.busy) return "Applying…"
        if (!wifiEnabled) {
            return "Off"
        }

        if (wifiStatus.connecting) {
            return "Connecting..."
        }

        if (wifiStatus.connected) {
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

    BackendChange {
        id: wifiChange
        label: "Wi-Fi"
        available: nmWatcher.registered
        identity: root.nmPath
        observed: root.wifiEnabled
        makeMessage: function(value) {
            return {service:root.nmService, path:root.nmPath,
                iface:"org.freedesktop.DBus.Properties", member:"Set", signature:"(ssv)",
                arguments:[root.nmInterface, "WirelessEnabled", new DBus.variant(value)]}
        }
    }
    BackendChange {
        id: brightnessChange
        bus: DBus.SessionBus
        label: "Brightness"
        available: brightnessWatcher.registered && root.brightnessAvailable
        identity: root.brightnessDisplayPath
        observed: root.brightnessValue
        makeMessage: function(value) {
            return {service:root.brightnessService, path:root.brightnessDisplayPath,
                iface:root.brightnessDisplayInterface, member:"SetBrightness", signature:"(iu)",
                arguments:[new DBus.int32(value), new DBus.uint32(1)]}
        }
    }
    function toggleWifi() { wifiChange.set(!root.wifiEnabled) }
    function toggleBluetooth() { bluetooth.toggle() }
    function setBrightness(ratio) {
        if (!Number.isFinite(ratio)) return
        brightnessChange.set(Math.round(Math.max(0, Math.min(1, ratio)) * root.brightnessMax))
    }
    DBus.DBusServiceWatcher {
        id: nmWatcher
        busType: DBus.BusType.System
        watchedService: root.nmService
        onRegisteredChanged: if (registered) networkManagerProperties.updateAll()
    }
    DBus.DBusServiceWatcher {
        id: brightnessWatcher
        busType: DBus.BusType.Session
        watchedService: root.brightnessService
        onRegisteredChanged: if (registered) brightnessRootProperties.updateAll()
    }

    DBus.Properties {
        id: networkManagerProperties

        busType: DBus.BusType.System
        service: root.nmService
        path: root.nmPath
        iface: root.nmInterface
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
        id: popup

        readonly property int popupPadding:
            Kirigami.Units.largeSpacing
        
        Layout.minimumWidth: 320
        Layout.preferredWidth: 320

        Layout.minimumHeight:
            content.implicitHeight + popupPadding * 2

        Layout.preferredHeight:
            content.implicitHeight + popupPadding * 2

        ColumnLayout {
            id: content
            
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: popup.popupPadding
            }

            spacing: Kirigami.Units.mediumSpacing

            RowLayout {
                Layout.fillWidth: true

                Controls.ToolButton {
                    visible: root.currentPage !== "home"

                    icon.name: "go-previous"

                    onClicked: root.goHome()
                }

                Controls.Label {
                    Layout.fillWidth: true

                    text: root.currentPage === "wifi"
                        ? "Wi-Fi"
                        : "Control Center"

                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }
            }

            GridLayout {
                Layout.fillWidth: true

                columns: 2

                columnSpacing: Kirigami.Units.mediumSpacing
                rowSpacing: Kirigami.Units.mediumSpacing

                visible: root.currentPage === "home"

                QuickTile {
                    title: root.connectedSsid.length > 0
                        ? root.connectedSsid
                        : "Wi-Fi"

                    subtitle: root.wifiSubtitle()
                    iconName: root.wifiIcon()

                    onClicked: root.toggleWifi()

                    onDetailsRequested: root.openPage("wifi")
                }

                QuickTile {
                    title: root.bluetoothTitle
                    subtitle: root.bluetoothSubtitle
                    iconName: "bluetooth"

                    onClicked: root.toggleBluetooth()
                    onDetailsRequested: {
                        root.expanded = false
                        KCM.KCMLauncher.open("kcm_bluetooth")
                    }
                }
            }

            Controls.Label {
                Layout.fillWidth: true
                visible: root.currentPage === "home" && text.length > 0
                text: [wifiChange.error, bluetooth.error].filter(Boolean).join("\n")
                    Controls.ToolTip.visible: radioErrorHover.hovered
                    Controls.ToolTip.text: text
                    HoverHandler { id: radioErrorHover }
                wrapMode: Text.Wrap
                maximumLineCount: 3
                elide: Text.ElideRight
                color: Kirigami.Theme.negativeTextColor
            }

            ColumnLayout {
                Layout.fillWidth: true

                spacing: Kirigami.Units.smallSpacing

                visible: root.currentPage === "home"

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
                        enabled: root.audioAvailable && !audio.output.busy
                        Accessible.name: root.muted ? "Unmute output" : "Mute output"
                        Controls.ToolTip.visible: hovered
                        Controls.ToolTip.text: Accessible.name

                        onClicked: root.toggleMuted()

                        contentItem: Kirigami.Icon {
                            source: root.volumeIcon()

                            implicitWidth: 20
                            implicitHeight: 20
                        }
                    }

                    Controls.Slider {
                        id: volumeSlider
                        Accessible.name: "Output volume"

                        Layout.fillWidth: true

                        enabled: audio.output.volumeWritable && !audio.output.busy

                        from: 0.0
                        to: 1.0
                        stepSize: 0.01

                        Binding on value {
                            value: root.volume
                            when: !volumeSlider.pressed && !audio.output.busy
                            restoreMode: Binding.RestoreNone
                        }

                        // Commit on release so a drag does not queue competing writes.
                        onPressedChanged: if (!pressed) root.setVolume(value)
                        onMoved: if (!pressed) root.setVolume(value)
                    }
                }

                Controls.Label {
                    Layout.fillWidth: true

                    text: root.deviceName
                    Controls.ToolTip.visible: outputDeviceHover.hovered
                    Controls.ToolTip.text: text
                    HoverHandler { id: outputDeviceHover }

                    opacity: 0.6
                    font.pixelSize: 11

                    elide: Text.ElideRight
                }

                RowLayout {
                    Layout.fillWidth: true
                    Controls.ToolButton {
                        objectName: "microphoneMute"
                        enabled: audio.input.available && !audio.input.busy
                        icon.name: audio.input.muted ? "microphone-sensitivity-muted" : "microphone-sensitivity-high"
                        text: audio.input.muted ? "Unmute mic" : "Mute mic"
                        Accessible.name: text
                        onClicked: audio.input.toggleMuted()
                    }
                    Controls.Label {
                        Layout.fillWidth: true
                        text: audio.input.deviceName
                        elide: Text.ElideRight
                        Controls.ToolTip.visible: hovered
                        Controls.ToolTip.text: text
                        property bool hovered: micHover.hovered
                        HoverHandler { id: micHover }
                    }
                }
                Controls.Label {
                    Layout.fillWidth: true
                    visible: audio.output.busy || audio.input.busy
                    text: "Applying audio change…"
                }
                Controls.Label {
                    Layout.fillWidth: true
                    visible: text.length > 0
                    text: [audio.output.error, audio.input.error].filter(Boolean).join("\n")
                    Controls.ToolTip.visible: audioErrorHover.hovered
                    Controls.ToolTip.text: text
                    HoverHandler { id: audioErrorHover }
                    wrapMode: Text.Wrap
                    maximumLineCount: 3
                    elide: Text.ElideRight
                    color: Kirigami.Theme.negativeTextColor
                }

                Controls.Button {
                    visible: !audio.ready
                    text: audio.retrying ? "Reconnecting audio…" : "Retry audio"
                    enabled: !audio.retrying
                    onClicked: audio.retry()
                }
                Controls.Button {
                    Layout.fillWidth: true
                    text: "Devices & Microphone…"
                    icon.name: "configure"
                    onClicked: {
                        root.expanded = false
                        KCM.KCMLauncher.open("kcm_pulseaudio")
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true

                spacing: Kirigami.Units.smallSpacing

                visible: root.currentPage === "home"

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
                        id: brightnessSlider
                        Accessible.name: "Display brightness"
                        Layout.fillWidth: true

                        enabled: brightnessChange.available && !brightnessChange.busy

                        from: 0.0
                        to: 1.0
                        stepSize: 0.01

                        Binding on value {
                            value: root.brightnessAvailable ? root.brightnessValue / root.brightnessMax : 0
                            when: !brightnessSlider.pressed && !brightnessChange.busy
                            restoreMode: Binding.RestoreNone
                        }

                        onPressedChanged: if (!pressed) root.setBrightness(value)
                        onMoved: if (!pressed) root.setBrightness(value)
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
                Controls.Label {
                    Layout.fillWidth: true
                    visible: brightnessChange.busy || brightnessChange.error.length > 0
                    text: brightnessChange.busy ? "Applying brightness…" : brightnessChange.error
                    Controls.ToolTip.visible: brightnessErrorHover.hovered
                    Controls.ToolTip.text: text
                    HoverHandler { id: brightnessErrorHover }
                    wrapMode: Text.Wrap
                    maximumLineCount: 3
                    elide: Text.ElideRight
                    color: Kirigami.Theme.negativeTextColor
                }
                Controls.ToolButton {
                    text: "Display settings…"
                    icon.name: "configure"
                    onClicked: { root.expanded = false; KCM.KCMLauncher.open("kcm_kscreen") }
                }

            }

            WiFiDetails {
                Layout.fillWidth: true

                visible: root.currentPage === "wifi"

                wifiEnabled: root.wifiEnabled
                connected: root.networkConnected
                ssid: root.connectedSsid
            }
        }
    }

    component QuickTile: Controls.AbstractButton {
        required property string title
        required property string subtitle
        required property string iconName

        signal detailsRequested()
        Accessible.name: title + ": " + subtitle

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
                Layout.fillWidth: true
                spacing: 1

                Controls.Label {
                    text: title
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                Controls.Label {
                    text: subtitle
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    Controls.ToolTip.visible: subtitleHover.hovered
                    Controls.ToolTip.text: text
                    HoverHandler { id: subtitleHover }
                    opacity: 0.65
                    font.pixelSize: 11
                }
            }

            Controls.ToolButton {
                visible: title.length > 0
                Accessible.name: "Open " + title + " details"
                Controls.ToolTip.visible: hovered
                Controls.ToolTip.text: Accessible.name
                icon.name: "go-next"

                onClicked: detailsRequested()
            }
        }
    }
}
