import QtQuick
import QtTest
import org.kde.kcmutils as KCM

TestCase {
    name: "PlasmaComponents"

    function test_nativeSettingsLauncherIsAvailable() {
        verify(KCM.KCMLauncher !== null)
        compare(typeof KCM.KCMLauncher.open, "function")
    }

    function test_widgetCompilation_data() {
        return [
            {tag: "control-center", widget: "org.kumios.controlcenter"},
            {tag: "system-menu", widget: "org.kumios.systemmenu"}
        ]
    }

    function test_widgetCompilation(data) {
        const component = Qt.createComponent(Qt.resolvedUrl(
            "../../plasma/plasmoids/" + data.widget + "/contents/ui/main.qml"))
        try {
            compare(component.status, Component.Ready, component.errorString())
        } finally {
            component.destroy()
        }
    }
}
