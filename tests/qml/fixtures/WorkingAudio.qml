import QtQuick
import "../../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

// A compatible backend standing in for NativeAudio; touches no real device.
QtObject {
    id: root
    property bool ready: true
    property bool retrying: false
    property int retries: 0
    property Kumi.AudioEndpoint output: Kumi.AudioEndpoint { label: "Output"; ready: root.ready }
    property Kumi.AudioEndpoint input: Kumi.AudioEndpoint { label: "Microphone"; ready: root.ready }
    function retry() { retries += 1 }
    function apiProblems() { return [] }
}
