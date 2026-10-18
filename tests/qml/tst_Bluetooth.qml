import QtQuick
import QtTest
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

TestCase {
    id: test
    name: "Bluetooth"
    QtObject {
        id: fakeBus
        property var calls: []
        function asyncCall(message, resolve, reject) { calls.push({message:message,resolve:resolve,reject:reject}) }
    }
    Component { id: adapterType; QtObject {
        property string ubi: "/org/bluez/hci7"
        property bool powered: false
        property var devices: []
    } }
    Component { id: managerType; QtObject {
        property bool operational: true
        property bool bluetoothBlocked: false
        property var usableAdapter: null
        property var adapters: []
    } }
    Component { id: deviceType; QtObject { property string name: "Headset"; property string friendlyName: ""; property bool connected: false } }
    Component { id: controlType; Kumi.BluetoothControl { bus: fakeBus; timeoutMs: 50 } }
    function init() { fakeBus.calls=[] }
    function setup() {
        const adapter=createTemporaryObject(adapterType,test)
        const manager=createTemporaryObject(managerType,test,{adapters:[adapter]})
        const control=createTemporaryObject(controlType,test,{manager:manager})
        return {adapter:adapter,manager:manager,control:control}
    }
    function test_nonHci0PowerAndWaitForActualState() {
        const x=setup(); x.control.toggle()
        compare(fakeBus.calls.length,1); verify(x.control.busy)
        compare(fakeBus.calls[0].message.path,"/org/bluez/hci7")
        compare(fakeBus.calls[0].message.signature,"(ssv)")
        fakeBus.calls[0].resolve(); verify(x.control.busy)
        x.adapter.powered=true; tryCompare(x.control,"busy",false)
        compare(x.control.error,""); compare(x.control.subtitle,"On")
    }
    function test_observationBeforeReplyStillNeedsAcknowledgement() {
        const x=setup(); x.control.toggle(); x.adapter.powered=true
        verify(x.control.busy); fakeBus.calls[0].resolve(); tryCompare(x.control,"busy",false)
    }
    function test_errorsTimeoutAndLateReplyCannotAffectRetry() {
        const x=setup(); x.control.toggle(); x.control.toggle(); compare(fakeBus.calls.length,1)
        fakeBus.calls[0].reject({message:"NotAuthorized"}); verify(!x.control.busy)
        verify(x.control.error.includes("NotAuthorized"))
        x.control.toggle(); tryCompare(x.control,"busy",false); verify(x.control.error.includes("not confirmed"))
        x.control.toggle(); verify(x.control.busy)
        fakeBus.calls[1].reject({message:"old error"}); verify(x.control.busy)
        x.adapter.powered=true; fakeBus.calls[2].resolve(); tryCompare(x.control,"busy",false)
        compare(x.control.error,"")
    }
    function test_removalAndServiceRecovery() {
        const x=setup(); x.control.toggle()
        x.manager.adapters=[]; verify(!x.control.available); verify(!x.control.busy)
        verify(x.control.error.includes("unavailable"))
        fakeBus.calls[0].resolve(); verify(!x.control.busy)
        x.manager.adapters=[x.adapter]; verify(x.control.available)
        x.manager.operational=false; verify(!x.control.available)
        x.manager.operational=true; verify(x.control.available)
        x.control.toggle(); fakeBus.calls[1].resolve(); x.adapter.powered=true
        tryCompare(x.control,"busy",false)
    }
    function test_blockedAndConnectedNamesFollowEvents() {
        const x=setup(); x.manager.bluetoothBlocked=true
        x.control.toggle(); compare(fakeBus.calls.length,0); verify(x.control.error.includes("blocked"))
        x.manager.bluetoothBlocked=false; x.adapter.powered=true
        const d=createTemporaryObject(deviceType,test)
        x.adapter.devices=[d]; compare(x.control.connectedName,"")
        d.connected=true; compare(x.control.connectedName,"Headset")
        d.name="New name"; compare(x.control.connectedName,"New name")
        d.friendlyName="My headset"; compare(x.control.connectedName,"My headset")
        d.connected=false; compare(x.control.connectedName,"")
    }
}
