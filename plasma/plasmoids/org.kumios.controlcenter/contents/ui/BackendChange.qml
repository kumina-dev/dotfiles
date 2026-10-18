import QtQuick
import org.kde.plasma.workspace.dbus as DBus

QtObject {
    id: root
    property var bus: DBus.SystemBus
    property bool available: false
    property string identity: ""
    property var observed: null
    property var desired: null
    property string pendingIdentity: ""
    property bool accepted: false
    property string label: "Setting"
    property var makeMessage: null
    readonly property bool busy: request.busy
    property alias error: request.error
    property alias timeoutMs: request.timeoutMs
    property ControlRequest request: ControlRequest {
        id: request
        confirmed: root.accepted && root.available && root.identity === root.pendingIdentity
            && root.observed === root.desired
        timeoutMessage: root.label + " change not confirmed. Check its current state or open Settings before retrying."
    }
    onAvailableChanged: invalidate()
    onIdentityChanged: invalidate()
    function invalidate() {
        if (busy && (!available || identity !== pendingIdentity))
            request.fail(request.serial, label + " became unavailable or changed. Check the current device and retry.")
    }
    function set(value) {
        if (busy) return
        if (!available) { error = label + " unavailable. Open Settings to check the device."; return }
        if (observed === value) { error = ""; return }
        accepted = false
        desired = value
        pendingIdentity = identity
        const token = request.begin()
        try {
            bus.asyncCall(makeMessage(value), function() {
                if (!request.busy || request.serial !== token) return
                accepted = true
                request.check()
            }, function(reply) {
                request.fail(token, label + ": " + String(reply.error?.message || reply.message || reply) + ". Check Settings and retry.")
            })
        } catch (error) {
            request.fail(token, label + ": " + String(error))
        }
    }
}
