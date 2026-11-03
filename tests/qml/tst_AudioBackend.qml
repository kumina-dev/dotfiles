import QtQuick
import QtTest
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

// KUM-23: a KDE release that changes the private audio module must disable only
// the audio controls. Fixtures stand in for NativeAudio; no real device is used.
TestCase {
    id: test
    name: "AudioBackend"

    Component { id: backendType; Kumi.AudioBackend {} }
    QtObject {
        id: device
        property string description: "Speakers"
        property string name: "speakers"
        property bool volumeWritable: true
        property real volume: 32768
        property bool muted: false
    }
    // A device object from a KDE release that renamed `volumeWritable`.
    QtObject {
        id: renamedDevice
        property string description: "Speakers"
        property string name: "speakers"
        property bool canChangeVolume: true
        property real volume: 32768
        property bool muted: false
    }
    Component { id: endpointType; Kumi.AudioEndpoint { label: "Output"; ready: true } }

    function backend(fixture) {
        return createTemporaryObject(backendType, test, {source: Qt.resolvedUrl("fixtures/" + fixture)})
    }

    function test_missingModuleDisablesOnlyAudio() {
        const audio = backend("BrokenAudio.qml")
        verify(!audio.compatible)
        verify(audio.incompatibility.includes("could not be loaded"), audio.incompatibility)
        verify(audio.unavailableMessage.includes("Devices & Microphone"))
        verify(!audio.ready); verify(!audio.retrying)
        verify(!audio.output.available); verify(!audio.input.available)
        audio.output.setVolume(0.5)      // must neither throw nor write
        audio.input.toggleMuted()
        verify(!audio.output.busy); verify(!audio.input.busy)
        audio.retry()                    // no-op; reconnecting cannot help
    }

    function test_renamedMembersAreRejectedBeforeUse() {
        const audio = backend("OutdatedAudio.qml")
        verify(!audio.compatible)
        compare(audio.backend, null)
        compare(audio.incompatibility, "missing Context.state, Server.defaultSink")
        verify(!audio.output.available)
    }

    function test_compatibleBackendPassesThrough() {
        const audio = backend("WorkingAudio.qml")
        verify(audio.compatible); compare(audio.incompatibility, "")
        verify(audio.ready)
        compare(audio.output, audio.backend.output)
        audio.backend.output.endpoint = device
        verify(audio.output.available)
        compare(audio.output.deviceName, "Speakers")
        audio.retry(); compare(audio.backend.retries, 1)
    }

    function test_reloadRecoversAfterFixedModule() {
        const audio = backend("BrokenAudio.qml")
        verify(!audio.compatible)
        audio.source = Qt.resolvedUrl("fixtures/WorkingAudio.qml")
        audio.load()
        verify(audio.compatible)
    }

    function test_renamedDeviceMemberBlocksReadsAndWrites() {
        const writes = []
        const endpoint = createTemporaryObject(endpointType, test, {
            endpoint: renamedDevice,
            writeProperty: function(target, key, value) { writes.push(key) }
        })
        verify(!endpoint.available)
        compare(endpoint.missingMembers, ["volumeWritable"])
        verify(endpoint.error.includes("missing volumeWritable"), endpoint.error)
        compare(endpoint.deviceName, "Output unavailable after a KDE update")
        compare(endpoint.volume, 0)
        endpoint.setVolume(0.75); endpoint.toggleMuted()
        compare(writes.length, 0); verify(!endpoint.busy)
        // A compatible device works normally again.
        endpoint.endpoint = device
        verify(endpoint.available); compare(endpoint.error, "")
    }
}
