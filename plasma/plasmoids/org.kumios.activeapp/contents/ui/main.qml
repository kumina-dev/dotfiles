import QtQuick
import QtQuick.Layouts

import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager

PlasmoidItem {
    id: root

    preferredRepresentation: fullRepresentation

    property var taskSource: tasksModel

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
        const index = root.taskSource.activeTask

        if (!index || !index.valid) {
            root.activeAppName = ""
            root.activeAppIcon = ""
            return
        }

        root.activeAppName =
            root.taskSource.data(
                index,
                TaskManager.AbstractTasksModel.AppName
            ) || ""

        root.activeAppIcon =
            root.taskSource.data(
                index,
                Qt.DecorationRole
            ) || ""
    }

    Connections {
        target: root.taskSource

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
        function onModelReset() { root.updateActiveTask() }
        function onLayoutChanged() { root.updateActiveTask() }
    }

    onTaskSourceChanged: updateActiveTask()
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
