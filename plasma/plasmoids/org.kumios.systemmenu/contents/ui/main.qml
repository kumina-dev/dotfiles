import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls

import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    preferredRepresentation: compactRepresentation

    compactRepresentation: Controls.ToolButton {
        text: "K"

        font.weight: Font.DemiBold

        onClicked: root.expanded = !root.expanded
    }

    fullRepresentation: ColumnLayout {
        spacing: 0

        implicitWidth: 220

        MenuButton {
            text: "About This PC"
            icon.name: "computer"

            onClicked: {
                root.expanded = false
            }
        }

        Separator {}

        MenuButton {
            text: "Sleep"
            icon.name: "system-suspend"

            onClicked: {
                root.expanded = false
            }
        }

        MenuButton {
            text: "Restart…"
            icon.name: "system-reboot"

            onClicked: {
                root.expanded = false
            }
        }

        MenuButton {
            text: "Shut Down…"
            icon.name: "system-shutdown"

            onClicked: {
                root.expanded = false
            }
        }

        Separator {}

        MenuButton {
            text: "Log Out Kumina…"
            icon.name: "system-log-out"

            onClicked: {
                root.expanded = false
            }
        }
    }

    component MenuButton: Controls.ItemDelegate {
        Layout.fillWidth: true

        implicitHeight: 38

        leftPadding: Kirigami.Units.largeSpacing
        rightPadding: Kirigami.Units.largeSpacing

        contentItem: RowLayout {
            spacing: Kirigami.Units.smallSpacing

            Kirigami.Icon {
                source: icon.name

                implicitWidth: Kirigami.Units.iconSizes.small
                implicitHeight: implicitWidth
            }

            Controls.Label {
                text: parent.parent.text

                Layout.fillWidth: true
            }
        }
    }

    component Separator: Rectangle {
        Layout.fillWidth: true

        implicitHeight: 1

        color: Kirigami.Theme.separatorColor

        opacity: 0.5

        Layout.topMargin: 5
        Layout.bottomMargin: 5
    }
}
