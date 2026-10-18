import QtQuick

// Receives KDE's live default sink/source. Injectable for tests, no custom daemon.
QtObject {
    id: root
    property var endpoint: null
    property bool ready: false
    property var writeProperty: function(target, key, value) { target[key] = value }
    property string label: "Audio"
    // PulseAudio's PA_VOLUME_NORM (also used by PipeWire's PulseAudio service).
    readonly property int normalVolume: 65536
    readonly property bool available: ready && endpoint !== null
    readonly property bool volumeWritable: available && Boolean(endpoint.volumeWritable)
    readonly property real volume: available ? Number(endpoint.volume) / normalVolume : 0
    readonly property bool muted: available && Boolean(endpoint.muted)
    readonly property string deviceName: available
        ? String(endpoint.description || endpoint.name || label)
        : ready ? "No " + label.toLowerCase() + " device" : "Audio service unavailable"
    readonly property bool busy: request.busy
    readonly property string error: request.error
    property string pendingProperty: ""
    property var desired: null
    property var pendingEndpoint: null
    property alias timeoutMs: request.timeoutMs
    property ControlRequest request: ControlRequest {
        id: request
        confirmed: root.available && root.endpoint === root.pendingEndpoint
            && (root.pendingProperty === "muted"
                ? root.muted === root.desired
                : Math.abs(Number(root.endpoint.volume) - Number(root.desired)) <= 1)
        timeoutMessage: root.label + " change not confirmed. Open Devices & Microphone or retry."
    }
    onEndpointChanged: invalidate()
    onReadyChanged: invalidate()
    function invalidate() {
        if (busy && (!available || endpoint !== pendingEndpoint))
            request.fail(request.serial, label + " device changed or disconnected. Check the current device and retry.")
    }
    function change(key, value) {
        if (busy) return
        if (!available || (key === "volume" && !volumeWritable)) {
            request.error = "No controllable " + label.toLowerCase() + " device. Open Devices & Microphone."
            return
        }
        if (endpoint[key] === value) { request.error = ""; return }
        pendingProperty = key
        desired = value
        pendingEndpoint = endpoint
        const token = request.begin()
        try {
            writeProperty(endpoint, key, value)
            request.check()
        } catch (error) {
            request.fail(token, label + ": " + String(error))
        }
    }
    function setVolume(value) {
        if (!Number.isFinite(value)) return
        change("volume", Math.round(Math.max(0, Math.min(1, value)) * normalVolume))
    }
    function toggleMuted() { change("muted", !muted) }
}
