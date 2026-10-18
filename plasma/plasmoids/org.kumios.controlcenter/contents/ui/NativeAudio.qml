import QtQuick
import org.kde.plasma.private.volume as PulseAudio

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
}
