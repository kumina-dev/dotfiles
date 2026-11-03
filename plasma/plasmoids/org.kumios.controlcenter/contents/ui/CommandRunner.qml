import QtQuick
import org.kde.plasma.plasma5support as Plasma5Support

// Runs a shell command through Plasma's executable engine and calls back with
// (exitCode, stdout, stderr). Identical commands in flight share one run.
Item {
    id: root
    visible: false
    property var callbacks: ({})

    function run(command, callback) {
        const pending = callbacks[command]
        if (pending) {
            pending.push(callback)
            return
        }
        callbacks[command] = [callback]
        executable.connectSource(command)
    }

    Plasma5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName, data) {
            disconnectSource(sourceName)
            const waiting = root.callbacks[sourceName] || []
            delete root.callbacks[sourceName]
            for (const callback of waiting)
                callback(Number(data["exit code"]), String(data.stdout || ""), String(data.stderr || ""))
        }
    }
}
