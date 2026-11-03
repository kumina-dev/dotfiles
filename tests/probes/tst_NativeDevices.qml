import QtQuick
import QtTest
import org.kde.bluezqt as BluezQt
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

// Read-only native device discovery; no radio power, pairing, scan or network writes.
TestCase {
    name: "NativeDevicesProbe"
    Kumi.BluetoothControl { id: bluetooth }
    Kumi.WiFiStatus { id: wifi }
    function test_bluetoothDiscoveryReadOnly() {
        tryVerify(function(){return BluezQt.Manager.operational},5000)
        verify(BluezQt.Manager.adapters.length > 0,"This machine has no Bluetooth adapter")
        verify(bluetooth.available)
        verify(bluetooth.adapter.ubi.startsWith("/org/bluez/"))
        console.log("Native Bluetooth adapter discovered; no radio or device changes performed.")
    }
    function test_wirelessStatusReadOnly() {
        wait(100)
        compare(typeof wifi.connected,"boolean")
        compare(typeof wifi.ssid,"string")
        console.log("Native wireless rows loaded; connected="+wifi.connected+"; no scan or network writes.")
    }
}
