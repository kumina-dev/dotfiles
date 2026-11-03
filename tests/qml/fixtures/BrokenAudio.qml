import QtQuick
// Simulates a KDE release that removed the private audio module.
import org.kde.plasma.private.volume.removedInFutureRelease as PulseAudio

QtObject {
    property var output: PulseAudio.Server.defaultSink
}
