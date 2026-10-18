
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import QtQml.Models

import org.kde.kirigami as Kirigami
import org.kde.plasma.networkmanagement as PlasmaNM

ColumnLayout {
    id: root

    required property bool wifiEnabled
    required property bool connected
    required property string ssid

    spacing: Kirigami.Units.mediumSpacing

    PlasmaNM.NetworkModel {
        id: networkModel
    }

    Connections {
        target: networkProxy

        function onRowsInserted(parent, first, last) {
            console.log(
                "KumiOS Wi-Fi: rows inserted:",
                first, last,
                "total:", networkProxy.rowCount()
            )
        }

        function onModelReset() {
            console.log(
                "KumiOS Wi-Fi: model reset:",
                networkProxy.rowCount()
            )
        }
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

    Controls.Label {
        Layout.fillWidth: true

        visible: root.wifiEnabled

        text: "Available networks"

        font.weight: Font.DemiBold
    }

    ListView {
        id: networkList

        Layout.fillWidth: true
        Layout.preferredHeight: Math.min(contentHeight, 220)

        clip: true
        spacing: 0

        model: networkModel

        delegate: Controls.ItemDelegate {
            id: networkItem

            required property var model

            readonly property bool isWireless:
                model.Type === 14

            readonly property bool isConnected:
                model.ConnectionState ===
                    PlasmaNM.Enums.Activated

            width: ListView.view.width
            height: isWireless ? 52 : 0
            visible: isWireless
            enabled: false

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
                        text: model.ItemUniqueName
                            || "Unknown network"
                        elide: Text.ElideRight
                    }

                    Controls.Label {
                        text: networkItem.isConnected
                            ? "Connected"
                            : model.SecurityTypeString
                                || "Available"

                        font.pixelSize: 11
                        opacity: 0.65
                    }
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
}
