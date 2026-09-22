import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls

import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import org.kde.plasma.private.sessions 2.0 as Sessions

PlasmoidItem {
    id: root

    preferredRepresentation: compactRepresentation

    property string pendingAction: ""

    Sessions.SessionManagement {
        id: session
    }

    compactRepresentation: Controls.ToolButton {
        text: "K"
        font.weight: Font.DemiBold

        onClicked: {
            root.pendingAction = ""
            root.expanded = !root.expanded
        }
    }

    fullRepresentation: Item {
        id: representation

        Layout.minimumWidth: 240
        Layout.maximumWidth: 240
        Layout.preferredWidth: 240

        Layout.minimumHeight: root.pendingAction === "" ? 220 : 125
        Layout.preferredHeight: root.pendingAction === "" ? 220 : 125

        Loader {
            id: pageLoader

            anchors.fill: parent

            sourceComponent:
                root.pendingAction === ""
                    ? menuComponent
                    : confirmationComponent
        }
    }

    Component {
        id: menuComponent

        ColumnLayout {
            implicitWidth: 240
            spacing: 0

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

                enabled: session.canSuspend

                onClicked: {
                    root.expanded = false
                    session.suspend()
                }
            }

            MenuButton {
                text: "Restart..."
                icon.name: "system-reboot"

                enabled: session.canReboot

                onClicked: {
                    root.pendingAction = "reboot"
                }
            }

            MenuButton {
                text: "Shut Down..."
                icon.name: "system-shutdown"

                enabled: session.canShutdown

                onClicked: {
                    root.pendingAction = "shutdown"
                }
            }

            Separator {}

            MenuButton {
                text: "Log Out Kumina…"
                icon.name: "system-log-out"

                enabled: session.canLogout

                onClicked: {
                    root.pendingAction = "logout"
                }
            }
        }
    }

    Component {
        id: confirmationComponent

        ColumnLayout {
            implicitWidth: 240
            spacing: Kirigami.Units.mediumSpacing

            Controls.Label {
                Layout.fillWidth: true

                text: {
                    switch (root.pendingAction) {
                    case "reboot":
                        return "Restart this PC?"
                    case "shutdown":
                        return "Shut down this PC?"
                    case "logout":
                        return "Log out?"
                    default:
                        return ""
                    }
                }

                font.pixelSize: 16
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }

            Controls.Label {
                Layout.fillWidth: true

                text: "All open apps will be closed."
                opacity: 0.75
                wrapMode: Text.WordWrap
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: Kirigami.Units.smallSpacing

                Item {
                    Layout.fillWidth: true
                }

                Controls.Button {
                    text: "Cancel"

                    onClicked: {
                        root.pendingAction = ""
                    }
                }

                Controls.Button {
                    highlighted: true

                    text: {
                        switch (root.pendingAction) {
                        case "reboot":
                            return "Restart"
                        case "shutdown":
                            return "Shut Down"
                        case "logout":
                            return "Log Out"
                        default:
                            return "Confirm"
                        }
                    }

                    onClicked: {
                        const action = root.pendingAction

                        root.pendingAction = ""
                        root.expanded = false

                        switch (action) {
                        case "reboot":
                            session.requestReboot(
                                Sessions.SessionManagement.Skip
                            )
                            break

                        case "shutdown":
                            session.requestShutdown(
                                Sessions.SessionManagement.Skip
                            )
                            break

                        case "logout":
                            session.requestLogout(
                                Sessions.SessionManagement.Skip
                            )
                            break
                        }
                    }
                }
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
