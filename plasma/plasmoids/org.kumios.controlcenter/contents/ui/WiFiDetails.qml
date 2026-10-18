
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

    spacing: Kirigami.Units.mediumSpacing

    PlasmaNM.NetworkModel {
        id: networkModel
    }

    // Filter before layout so wired/VPN entries do not occupy list rows.
    KItemModels.KSortFilterProxyModel {
        id: networkProxy
        sourceModel: networkModel
        filterRoleName: "Type"
        filterRegularExpression: "^" + PlasmaNM.Enums.Wireless + "$"
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
            // Discovery is read-only until connection handling is implemented.
            hoverEnabled: false

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
                        text: model.Ssid || model.ItemUniqueName
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

    Controls.Label {
        Layout.fillWidth: true
        visible: root.wifiEnabled && networkList.count === 0
        text: "No Wi-Fi networks found"
        opacity: 0.65
        wrapMode: Text.WordWrap
    }

}
