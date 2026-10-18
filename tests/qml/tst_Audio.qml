import QtQuick
import QtTest
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

TestCase {
    id: test
    name: "Audio"
    QtObject {
        id: state
        property var writes: []
    }
    Component {
        id: mockDevice
        QtObject {
            property string description: "Device"
            property bool volumeWritable: true
            property real volume: 32768
            property bool muted: false
        }
    }
    function fake(name) { return createTemporaryObject(mockDevice, test, {description:name}) }
    function record(target, key, value) { state.writes.push([key,value]) }
    Component { id: endpoint; Kumi.AudioEndpoint { timeoutMs: 60; writeProperty: record } }
    function init() { state.writes=[] }
    function test_followDevicesAndRecoveryWithoutWrites() {
        const audio=createTemporaryObject(endpoint,this,{ready:true,endpoint:fake("Speakers")})
        compare(audio.deviceName,"Speakers"); compare(audio.volume,0.5)
        audio.endpoint=null; verify(!audio.available)
        audio.endpoint=fake("Headphones"); compare(audio.deviceName,"Headphones")
        audio.ready=false; verify(!audio.available); compare(audio.deviceName,"Audio service unavailable")
        audio.ready=true; verify(audio.available); compare(state.writes.length,0)
    }
    function test_waitForObservedMuteAndRejectDuplicates() {
        const audio=createTemporaryObject(endpoint,this,{ready:true,endpoint:fake("Microphone")})
        audio.toggleMuted(); verify(audio.busy); compare(state.writes.length,1)
        audio.toggleMuted(); compare(state.writes.length,1)
        audio.endpoint.muted=true; tryCompare(audio,"busy",false); verify(audio.muted)
        compare(audio.error,"")
    }
    function test_timeoutThenRetry() {
        const audio=createTemporaryObject(endpoint,this,{ready:true,endpoint:fake("Output")})
        audio.setVolume(0.7); verify(audio.busy)
        tryCompare(audio,"busy",false); verify(audio.error.includes("not confirmed"))
        audio.setVolume(0.8); verify(audio.busy)
        audio.endpoint.volume=Math.round(0.8*65536); tryCompare(audio,"busy",false)
        compare(audio.error,"")
    }
    function test_deviceChangeInvalidatesRequest() {
        const audio=createTemporaryObject(endpoint,this,{ready:true,endpoint:fake("Old")})
        audio.toggleMuted(); verify(audio.busy)
        audio.endpoint=fake("New"); verify(!audio.busy)
        verify(audio.error.includes("device changed"))
        audio.endpoint.muted=true; verify(audio.error.includes("device changed"))
    }
    function test_clampWritesButShowActualAmplification() {
        const audio=createTemporaryObject(endpoint,this,{ready:true,endpoint:fake("Output")})
        audio.endpoint.volume=98304; compare(audio.volume,1.5)
        audio.setVolume(4); compare(state.writes[0][1],65536)
        audio.endpoint.volume=65536; tryCompare(audio,"busy",false)
        audio.setVolume(-1); compare(state.writes[1][1],0)
        audio.endpoint.volume=0; tryCompare(audio,"busy",false)
        audio.setVolume(NaN); compare(state.writes.length,2)
    }
    function test_unavailableNeverChangesDevice() {
        const audio=createTemporaryObject(endpoint,this,{ready:false,endpoint:fake("Output")})
        audio.toggleMuted(); compare(state.writes.length,0)
        verify(audio.error.includes("No controllable"))
    }
    function test_noopClearsError() {
        const audio=createTemporaryObject(endpoint,this,{ready:true,endpoint:fake("Output")})
        audio.request.error="previous failure"
        audio.setVolume(0.5); compare(audio.error,""); verify(!audio.busy)
    }
    function test_readonlyVolumeAndWriterError() {
        const audio=createTemporaryObject(endpoint,this,{ready:true,endpoint:fake("Output")})
        audio.endpoint.volumeWritable=false
        audio.setVolume(0.7); compare(state.writes.length,0); verify(audio.error.length>0)
        audio.writeProperty=function(){throw new Error("Denied")}
        audio.toggleMuted(); verify(!audio.busy); verify(audio.error.includes("Denied"))
    }
    function test_defaultWriterUsesEndpointAndConfirms() {
        const audio=createTemporaryObject(endpoint,this,{ready:true,endpoint:fake("Output")})
        audio.writeProperty=function(target,key,value){target[key]=value}
        audio.toggleMuted(); verify(audio.muted); verify(!audio.busy)
        audio.setVolume(0.25); compare(audio.volume,0.25); verify(!audio.busy)
    }

}
