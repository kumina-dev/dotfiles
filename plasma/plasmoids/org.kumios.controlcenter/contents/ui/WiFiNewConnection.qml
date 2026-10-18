import QtQuick
import org.kde.plasma.plasma5support as Plasma5Support

// Plasma's QML D-Bus encoder cannot marshal a{sa{sv}} on Plasma 6. Use
// GDBus for this one method; authentication stays with Plasma's secrets agent.
Item {
    id: root
    visible: false
    property var requests: ({})
    signal finished(int requestId, string activePath, string error)

    function quote(value) {
        return "'" + String(value).replace(/'/g, "'\\''") + "'"
    }

    function start(device, accessPoint, requestId) {
        const command = "gdbus call --system --dest org.freedesktop.NetworkManager"
            + " --object-path /org/freedesktop/NetworkManager"
            + " --method org.freedesktop.NetworkManager.AddAndActivateConnection '{}' "
            + quote(device) + " " + quote(accessPoint)
        requests[command] = requestId
        executable.connectSource(command)
    }

    function processResult(command, data) {
        const serial = requests[command]
        delete requests[command]
        if (serial === undefined) {
            return
        }
        if (data["exit code"] !== 0) {
            finished(serial, "/", String(data.stderr || "NetworkManager rejected the connection request.").trim())
            return
        }
        // GDBus prints a tuple of the profile path followed by the active path.
        const paths = /^\(objectpath '[^']+', objectpath '(\/org\/freedesktop\/NetworkManager\/ActiveConnection\/[0-9]+)'\)\s*$/.exec(String(data.stdout))
        if (!paths) {
            finished(serial, "/", "NetworkManager returned an unexpected connection result.")
            return
        }
        finished(serial, paths[1], "")
    }

    Plasma5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName, data) {
            disconnectSource(sourceName)
            root.processResult(sourceName, data)
        }
    }
}
