import QtQuick
import QtQuick.Layouts
import QtTest

// Offscreen construction only. Opens no settings pages, performs no device writes.
TestCase {
    id: test
    name: "ControlCenterProbe"
    function test_popupConstruction() {
        const component=Qt.createComponent(Qt.resolvedUrl("../../plasma/plasmoids/org.kumios.controlcenter/contents/ui/main.qml"))
        compare(component.status,Component.Ready,component.errorString())
        const widget=createTemporaryObject(component,test)
        verify(widget !== null)
        const popup=createTemporaryObject(widget.fullRepresentation,test,{width:320})
        verify(popup !== null)
        wait(100)
        verify(popup.Layout.preferredHeight > 0)
        verify(popup.Layout.preferredHeight < 720,"Popup too tall at the default font size")
        console.log("Control Center preferred height: "+popup.Layout.preferredHeight)
        component.destroy()
    }
}
