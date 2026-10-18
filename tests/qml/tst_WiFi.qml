import QtQuick
import QtTest
import org.kde.plasma.networkmanagement as PlasmaNM
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

TestCase {
    id: test
    name: "WiFi"
    when: windowShown
    visible: true
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
        view.visible = true
        view.cancelForget()
        networks.clear()
        runnerSpy.clear()
        bus.calls = []
        newConnectionRunner.calls = []
        view.connection.newConnectionRunner = newConnectionRunner
        view.wifiEnabled = true
        view.connection.bus = bus
        view.connection.busy = false
        view.connection.operation = "connect"
        view.connection.disconnectAccepted = false
        view.connection.cancelInFlight = false
        view.connection.cancelAccepted = false
        view.connection.activePath = "/"
        view.connection.error = ""
        view.connection.failureDetail = ""
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
        tryVerify(function() { return !view.connection.busy })
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
        verify(view.connection.busy)
        view.connection.observeState(4)
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
        view.connection.observeState(4)
        verify(!view.connection.busy)
    }

    function test_disconnectWaitsForDeviceState() {
        view.connection.disconnectNetwork(network({ConnectionState: PlasmaNM.Enums.Activated}))
        compare(bus.calls.length, 1)
        compare(bus.calls[0].message.member, "Disconnect")
        compare(bus.calls[0].message.path, "/test/device")
        compare(bus.calls[0].message.iface, "org.freedesktop.NetworkManager.Device")
        compare(bus.calls[0].message.arguments.length, 0)
        view.connection.observeDeviceState(30)
        verify(view.connection.busy) // State alone cannot precede request acceptance.
        bus.calls[0].resolve({values: []})
        verify(view.connection.busy) // Acceptance alone is not completion.
        view.connection.observeDeviceState(30)
        verify(!view.connection.busy)
        compare(view.connection.message, "Disconnected from Test network")
    }

    function test_disconnectFailureCanRetryAndBlocksDuplicates() {
        const connected = network({ConnectionState: PlasmaNM.Enums.Activated})
        view.connection.disconnectNetwork(connected)
        view.connection.disconnectNetwork(connected)
        view.connection.connectNetwork(network())
        view.connection.cancel() // A disconnect cannot be cancelled as an activation.
        compare(bus.calls.length, 1)
        bus.calls[0].reject({error: {message: "Permission denied"}})
        verify(!view.connection.busy)
        verify(view.connection.error.indexOf("Could not disconnect") >= 0)
        view.connection.disconnectNetwork(connected)
        compare(bus.calls.length, 2)
        compare(view.connection.error, "")
    }

    function test_disconnectTimeoutDoesNotLeaveViewBusy() {
        view.connection.timeoutInterval = 20
        view.connection.disconnectNetwork(network({ConnectionState: PlasmaNM.Enums.Activated}))
        tryVerify(function() { return !view.connection.busy })
        verify(view.connection.error.indexOf("did not complete") >= 0)
        bus.calls[0].resolve({values: []})
        verify(!view.connection.disconnectAccepted) // Late reply ignored.
    }

    function test_cancelAcknowledgementWaitsAndDoesNotDuplicate() {
        view.connection.connectNetwork(network())
        bus.calls[0].resolve({values: ["/test/active"]})
        view.connection.cancel()
        view.connection.cancel()
        compare(bus.calls.length, 2)
        bus.calls[1].resolve({values: []})
        view.connection.observeState(2)
        verify(view.connection.busy)
        view.connection.observeState(4)
        verify(!view.connection.busy)
    }

    function test_nativeFailureReasonSurvivesTerminalStateAndRetry() {
        view.connection.connectNetwork(network())
        bus.calls[0].resolve({values: ["/test/active"]})
        view.connection.observeState(4)
        view.connection.recordDeviceReason(120, 53)
        tryVerify(function() { return !view.connection.busy })
        verify(view.connection.error.indexOf("access point could not be reached") >= 0)
        view.connection.connectNetwork(network())
        compare(view.connection.failureDetail, "")
        bus.calls[1].resolve({values: ["/test/another_active"]})
        view.connection.recordDeviceReason(120, 7)
        view.connection.observeState(4)
        tryVerify(function() { return !view.connection.busy })
        verify(view.connection.error.indexOf("Authentication was cancelled") >= 0)
    }

    function test_disconnectButtonDoesNotActivateParentRow() {
        networks.append(network({ConnectionState: PlasmaNM.Enums.Activated}))
        tryVerify(function() { return findChild(view, "disconnectNetwork") !== null })
        const button = findChild(view, "disconnectNetwork")
        tryVerify(function() { return button.visible && button.width > 0 })
        mouseClick(button)
        compare(bus.calls.length, 1)
        compare(bus.calls[0].message.member, "Disconnect")
        verify(view.wifiEnabled)
    }

    function settingsReply(uuid, type) {
        return {values: [{connection: {uuid: uuid || "saved-profile", type: type || "802-11-wireless"}}]}
    }

    function test_forgetButtonConfirmsAndCancelDoesNotDelete() {
        networks.append(network())
        tryVerify(function() { const button = findChild(view, "forgetNetwork"); return button && button.visible })
        mouseClick(findChild(view, "forgetNetwork"))
        verify(view.pendingForget !== null)
        compare(bus.calls.length, 0)
        mouseClick(findChild(view, "cancelForget"))
        compare(view.pendingForget, null)
        compare(bus.calls.length, 0)
    }

    function test_forgetConfirmationSurvivesDelegateRemoval() {
        networks.append(network())
        waitForRendering(view)
        tryVerify(function() { const button = findChild(view, "forgetNetwork"); return button && button.visible })
        mouseClick(findChild(view, "forgetNetwork"))
        verify(view.pendingForget !== null)
        networks.clear()
        waitForRendering(view)
        mouseClick(findChild(view, "confirmForget"))
        compare(view.pendingForget, null)
        verify(view.connection.busy)
        compare(bus.calls.length, 1)
        compare(bus.calls[0].message.member, "GetSettings")
        compare(bus.calls[0].message.path, "/test/profile")
        bus.calls[0].resolve(settingsReply())
        compare(bus.calls.length, 2)
        compare(bus.calls[1].message.member, "Delete")
        compare(bus.calls[1].message.path, "/test/profile")
        compare(bus.calls[1].message.iface, "org.freedesktop.NetworkManager.Settings.Connection")
        verify(view.connection.busy)
        bus.calls[1].resolve({values: []})
        verify(!view.connection.busy)
        compare(view.connection.message, "Forgot Test network")
    }

    function test_forgetRechecksIdentityAndType() {
        view.requestForget(network())
        view.confirmForget()
        bus.calls[0].resolve(settingsReply("different-profile"))
        compare(bus.calls.length, 1)
        verify(view.connection.error.indexOf("profile changed") >= 0)
        view.requestForget(network())
        view.confirmForget()
        bus.calls[1].resolve(settingsReply("saved-profile", "802-3-ethernet"))
        compare(bus.calls.length, 2)
        verify(!view.connection.busy)
    }

    function test_forgetDeleteErrorAndRetry() {
        view.requestForget(network())
        view.confirmForget()
        bus.calls[0].resolve(settingsReply())
        bus.calls[1].reject({error: {message: "Permission denied"}})
        verify(!view.connection.busy)
        verify(view.connection.error.indexOf("Permission denied") >= 0)
        view.requestForget(network())
        view.confirmForget()
        compare(view.connection.error, "")
        bus.calls[2].resolve(settingsReply())
        bus.calls[3].resolve({values: []})
        compare(view.connection.message, "Forgot Test network")
    }

    function test_forgetReadErrorDoesNotDelete() {
        view.requestForget(network())
        view.confirmForget()
        bus.calls[0].reject({error: {message: "Profile no longer exists"}})
        compare(bus.calls.length, 1)
        verify(!view.connection.busy)
        verify(view.connection.error.indexOf("Profile no longer exists") >= 0)
    }

    function test_forgetTimeoutNeverDeletesAfterLateRead() {
        view.connection.timeoutInterval = 20
        view.requestForget(network())
        view.confirmForget()
        tryVerify(function() { return !view.connection.busy })
        bus.calls[0].resolve(settingsReply())
        compare(bus.calls.length, 1)
        verify(view.connection.error.indexOf("No response") >= 0)
    }

    function test_forgetRequiresSavedProfileAndPageScopedConfirmation() {
        view.requestForget(network({Uuid: ""}))
        compare(view.pendingForget, null)
        view.requestForget(network())
        view.visible = false
        compare(view.pendingForget, null)
        view.visible = true
        view.requestForget(network())
        view.wifiEnabled = false
        compare(view.pendingForget, null)
        compare(bus.calls.length, 0)
    }

    function test_forgetBlocksConcurrentOperationsAndDoesNotCancel() {
        view.requestForget(network())
        view.confirmForget()
        view.connection.connectNetwork(network())
        view.connection.disconnectNetwork(network({ConnectionState: PlasmaNM.Enums.Activated}))
        view.connection.forgetNetwork(network())
        view.connection.cancel()
        compare(bus.calls.length, 1)
        verify(view.connection.busy)
        verify(!view.connection.cancelRequested)
    }

}
