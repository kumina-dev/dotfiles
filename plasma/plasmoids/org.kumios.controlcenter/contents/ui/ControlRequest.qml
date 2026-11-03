import QtQuick

// An operation is complete only when the observed backend state agrees.
// Serial numbers prevent timed-out replies from changing a newer request.
QtObject {
    id: root
    property bool busy: false
    property string error: ""
    property int serial: 0
    property bool confirmed: false
    property int timeoutMs: 5000
    property string timeoutMessage: "Change not confirmed. Check the current state before retrying."
    property Timer deadline: Timer {
        interval: root.timeoutMs
        onTriggered: root.fail(root.serial, root.timeoutMessage)
    }
    onConfirmedChanged: check()
    function begin() {
        if (busy) return 0
        error = ""
        serial += 1
        busy = true
        deadline.restart()
        return serial
    }
    function check() {
        if (busy && confirmed) {
            busy = false
            deadline.stop()
        }
    }
    function fail(token, message) {
        if (!busy || token !== serial) return
        error = message
        busy = false
        deadline.stop()
    }
}
