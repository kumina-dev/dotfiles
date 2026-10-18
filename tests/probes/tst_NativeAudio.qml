import QtQuick
import QtTest
import org.kde.plasma.private.volume as PulseAudio
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

// Opt-in read-only probe against the running audio daemon. Never writes volume,
// mute, defaults, stream routing or service state.
TestCase {
    name: "NativeAudioProbe"
    Kumi.NativeAudio { id: audio }
    SignalSpy { id: readySpy; target: audio; signalName: "readyChanged" }
    function test_backendReadOnly() {
        tryCompare(audio, "ready", true, 5000)
        verify(audio.output.available, "No default output is present on this machine")
        verify(audio.input.available, "No default input is present on this machine")
        verify(audio.output.deviceName.length > 0)
        verify(audio.input.deviceName.length > 0)
        verify(Number.isFinite(audio.output.volume))
        console.log("KDE audio ready; default output and microphone are available. No writes performed.")
    }
    function test_clientReconnectOnly() {
        tryCompare(audio, "ready", true, 5000)
        const outputName=audio.output.deviceName
        const inputName=audio.input.deviceName
        readySpy.clear()
        // Reconnects only THIS PROCESS's PulseAudioQt client; no server restart.
        audio.retry()
        tryVerify(function() { return readySpy.count >= 2 && audio.ready },5000)
        tryVerify(function() {return audio.output.available && audio.input.available},5000)
        compare(audio.output.deviceName,outputName)
        compare(audio.input.deviceName,inputName)
        console.log("Read-only client reconnect recovered defaults; no audio service/device changes.")
    }

}
