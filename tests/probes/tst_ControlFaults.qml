import QtQuick
import QtQuick.Controls as Controls
import QtTest

// Run through run_control_fault_probe.py; ui/ is a disposable production copy.
TestCase {
    id: test
    name: "ControlFaultPresentation"
    when: windowShown
    visible: true
    width: 360; height: 900
    property var widget
    property var popup
    QtObject {
        id: fakeBus
        property var calls: []
        function asyncCall(message, resolve, reject) { calls.push({resolve:resolve,reject:reject}) }
    }
    QtObject {
        id: manager
        property bool operational: true
        property bool bluetoothBlocked: false
        property var usableAdapter: null
        property var adapters: []
    }
    QtObject { id: adapter
        property string ubi: "/org/bluez/testOnly"
        property bool powered: false
        property var devices: []
    }
    QtObject { id: endpoint
        property string description: "Simulated output"
        property bool volumeWritable: true
        property real volume: 32768
        property bool muted: false
    }
    function init() {
        fakeBus.calls=[]; manager.operational=true; manager.bluetoothBlocked=false
        manager.adapters=[adapter]; adapter.powered=false
        endpoint.volume=32768; endpoint.muted=false
        const component=Qt.createComponent("ui/main.qml")
        compare(component.status,Component.Ready,component.errorString())
        widget=createTemporaryObject(component,test)
        verify(widget !== null)
        widget.probeBluetooth.manager=manager
        widget.probeBluetooth.bus=fakeBus
        widget.probeBluetooth.timeoutMs=80
        widget.probeAudio.output.endpoint=endpoint
        widget.probeAudio.output.ready=true
        widget.probeAudio.output.timeoutMs=80
        widget.probeAudio.output.writeProperty=function(target,key,value){target[key]=value}
        popup=createTemporaryObject(widget.fullRepresentation,test,{width:320,height:850,visible:true})
        verify(popup !== null)
        wait(30)
    }
    function named(name) { const item=findChild(popup,name); verify(item !== null,name); return item }
    function test_adapterRemovalAndBlockedPresentation() {
        const tile=named("probeBluetoothTile"), error=named("probeRadioError")
        manager.adapters=[]
        compare(tile.subtitle,"No adapter"); verify(!widget.probeBluetooth.available)
        // Details remain accessible without invoking a native settings window.
        verify(tile.enabled); verify(tile.detailsRequested !== undefined)
        manager.adapters=[adapter]; manager.bluetoothBlocked=true
        compare(tile.subtitle,"Blocked — open Bluetooth settings")
        widget.probeBluetooth.toggle()
        compare(fakeBus.calls.length,0); verify(error.visible)
        verify(error.text.includes("blocked")); compare(error.Controls.ToolTip.text,error.text)
        manager.bluetoothBlocked=false; widget.probeBluetooth.toggle()
        verify(widget.probeBluetooth.busy)
        manager.adapters=[]
        verify(!widget.probeBluetooth.busy); verify(error.text.includes("unavailable"))
        fakeBus.calls[0].resolve(); verify(!widget.probeBluetooth.busy)
        manager.adapters=[adapter]; widget.probeBluetooth.toggle()
        adapter.powered=true; fakeBus.calls[1].resolve()
        tryCompare(widget.probeBluetooth,"busy",false)
        compare(error.text,""); verify(!error.visible); compare(tile.subtitle,"On")
    }
    function test_permissionErrorTextAndRetry() {
        const error=named("probeRadioError")
        widget.probeBluetooth.toggle()
        fakeBus.calls[0].reject({message:"Permission denied: " + "controlled failure detail ".repeat(25)})
        verify(error.visible); verify(error.text.includes("Permission denied"))
        verify(error.text.includes("Check Settings and retry"))
        compare(error.Controls.ToolTip.text,error.text)
        compare(error.maximumLineCount,3)
        widget.probeBluetooth.toggle()
        adapter.powered=true; fakeBus.calls[1].resolve()
        tryCompare(widget.probeBluetooth,"busy",false)
        compare(error.text,""); verify(!error.visible)
    }
    function test_brightnessDenialAndRetryPresentation() {
        const change=widget.probeBrightness, error=named("probeBrightnessError")
        change.bus=fakeBus; change.available=true; change.identity="test-display"
        change.observed=40; change.makeMessage=function(value){return {}}
        change.set(60)
        verify(error.visible); compare(error.text,"Applying brightness…")
        fakeBus.calls[0].reject({message:"Controlled permission denial"})
        verify(error.visible); verify(error.text.includes("Controlled permission denial"))
        compare(error.Controls.ToolTip.text,error.text); compare(change.observed,40)
        change.set(60); change.observed=60; fakeBus.calls[1].resolve()
        tryCompare(change,"busy",false)
        compare(change.error,""); verify(!error.visible)
    }
    function test_audioPendingTimeoutAndRetryPresentation() {
        const error=named("probeAudioError"), pending=named("probeAudioPending")
        const audio=widget.probeAudio.output
        audio.writeProperty=function() {} // Deliberately withhold confirmation; no native writer.
        audio.setVolume(0.75)
        verify(pending.visible)
        tryCompare(audio,"busy",false)
        verify(error.visible); verify(error.text.includes("not confirmed"))
        compare(error.Controls.ToolTip.text,error.text)
        verify(named("probeAudioSettings").enabled)
        compare(audio.volume,0.5)
        audio.writeProperty=function(target,key,value){target[key]=value}
        audio.setVolume(0.75)
        tryCompare(audio,"busy",false)
        compare(audio.volume,0.75); compare(error.text,"")
        verify(!error.visible); verify(!pending.visible)
    }
}
