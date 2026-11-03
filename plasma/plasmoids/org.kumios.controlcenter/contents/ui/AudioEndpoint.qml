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
    // Device members used here; keep in sync with plasma/audio-api-contract.json.
    readonly property var requiredMembers: ["volume", "muted", "volumeWritable", "description", "name"]
    // Members a KDE update removed from the device object; such a device is never
    // read or written, rather than showing undefined values or throwing on write.
    readonly property var missingMembers: endpoint ? requiredMembers.filter(m => !(m in endpoint)) : []
    readonly property string apiProblem: missingMembers.length > 0
        ? label + " controls need an update for this KDE version (missing " + missingMembers.join(", ")
          + "). Open Devices & Microphone."
        : ""
    readonly property bool available: ready && endpoint !== null && missingMembers.length === 0
    readonly property bool volumeWritable: available && Boolean(endpoint.volumeWritable)
    readonly property real volume: available ? Number(endpoint.volume) / normalVolume : 0
    readonly property bool muted: available && Boolean(endpoint.muted)
    readonly property string deviceName: available
        ? String(endpoint.description || endpoint.name || label)
        : missingMembers.length > 0 ? label + " unavailable after a KDE update"
        : ready ? "No " + label.toLowerCase() + " device" : "Audio service unavailable"
    readonly property bool busy: request.busy
    readonly property string error: request.error || apiProblem
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
            if (apiProblem.length === 0)
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
