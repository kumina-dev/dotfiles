import QtQuick
import QtTest
import org.kde.plasma.workspace.dbus as DBus
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

// Run only via run_dbus_probe.py inside a new dbus-run-session.
TestCase {
    name: "IsolatedDBus"
    DBus.Properties { id: props; busType: DBus.BusType.Session
        service: "org.kumios.Probe"; path: "/Probe"; iface: "org.kumios.Probe" }
    property string settingKey: "Enabled"
    Kumi.BackendChange { id: setting
        label: "Test property"; bus: DBus.SessionBus; available: true; identity: "/Probe"
        observed: props.properties.Enabled ?? false
        timeoutMs: 1000
        makeMessage: function(value) { return {service:"org.kumios.Probe",path:"/Probe",
            iface:"org.kumios.Probe",member:"Set",signature:"(ssv)",
            arguments:["org.kumios.Probe",settingKey,new DBus.variant(value)]} }
    }
    Kumi.BackendChange { id: brightness
        label: "Test brightness"; bus: DBus.SessionBus; available: true; identity: "/Probe"
        observed: props.properties.Brightness ?? 0
        makeMessage: function(value) { return {service:"org.kumios.Probe",path:"/Probe",
            iface:"org.kumios.Probe",member:"SetBrightness",signature:"(iu)",
            arguments:[new DBus.int32(value),new DBus.uint32(1)]} }
    }
    function test_brightnessTypedRoundTrip() {
        tryVerify(function(){return props.properties.Brightness !== undefined},2000)
        brightness.set(25); tryCompare(brightness,"busy",false,2000)
        compare(brightness.error,""); compare(brightness.observed,25)
    }
    function test_denialIsVisibleAndRetryWorks() {
        settingKey="Denied"; setting.set(true); tryCompare(setting,"busy",false,2000)
        verify(setting.error.includes("Permission denied")); compare(setting.observed,false)
        settingKey="Enabled"
        setting.set(true); tryCompare(setting,"busy",false,2000)
        compare(setting.error,""); compare(setting.observed,true)
        setting.set(false); tryCompare(setting,"busy",false,2000)
        compare(setting.error,""); compare(setting.observed,false)
    }
    function test_variantBooleanRoundTrip() {
        tryVerify(function(){return props.properties.Enabled !== undefined},2000)
        setting.set(true)
        tryCompare(setting,"busy",false,2000)
        compare(setting.error,""); compare(setting.observed,true)
        setting.set(false); tryCompare(setting,"busy",false,2000)
        compare(setting.error,""); compare(setting.observed,false)
    }
}
