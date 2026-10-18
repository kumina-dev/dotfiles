import QtQuick
import QtTest
import org.kde.plasma.networkmanagement as PlasmaNM
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

TestCase {
    id: test
    name: "WiFi"
    when: windowShown
    width: 320
    height: 600

    ListModel { id: networks }
    QtObject {
        id: bus
        property var calls: []
        function asyncCall(message, resolve, reject) {
            calls.push({message: message, resolve: resolve, reject: reject})
        }
    }

    QtObject {
        id: newConnectionRunner
        property var calls: []
        function start(device, accessPoint, serial) {
            calls.push({device: device, accessPoint: accessPoint, serial: serial})
        }
    }

    Kumi.WiFiNewConnection { id: runner }
    SignalSpy { id: runnerSpy; target: runner; signalName: "finished" }

    QtObject {
        id: scanner
        property bool scanning: false
        function requestScan() {}
    }

    Kumi.WiFiDetails {
        id: view
        width: 300
        wifiEnabled: true
        connected: false
        ssid: ""
        networkSource: networks
        discoveryHandler: scanner
    }

    function network(overrides) {
        return Object.assign({
            Type: PlasmaNM.Enums.Wireless, Signal: 70,
            Ssid: "Test network", ItemUniqueName: "Test network",
            ConnectionIcon: "network-wireless", ConnectionState: PlasmaNM.Enums.Deactivated,
            SecurityType: PlasmaNM.Enums.Wpa2Psk, SecurityTypeString: "WPA2",
            DevicePath: "/test/device", SpecificPath: "/test/ap",
            ConnectionPath: "/test/profile", Uuid: "saved-profile"
        }, overrides || {})
    }

    function init() {
        networks.clear()
        runnerSpy.clear()
        bus.calls = []
        newConnectionRunner.calls = []
        view.connection.newConnectionRunner = newConnectionRunner
        view.wifiEnabled = true
        view.connection.bus = bus
        view.connection.busy = false
        view.connection.activePath = "/"
        view.connection.error = ""
        view.connection.message = ""
        view.connection.cancelRequested = false
        view.connection.timeoutInterval = 90000
        ++view.connection.requestId
    }

    function cleanup() {
        view.connection.finish("", false)
    }

    function test_filtersMixedNetworksAndUpdates() {
        networks.append(network({Ssid: "Wi-Fi"}))
        const proxy = findChild(view, "wifiNetworkModel")
        networks.append(network({Signal: 99, Ssid: "Strong Wi-Fi"}))
        compare(proxy.data(proxy.index(0, 0), proxy.sortRole), 99)
        networks.remove(1)
        networks.append(network({Type: PlasmaNM.Enums.Wired, Ssid: "Ethernet"}))
        networks.append(network({Type: PlasmaNM.Enums.Bridge, Ssid: "docker0"}))
        networks.append(network({Type: 20, Ssid: "lo"}))
        compare(view.networkCount, 1)
        networks.setProperty(1, "Type", PlasmaNM.Enums.Wireless)
        tryCompare(view, "networkCount", 2)
        networks.remove(0)
        tryCompare(view, "networkCount", 1)
        networks.clear()
        tryCompare(view, "networkCount", 0)
    }

    function test_savedConnectionProgressAndSuccess() {
        view.connection.connectNetwork(network())
        compare(bus.calls.length, 1)
        compare(bus.calls[0].message.member, "ActivateConnection")
        compare(bus.calls[0].message.signature, "(ooo)")
        compare(bus.calls[0].message.arguments, ["/test/profile", "/test/device", "/test/ap"])
        verify(view.connection.busy)
        bus.calls[0].resolve({values: ["/test/active"]})
        view.connection.observeState(1)
        verify(view.connection.busy)
        view.connection.observeState(2)
        verify(!view.connection.busy)
        compare(view.connection.message, "Connected to Test network")
    }

    function test_newNetworkUsesNativeSecretsAgent() {
        view.connection.connectNetwork(network({Uuid: "", ConnectionPath: ""}))
        compare(bus.calls.length, 0)
        compare(newConnectionRunner.calls.length, 1)
        compare(newConnectionRunner.calls[0].device, "/test/device")
        compare(newConnectionRunner.calls[0].accessPoint, "/test/ap")
        view.connection.activationFinished(newConnectionRunner.calls[0].serial, "/test/active", "")
        compare(view.connection.activePath, "/test/active")
        view.connection.observeState(4)
        verify(!view.connection.busy)
        verify(view.connection.error.indexOf("Could not connect") >= 0)
    }

    function test_requestErrorAllowsRetry() {
        view.connection.connectNetwork(network())
        bus.calls[0].reject({error: {message: "Permission denied"}})
        verify(!view.connection.busy)
        verify(view.connection.error.indexOf("Permission denied") >= 0)
        view.connection.connectNetwork(network())
        compare(view.connection.error, "")
        compare(bus.calls.length, 2)
    }

    function test_duplicateRequestAndConnectedRowIgnored() {
        view.connection.connectNetwork(network({ConnectionState: PlasmaNM.Enums.Activated}))
        compare(bus.calls.length, 0)
        view.connection.connectNetwork(network())
        view.connection.connectNetwork(network())
        compare(bus.calls.length, 1)
    }

    function test_cancelBeforeActivationReply() {
        view.connection.connectNetwork(network())
        view.connection.cancel()
        compare(bus.calls.length, 1)
        bus.calls[0].resolve({values: ["/test/active"]})
        compare(bus.calls.length, 2)
        compare(bus.calls[1].message.member, "DeactivateConnection")
        compare(bus.calls[1].message.arguments, ["/test/active"])
        bus.calls[1].resolve({values: []})
        verify(!view.connection.busy)
        compare(view.connection.message, "Connection cancelled")
    }

    function test_radioOffCancelsPendingRequest() {
        view.connection.connectNetwork(network())
        view.wifiEnabled = false
        verify(view.connection.cancelRequested)
    }

    function test_staleReplyDoesNotOverwriteRetry() {
        view.connection.connectNetwork(network())
        const previous = bus.calls[0]
        previous.reject({error: {message: "Rejected"}})
        view.connection.connectNetwork(network({Ssid: "Other network"}))
        previous.resolve({values: ["/test/old_active"]})
        compare(view.connection.activePath, "/")
        verify(view.connection.message.indexOf("Other network") >= 0)
    }

    function test_slowRequestStaysCancellable() {
        view.connection.timeoutInterval = 20
        view.connection.connectNetwork(network())
        tryVerify(function() { return view.connection.error.indexOf("longer than expected") >= 0 })
        verify(view.connection.busy)
        view.connection.cancel()
        verify(view.connection.cancelRequested)
    }

    function test_unavailableAndUnconfiguredEnterprise() {
        view.connection.connectNetwork(network({SpecificPath: "/"}))
        verify(!view.connection.busy)
        verify(view.connection.error.indexOf("no longer available") >= 0)
        view.connection.connectNetwork(network({Uuid: "", SecurityType: PlasmaNM.Enums.Wpa2Eap}))
        verify(view.connection.error.indexOf("enterprise") >= 0)
        compare(bus.calls.length, 0)
    }

    function test_newProfileResultAndShellQuoting() {
        compare(runner.quote("a'b;$(whoami)"), "'a'\\''b;$(whoami)'")
        runner.requests["test"] = 17
        runner.processResult("test", {"exit code": 0, stdout: "(objectpath '/org/freedesktop/NetworkManager/Settings/10', objectpath '/org/freedesktop/NetworkManager/ActiveConnection/20')"})
        compare(runnerSpy.count, 1)
        compare(Array.from(runnerSpy.signalArguments[0]), [17, "/org/freedesktop/NetworkManager/ActiveConnection/20", ""])
        runner.requests["failure"] = 18
        runner.processResult("failure", {"exit code": 1, stderr: "Permission denied\n"})
        compare(Array.from(runnerSpy.signalArguments[1]), [18, "/", "Permission denied"])
        runner.requests["malformed"] = 19
        runner.processResult("malformed", {"exit code": 0, stdout: "unexpected output"})
        verify(runnerSpy.signalArguments[2][2].indexOf("unexpected") >= 0)
    }


    function test_cancelFailureRemainsVisibleAndCanBeRetried() {
        view.connection.connectNetwork(network())
        bus.calls[0].resolve({values: ["/test/active"]})
        view.connection.cancel()
        bus.calls[1].reject({error: {message: "Permission denied"}})
        verify(view.connection.busy)
        verify(!view.connection.cancelRequested)
        verify(view.connection.error.indexOf("Could not cancel") >= 0)
        view.connection.cancel()
        compare(bus.calls.length, 3)
        bus.calls[2].resolve({values: []})
        verify(!view.connection.busy)
    }

}
