import QtQuick
import org.kde.plasma.networkmanagement as PlasmaNM

// Use KDE's wireless rows and decoded SSID, not the global wired/VPN state.
Item {
    id: root
    visible: false
    property var networkSource: nativeNetworks
    property bool radioEnabled: true
    property bool connected: false
    property bool connecting: false
    property string ssid: ""
    PlasmaNM.NetworkModel { id: nativeNetworks }
    Instantiator {
        id: rows
        model: root.networkSource
        delegate: QtObject {
            required property var model
            readonly property bool wireless: model.Type === PlasmaNM.Enums.Wireless
            readonly property int state: model.ConnectionState
            readonly property string ssid: String(model.Ssid || "")
            onWirelessChanged: Qt.callLater(root.refresh)
            onStateChanged: Qt.callLater(root.refresh)
            onSsidChanged: Qt.callLater(root.refresh)
        }
        onObjectAdded: Qt.callLater(root.refresh)
        onObjectRemoved: Qt.callLater(root.refresh)
    }
    onRadioEnabledChanged: refresh()
    function refresh() {
        let active = ""
        let hasActive = false
        let activating = false
        if (radioEnabled) for (let i=0; i<rows.count; ++i) {
            const row=rows.objectAt(i)
            if (!row || !row.wireless) continue
            if (row.state === PlasmaNM.Enums.Activated) { hasActive=true; active=row.ssid }
            if (row.state === PlasmaNM.Enums.Activating) activating=true
        }
        connected=hasActive
        connecting=activating
        ssid=active
    }
}
