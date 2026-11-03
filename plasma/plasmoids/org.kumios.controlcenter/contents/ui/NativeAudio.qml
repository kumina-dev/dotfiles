import QtQuick
import org.kde.plasma.private.volume as PulseAudio

// The only file importing KDE's private audio module. AudioBackend loads it at
// runtime, so a KDE release that changes this module disables audio controls
// only, not the whole Control Center. Keep `required*` in sync with
// plasma/audio-api-contract.json (tests/test_audio_api.py checks this).
QtObject {
    id: root
    // KDE's Context owns daemon reconnects and the models own device lifetimes.
    property PulseAudio.SinkModel sinks: PulseAudio.SinkModel {}
    property PulseAudio.SourceModel sources: PulseAudio.SourceModel {}
    readonly property bool ready: PulseAudio.Context.state === PulseAudio.Context.Ready
    property AudioEndpoint output: AudioEndpoint {
        label: "Output"
        ready: root.ready
        endpoint: PulseAudio.Server.defaultSink
    }
    readonly property bool retrying: !ready && (PulseAudio.Context.autoConnecting
        || PulseAudio.Context.state === PulseAudio.Context.Connecting
        || PulseAudio.Context.state === PulseAudio.Context.Authorizing
        || PulseAudio.Context.state === PulseAudio.Context.SettingName)
    function retry() { if (!retrying) PulseAudio.Context.reconnectDaemon() }
    property AudioEndpoint input: AudioEndpoint {
        label: "Microphone"
        ready: root.ready
        endpoint: PulseAudio.Server.defaultSource
    }

    readonly property var requiredContext: ["state", "autoConnecting"]
    readonly property var requiredContextMethods: ["reconnectDaemon"]
    readonly property var requiredStates: ["Ready", "Connecting", "Authorizing", "SettingName"]
    readonly property var requiredServer: ["defaultSink", "defaultSource"]

    // Names of the members this component uses that KDE's module no longer has.
    function apiProblems() {
        const missing = []
        for (const name of requiredContext)
            if (!(name in PulseAudio.Context)) missing.push("Context." + name)
        for (const name of requiredContextMethods)
            if (typeof PulseAudio.Context[name] !== "function") missing.push("Context." + name + "()")
        for (const name of requiredStates)
            if (PulseAudio.Context[name] === undefined) missing.push("Context.State." + name)
        for (const name of requiredServer)
            if (!(name in PulseAudio.Server)) missing.push("Server." + name)
        return missing
    }
}
