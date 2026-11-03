import QtQuick
import QtTest
import "../../plasma/plasmoids/org.kumios.controlcenter/contents/ui" as Kumi

// KUM-22: Light / Dark / Automatic choice. A fake runner stands in for the shell;
// nothing is executed and the live appearance is never read or changed.
TestCase {
    id: test
    name: "Appearance"

    QtObject {
        id: fake
        property var calls: []
        // Simulated kdeglobals and installed themes.
        property string automatic: ""
        property string theme: "org.kumios.dark"
        property string accent: "true"
        property bool installed: true
        function state() {
            return automatic + "\n" + theme + "\n" + accent + "\n" + (installed ? "installed" : "missing") + "\n"
        }
        function run(command, callback) { calls.push({command: command, callback: callback}) }
        function applies() { return calls.filter(c => !c.command.startsWith("kreadconfig6")) }
        // Answer every outstanding read with the current simulated state.
        function answerReads() {
            const reads = calls.filter(c => c.command.startsWith("kreadconfig6") && !c.done)
            for (const c of reads) { c.done = true; c.callback(0, state(), "") }
        }
    }
    Component {
        id: controlType
        Kumi.AppearanceControl { run: fake.run; timeoutMs: 200; pollMs: 20 }
    }

    function init() {
        fake.calls = []; fake.automatic = ""; fake.theme = "org.kumios.dark"
        fake.accent = "true"; fake.installed = true
    }
    function setup() {
        const control = createTemporaryObject(controlType, test)
        control.refresh(); fake.answerReads()
        return control
    }

    function test_observesModeAccentAndInstallation() {
        let c = setup()
        compare(c.mode, "dark"); verify(c.wallpaperAccent); verify(c.installed)
        fake.theme = "org.kumios.light"; c.refresh(); fake.answerReads(); compare(c.mode, "light")
        fake.automatic = "true"; c.refresh(); fake.answerReads(); compare(c.mode, "auto")
        fake.automatic = ""; fake.theme = "org.kde.breeze.desktop"; fake.accent = ""
        c.refresh(); fake.answerReads()
        compare(c.mode, "other"); verify(!c.wallpaperAccent)
    }

    function test_manualChoiceAppliesThemeAndWaitsForObservedState() {
        const c = setup()
        c.set("light")
        verify(c.busy)
        compare(fake.applies().length, 1)
        compare(fake.applies()[0].command, "plasma-apply-lookandfeel --apply org.kumios.light")
        // Command success alone is not confirmation.
        fake.applies()[0].callback(0, "", ""); fake.answerReads(); verify(c.busy)
        fake.theme = "org.kumios.light"
        tryVerify(function() { fake.answerReads(); return !c.busy }, 1000)
        compare(c.mode, "light"); compare(c.error, "")
    }

    function test_automaticRegistersPairAndKeepsAutoMode() {
        const c = setup()
        c.daylight = true
        c.set("auto")
        const command = fake.applies()[0].command
        verify(command.includes("DefaultLightLookAndFeel org.kumios.light"))
        verify(command.includes("DefaultDarkLookAndFeel org.kumios.dark"))
        verify(command.includes("AutomaticLookAndFeel true"))
        verify(command.endsWith("plasma-apply-lookandfeel --keep-auto --apply org.kumios.light"))
        fake.applies()[0].callback(0, "", "")
        fake.automatic = "true"; fake.theme = "org.kumios.light"
        tryVerify(function() { fake.answerReads(); return !c.busy }, 1000)
        compare(c.mode, "auto")
    }

    function test_automaticStartingVariant() {
        const c = setup()
        c.daylight = false; compare(c.command("auto").slice(-15), "org.kumios.dark")
        c.daylight = undefined; compare(c.startingVariant(), "dark")   // current theme is dark
        fake.theme = "org.kumios.light"; c.refresh(); fake.answerReads()
        compare(c.startingVariant(), "light")
    }

    function test_failureTimeoutAndLateReplyCannotAffectRetry() {
        const c = setup()
        c.set("light"); c.set("auto"); compare(fake.applies().length, 1)   // one change at a time
        fake.applies()[0].callback(1, "", "plasma-apply-lookandfeel: package not found")
        verify(!c.busy); verify(c.error.includes("package not found"))

        c.set("light")                                     // retry; the change never shows up
        fake.applies()[1].callback(0, "", "")
        tryVerify(function() { fake.answerReads(); return !c.busy }, 1000)
        verify(c.error.includes("not confirmed"))

        c.set("light"); verify(c.busy); compare(c.error, "")
        fake.applies()[1].callback(1, "", "late failure")  // stale reply from the timed-out try
        verify(c.busy)
        fake.theme = "org.kumios.light"; fake.applies()[2].callback(0, "", "")
        tryVerify(function() { fake.answerReads(); return !c.busy }, 1000)
        compare(c.error, ""); compare(c.mode, "light")
    }

    function test_missingThemesAndCurrentModeDoNotRunCommands() {
        fake.installed = false
        const c = setup()
        c.set("light")
        verify(!c.busy); compare(fake.applies().length, 0)
        verify(c.error.includes("appearance.py"))
        fake.installed = true; c.refresh(); fake.answerReads()
        c.set("dark")                                       // already dark
        verify(!c.busy); compare(fake.applies().length, 0); compare(c.error, "")
        c.set("sepia")                                      // unknown mode is ignored
        compare(fake.applies().length, 0)
    }

    function test_externalChangeIsObserved() {
        const c = setup()
        fake.theme = "org.kumios.light"   // e.g. changed in System Settings
        c.refresh(); fake.answerReads()
        compare(c.mode, "light")
    }
}
