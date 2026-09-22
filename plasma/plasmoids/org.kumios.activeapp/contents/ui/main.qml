import QtQuick
import QtQuick.Layouts

import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager

PlasmoidItem {
    id: root

    preferredRepresentation: fullRepresentation

    property string activeAppName: ""
    property var activeAppIcon: ""

    TaskManager.TasksModel {
        id: tasksModel

        groupMode: TaskManager.TasksModel.GroupDisabled
        sortMode: TaskManager.TasksModel.SortDisabled

        filterByVirtualDesktop: false
        filterByActivity: false
        filterByScreen: false
    }

    function updateActiveTask() {
        const index = tasksModel.activeTask

        if (!index || !index.valid) {
            return
        }

        root.activeAppName =
            tasksModel.data(
                index,
                TaskManager.AbstractTasksModel.AppName
            ) || ""

        root.activeAppIcon =
            tasksModel.data(
                index,
                Qt.DecorationRole
            ) || ""
    }

    Connections {
        target: tasksModel

        function onActiveTaskChanged() {
            root.updateActiveTask()
        }

        function onDataChanged() {
            root.updateActiveTask()
        }

        function onRowsInserted() {
            root.updateActiveTask()
        }

        function onRowsRemoved() {
            root.updateActiveTask()
        }
    }

    Component.onCompleted: updateActiveTask()

    fullRepresentation: RowLayout {
        id: contentRow

        spacing: Kirigami.Units.smallSpacing

        Kirigami.Icon {
            source: root.activeAppIcon

            visible: root.activeAppName.length > 0

            implicitWidth: Kirigami.Units.iconSizes.small
            implicitHeight: implicitWidth
        }

        Text {
            text: root.activeAppName

            visible: text.length > 0

            color: Kirigami.Theme.textColor
            font.weight: Font.DemiBold

            elide: Text.ElideRight

            Layout.maximumWidth: 220
        }
    }
}
