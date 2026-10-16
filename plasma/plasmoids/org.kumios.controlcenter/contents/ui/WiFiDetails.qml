
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls

import org.kde.kirigami as Kirigami

ColumnLayout {
    id: root

    required property bool wifiEnabled
    required property bool connected
    required property string ssid

    spacing: Kirigami.Units.mediumSpacing

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

    Controls.Label {
        Layout.fillWidth: true

        visible: root.wifiEnabled

        text: "Network discovery will be added next."

        opacity: 0.65
        wrapMode: Text.WordWrap
    }
}
