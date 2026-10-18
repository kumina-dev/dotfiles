import QtQuick
import QtTest
import org.kde.plasma.networkmanagement as PlasmaNM
import org.kde.taskmanager as TaskManager
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi
import "../../plasma/plasmoids/org.kumios.activeapp/contents/ui" as Active

TestCase {
    id: test
    name: "Status"
    ListModel { id: networks; dynamicRoles: true }
    Kumi.WiFiStatus { id: status; networkSource: networks }
    QtObject {
        id: tasks
        property var activeTask: null
        signal dataChanged()
        signal rowsInserted()
        signal rowsRemoved()
        signal modelReset()
        signal layoutChanged()
        function data(index,role) { return role === Qt.DecorationRole ? "test-icon" : "Test app" }
    }
    function init() { networks.clear(); status.radioEnabled=true; tasks.activeTask=null }
    function add(type,state,ssid) { networks.append({Type:type,ConnectionState:state,Ssid:ssid}) }
    function test_wiredAndVpnDoNotPretendWifiIsConnected() {
        add(PlasmaNM.Enums.Wired,PlasmaNM.Enums.Activated,"Wired")
        add(PlasmaNM.Enums.Vpn,PlasmaNM.Enums.Activated,"VPN")
        wait(0); verify(!status.connected); compare(status.ssid,"")
    }
    function test_wirelessAlongsideVpnAndUnicode() {
        add(PlasmaNM.Enums.Wireless,PlasmaNM.Enums.Activated,"Koti — mökki 日本 🐈")
        add(PlasmaNM.Enums.Vpn,PlasmaNM.Enums.Activated,"VPN")
        tryCompare(status,"connected",true)
        compare(status.ssid,"Koti — mökki 日本 🐈")
        status.radioEnabled=false; verify(!status.connected); compare(status.ssid,"")
        status.radioEnabled=true; tryCompare(status,"connected",true)
        networks.clear(); tryCompare(status,"connected",false); compare(status.ssid,"")
    }
    function test_activationAndRemovalFollowModel() {
        add(PlasmaNM.Enums.Wireless,PlasmaNM.Enums.Activating,"New network")
        tryCompare(status,"connecting",true); verify(!status.connected)
        networks.setProperty(0,"ConnectionState",PlasmaNM.Enums.Activated)
        tryCompare(status,"connected",true); verify(!status.connecting)
        networks.setProperty(0,"Ssid","Renamed")
        tryCompare(status,"ssid","Renamed")
        networks.remove(0); tryCompare(status,"connected",false)
    }
    function test_noActiveTaskClearsNameAndIcon() {
        const component=Qt.createComponent(Qt.resolvedUrl("../../plasma/plasmoids/org.kumios.activeapp/contents/ui/main.qml"))
        compare(component.status,Component.Ready,component.errorString())
        const app=createTemporaryObject(component,test,{taskSource:tasks})
        verify(app !== null)
        tasks.activeTask={valid:true}; tryCompare(app,"activeAppName","Test app")
        compare(app.activeAppIcon,"test-icon")
        tasks.activeTask={valid:false}; tryCompare(app,"activeAppName",""); compare(app.activeAppIcon,"")
        component.destroy()
    }
}
