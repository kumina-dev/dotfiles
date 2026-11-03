import QtQuick

// Light / Dark / Automatic appearance through KDE's global theme settings.
// A choice is complete only when kdeglobals reports the requested mode; a
// successful command alone is not success. KDE's accent service keeps the
// accent following the wallpaper in every mode.
QtObject {
    id: root
    // run(command, callback(exitCode, stdout, stderr)): CommandRunner in production.
    property var run: null
    // KWin Night Light day/night (true, false, or undefined when unknown); picks the
    // starting variant for Automatic, as KDE's switcher does.
    property var daylight: undefined

    readonly property var packages: ({light: "org.kumios.light", dark: "org.kumios.dark"})
    // Observed state.
    property string mode: ""            // "light", "dark", "auto", "other" or "" (unknown)
    property string globalTheme: ""
    property bool installed: false
    property bool wallpaperAccent: false
    property bool known: false

    property string desired: ""
    readonly property bool busy: request.busy
    property alias error: request.error
    property alias timeoutMs: request.timeoutMs
    property int pollMs: 500

    property ControlRequest request: ControlRequest {
        id: request
        timeoutMs: 15000
        confirmed: root.desired.length > 0 && root.mode === root.desired
        timeoutMessage: "Appearance change not confirmed. Check Global Theme settings before retrying."
    }
    property Timer poll: Timer {
        interval: root.pollMs
        repeat: true
        running: root.busy
        onTriggered: root.refresh()
    }

    readonly property string readCommand:
        "kreadconfig6 --file kdeglobals --group KDE --key AutomaticLookAndFeel;"
        + " kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage;"
        + " kreadconfig6 --file kdeglobals --group General --key accentColorFromWallpaper;"
        + " d=\"${XDG_DATA_HOME:-$HOME/.local/share}/plasma/look-and-feel\";"
        + " [ -d \"$d/org.kumios.light\" ] && [ -d \"$d/org.kumios.dark\" ] && echo installed || echo missing"

    function parse(stdout) {
        const lines = String(stdout).split("\n")
        const automatic = lines[0] === "true"
        globalTheme = lines[1] || ""
        wallpaperAccent = lines[2] === "true"
        installed = lines[3] === "installed"
        mode = automatic ? "auto"
            : globalTheme === packages.light ? "light"
            : globalTheme === packages.dark ? "dark"
            : "other"
        known = true
    }

    function refresh() {
        if (!run) return
        run(readCommand, function(exitCode, stdout) {
            if (exitCode === 0) parse(stdout)
        })
    }

    function startingVariant() {
        if (daylight === true) return "light"
        if (daylight === false) return "dark"
        return globalTheme === packages.light ? "light" : "dark"
    }

    function command(value) {
        if (value === "auto") {
            const write = "kwriteconfig6 --notify --file kdeglobals --group KDE --key "
            return write + "DefaultLightLookAndFeel " + packages.light
                + " && " + write + "DefaultDarkLookAndFeel " + packages.dark
                + " && " + write + "AutomaticLookAndFeel true"
                + " && plasma-apply-lookandfeel --keep-auto --apply " + packages[startingVariant()]
        }
        // Without --keep-auto KDE turns Automatic off: a manual choice wins.
        return "plasma-apply-lookandfeel --apply " + packages[value]
    }

    function set(value) {
        if (busy || !run) return
        if (!(value === "auto" || value in packages)) return
        if (known && !installed) {
            error = "KumiOS themes are not installed. Run plasma/appearance.py --apply current, then retry."
            return
        }
        if (mode === value) { error = ""; return }
        desired = value
        const token = request.begin()
        run(command(value), function(exitCode, stdout, stderr) {
            if (!request.busy || request.serial !== token) return
            if (exitCode !== 0) {
                const detail = String(stderr).trim() || ("exit code " + exitCode)
                request.fail(token, "Appearance: " + detail + ". Open Global Theme settings and retry.")
                return
            }
            refresh()
        })
    }
}
