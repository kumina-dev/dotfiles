import QtQuick

// Loads NativeAudio (KDE's private audio module) at runtime. If a KDE release
// removes or changes that module, only the audio controls are disabled: the
// Control Center still loads, and the audio section points to Sound settings.
// This file must not import the private module itself.
QtObject {
    id: root
    property url source: Qt.resolvedUrl("NativeAudio.qml")

    property var backend: null
    // Why NativeAudio is unusable; empty when audio controls can be used.
    property string incompatibility: ""
    readonly property bool compatible: backend !== null && incompatibility.length === 0

    // Stand-ins while unavailable: never ready, so nothing reads or writes a device.
    property AudioEndpoint unavailableOutput: AudioEndpoint { label: "Output" }
    property AudioEndpoint unavailableInput: AudioEndpoint { label: "Microphone" }

    readonly property var output: compatible ? backend.output : unavailableOutput
    readonly property var input: compatible ? backend.input : unavailableInput
    readonly property bool ready: compatible && backend.ready
    readonly property bool retrying: compatible && backend.retrying
    function retry() { if (compatible) backend.retry() }

    readonly property string unavailableMessage: "Audio controls need an update for this KDE version"
    + " (" + incompatibility + "). Use Devices & Microphone; other controls are unaffected."

    function load() {
        if (backend) { backend.destroy(); backend = null }
        incompatibility = ""
        const component = Qt.createComponent(source)
        if (component.status !== Component.Ready) {
            // Keep KDE's reason, without the file URL and position prefix.
            incompatibility = "KDE audio module could not be loaded: "
                + component.errorString().trim().split("\n")[0].replace(/^.*?:\d+:\d+:\s*/, "")
            return
        }
        let object = null
        try {
            object = component.createObject(root)
        } catch (error) {
            incompatibility = "KDE audio module failed to start: " + String(error)
            return
        }
        if (!object) {
            incompatibility = "KDE audio module failed to start: " + component.errorString().trim()
            return
        }
        const missing = typeof object.apiProblems === "function" ? object.apiProblems() : ["apiProblems()"]
        if (missing.length > 0) {
            object.destroy()
            incompatibility = "missing " + missing.join(", ")
            return
        }
        backend = object
    }

    Component.onCompleted: load()
}
