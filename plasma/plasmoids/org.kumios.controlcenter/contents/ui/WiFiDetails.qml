import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kitemmodels as KItemModels

import org.kde.kirigami as Kirigami
import org.kde.plasma.networkmanagement as PlasmaNM

ColumnLayout {
    id: root

    required property bool wifiEnabled
    required property bool connected
    required property string ssid

    // Injectable model/bus keep connection regression tests off the real network.
    property var networkSource: networkModel
    property var discoveryHandler: networkHandler
    property alias connection: connection
    readonly property int networkCount: networkProxy.count

    spacing: Kirigami.Units.mediumSpacing

    WiFiConnection { id: connection }
    PlasmaNM.Handler { id: networkHandler }

    function refreshNetworks() {
        if (visible && wifiEnabled) {
            discoveryHandler.requestScan()
        }
    }

    Component.onCompleted: refreshNetworks()
    onVisibleChanged: refreshNetworks()

    onWifiEnabledChanged: {
        refreshNetworks()
        if (!wifiEnabled) {
            if (connection.busy) {
                connection.cancel()
            } else {
                connection.message = ""
                connection.error = ""
            }
        }
    }

    PlasmaNM.NetworkModel {
        id: networkModel
    }

    // Filter before layout so wired/VPN entries do not occupy list rows.
    KItemModels.KSortFilterProxyModel {
        id: networkProxy
        objectName: "wifiNetworkModel"
        sourceModel: root.networkSource
        filterRoleName: "Type"
        filterRowCallback: function(row, parent) {
            return sourceModel.data(sourceModel.index(row, 0, parent),
                                    filterRole) === PlasmaNM.Enums.Wireless
        }
        sortRoleName: "Signal"
        sortOrder: Qt.DescendingOrder
    }

    Controls.Label {
        Layout.fillWidth: true

        text: root.wifiEnabled
            ? "Wi-Fi is enabled"
            : "Wi-Fi is disabled"

        opacity: 0.7
    }

    Controls.Label {
        Layout.fillWidth: true

        visible: root.wifiEnabled

        text: "Current connection"

        font.weight: Font.DemiBold
    }

    RowLayout {
        Layout.fillWidth: true

        visible: root.wifiEnabled

        Kirigami.Icon {
            source: root.connected
                ? "network-wireless"
                : "network-wireless-disconnected"

            implicitWidth: 24
            implicitHeight: 24
        }

        ColumnLayout {
            Layout.fillWidth: true

            Controls.Label {
                Layout.fillWidth: true

                textFormat: Text.PlainText
                text: root.connected
                    ? (root.ssid || "Connected network")
                    : "Not connected"

                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }

            Controls.Label {
                text: root.connected
                    ? "Connected"
                    : "No active Wi-Fi connection"

                opacity: 0.65
                font.pixelSize: 11
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        visible: root.wifiEnabled

        Controls.Label {
            Layout.fillWidth: true
            text: "Available networks"
            font.weight: Font.DemiBold
        }

        Controls.ToolButton {
            text: "Refresh networks"
            icon.name: "view-refresh"
            display: Controls.AbstractButton.IconOnly
            enabled: !root.discoveryHandler.scanning && !root.connection.busy
            onClicked: root.refreshNetworks()
            Controls.ToolTip.visible: hovered
            Controls.ToolTip.text: text
        }
    }

    ListView {
        id: networkList

        Layout.fillWidth: true
        Layout.preferredHeight: Math.min(contentHeight, 220)

        visible: root.wifiEnabled
        clip: true
        spacing: 0

        model: networkProxy

        Controls.ScrollBar.vertical: Controls.ScrollBar {}

        delegate: Controls.ItemDelegate {
            id: networkItem

            required property var model

            readonly property bool isConnected:
                model.ConnectionState ===
                    PlasmaNM.Enums.Activated

            width: ListView.view.width
            height: 52
            readonly property bool isActivating:
                model.ConnectionState === PlasmaNM.Enums.Activating

            enabled: !root.connection.busy && !isActivating
            onClicked: root.connection.connectNetwork(model)
            Accessible.name: (model.Ssid || model.ItemUniqueName || "Wi-Fi network")
                + (isConnected ? ", connected" : ", connect")

            contentItem: RowLayout {
                spacing: Kirigami.Units.mediumSpacing

                Kirigami.Icon {
                    source: model.ConnectionIcon
                        || "network-wireless"

                    implicitWidth: 24
                    implicitHeight: 24
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Controls.Label {
                        Layout.fillWidth: true
                        textFormat: Text.PlainText
                        text: model.Ssid || model.ItemUniqueName
                            || "Unknown network"
                        elide: Text.ElideRight
                    }

                    Controls.Label {
                        text: networkItem.isConnected
                            ? "Connected"
                            : networkItem.isActivating
                                ? "Connecting…"
                                : model.SecurityTypeString
                                || "Available"

                        font.pixelSize: 11
                        opacity: 0.65
                    }
                }

                Controls.BusyIndicator {
                    running: networkItem.isActivating
                    visible: running
                    implicitWidth: 18
                    implicitHeight: 18
                }

                Kirigami.Icon {
                    visible: networkItem.isConnected
                    source: "checkmark"

                    implicitWidth: 18
                    implicitHeight: 18
                }
            }
        }
    }

    Controls.Label {
        Layout.fillWidth: true
        visible: root.wifiEnabled && networkList.count === 0
        text: root.discoveryHandler.scanning ? "Scanning for Wi-Fi networks…" : "No Wi-Fi networks found"
        opacity: 0.65
        wrapMode: Text.WordWrap
    }

    RowLayout {
        Layout.fillWidth: true
        visible: root.connection.busy || root.connection.message.length > 0

        Controls.BusyIndicator {
            running: root.connection.busy
            visible: running
            implicitWidth: 22
            implicitHeight: 22
        }

        Controls.Label {
            Layout.fillWidth: true
            text: root.connection.message
            textFormat: Text.PlainText
            wrapMode: Text.WordWrap
        }

        Controls.Button {
            text: "Cancel"
            visible: root.connection.busy
            enabled: !root.connection.cancelRequested
            onClicked: root.connection.cancel()
        }
    }

    Kirigami.InlineMessage {
        Layout.fillWidth: true
        visible: root.connection.error.length > 0
        type: Kirigami.MessageType.Error
        text: root.connection.error.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    }

}
