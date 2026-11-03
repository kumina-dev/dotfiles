import QtQuick
import QtTest
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

// The selected Light / Dark / Automatic button must stay visibly selected: KDE's
// desktop style only draws `checked` on checkable buttons, and a click must not
// leave a button selected unless the observed mode agrees. Fake runner only.
TestCase {
    id: test
    name: "AppearanceButton"
    width: 360; height: 80
    visible: true
    when: windowShown

    QtObject {
        id: fake
        property var calls: []
        property string theme: "org.kumios.dark"
        function run(command, callback) { calls.push({command: command, callback: callback}) }
        function answerReads() {
            for (const c of calls.filter(c => c.command.startsWith("kreadconfig6") && !c.done)) {
                c.done = true
                c.callback(0, "\n" + theme + "\ntrue\ninstalled\n", "")
            }
        }
        function applies() { return calls.filter(c => !c.command.startsWith("kreadconfig6")) }
    }
    Component {
        id: controlType
        Kumi.AppearanceControl { run: fake.run; timeoutMs: 300; pollMs: 20 }
    }
    Component {
        id: buttonType
        Kumi.AppearanceModeButton { width: 110; height: 36 }
    }

    function init() { fake.calls = []; fake.theme = "org.kumios.dark" }
    function setup() {
        const control = createTemporaryObject(controlType, test)
        control.refresh(); fake.answerReads()
        const light = createTemporaryObject(buttonType, test, {control: control, mode: "light", text: "Light", x: 0})
        const dark = createTemporaryObject(buttonType, test, {control: control, mode: "dark", text: "Dark", x: 120})
        return {control: control, light: light, dark: dark}
    }

    function test_selectedButtonIsCheckableSoTheStyleDrawsIt() {
        const x = setup()
        verify(x.dark.checkable); verify(x.light.checkable)
        verify(x.dark.checked); verify(!x.light.checked)
    }

    function test_clickSelectsOnlyAfterConfirmation() {
        const x = setup()
        mouseClick(x.light)
        compare(fake.applies().length, 1)
        // The click alone must not select Light, and Dark stays selected.
        verify(!x.light.checked); verify(x.dark.checked)
        fake.applies()[0].callback(0, "", "")
        fake.theme = "org.kumios.light"
        tryVerify(function() { fake.answerReads(); return !x.control.busy }, 1000)
        verify(x.light.checked); verify(!x.dark.checked)
    }

    function test_clickingSelectedButtonKeepsItSelected() {
        const x = setup()
        mouseClick(x.dark)                      // would toggle it off without re-binding
        verify(x.dark.checked)
        compare(fake.applies().length, 0)       // already dark: no command
    }

    function test_failedChangeLeavesPreviousSelection() {
        const x = setup()
        mouseClick(x.light)
        fake.applies()[0].callback(1, "", "denied")
        verify(!x.control.busy)
        verify(x.dark.checked); verify(!x.light.checked)
        fake.theme = "org.kumios.light"          // later external change still shows
        x.control.refresh(); fake.answerReads()
        verify(x.light.checked); verify(!x.dark.checked)
    }
}
