import QtQuick
import "../../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

// Simulates a KDE release that renamed members NativeAudio relies on.
QtObject {
    property bool ready: true
    property bool retrying: false
    property Kumi.AudioEndpoint output: Kumi.AudioEndpoint { label: "Output"; ready: true }
    property Kumi.AudioEndpoint input: Kumi.AudioEndpoint { label: "Microphone"; ready: true }
    function retry() {}
    function apiProblems() { return ["Context.state", "Server.defaultSink"] }
}
