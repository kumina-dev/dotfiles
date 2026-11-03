import QtQuick
import QtQuick.Controls as Controls

// One Light / Dark / Automatic choice. KDE's desktop style draws the selected
// state only for checkable buttons, so the button is checkable; a click would
// toggle `checked` and break the binding, so it is re-bound to the observed mode.
// The selection therefore moves only once AppearanceControl confirms the change.
Controls.ToolButton {
    id: button
    required property var control      // AppearanceControl
    required property string mode
    property string tooltip: ""

    readonly property bool selected: control.mode === mode

    checkable: true
    checked: selected
    enabled: !control.busy
    Accessible.name: text + " appearance"
    Controls.ToolTip.visible: hovered && tooltip.length > 0
    Controls.ToolTip.text: tooltip

    onClicked: {
        checked = Qt.binding(function() { return button.selected })
        control.set(mode)
    }
}
