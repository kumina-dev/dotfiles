.pragma library

// KDE's day/night schedule (KNightTime, org.kde.NightTime) is what the automatic
// light/dark switcher follows. It is independent of Night Light being enabled.
// Same rule as plasma/appearance.py's is_daytime(); tests share fixtures.

// One subscription read: subscribe, release the subscription, print the reply.
var readCommand =
    "out=$(gdbus call --session --dest org.kde.NightTime --object-path /org/kde/NightTime/Manager"
    + " --method org.kde.NightTime.Manager.Subscribe '{}') || exit 1;"
    + " cookie=$(printf %s \"$out\" | grep -oE \"'Cookie': <uint32 [0-9]+\" | grep -oE '[0-9]+$');"
    + " [ -n \"$cookie\" ] && gdbus call --session --dest org.kde.NightTime --object-path /org/kde/NightTime/Manager"
    + " --method org.kde.NightTime.Manager.Unsubscribe \"$cookie\" >/dev/null;"
    + " printf %s \"$out\""

// Entries of (noon, morning-start, morning-end, evening-start, evening-end) in ms.
function entries(reply) {
    var text = String(reply).replace(/int64 /g, "")
    var pattern = /\((-?\d+), (-?\d+), (-?\d+), (-?\d+), (-?\d+)\)/g
    var found = []
    var match
    while ((match = pattern.exec(text)) !== null)
        found.push(match.slice(1).map(Number))
    return found
}

// true (day), false (night) or undefined (no usable schedule). Day runs from the
// middle of the morning transition to the middle of the evening transition.
function isDaytime(reply, nowMs) {
    var days = entries(reply)
    if (days.length === 0) return undefined
    for (var i = 0; i < days.length; ++i) {
        var d = days[i]
        if ((d[1] + d[2]) / 2 <= nowMs && nowMs < (d[3] + d[4]) / 2) return true
    }
    if (days[0][1] <= nowMs && nowMs < days[days.length - 1][4]) return false
    return undefined
}
