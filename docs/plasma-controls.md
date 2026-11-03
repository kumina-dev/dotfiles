# Plasma appearance and Control Center

Detailed behavior and prerequisites for the KumiOS Plasma appearance defaults and
Control Center widget. For setup, upgrade, recovery and acceptance, see the
[Plasma runbook](../plasma/README.md).

## Plasma appearance defaults

The current KumiOS Plasma design uses its custom desktop style with Breeze Dark
application colors. Apply the same appearance on this desktop or a future Plasma
6 installation from a terminal in the logged-in desktop session:

```sh
~/dotfiles/plasma/apply-defaults.sh
```

Requires Plasma's `plasma-apply-colorscheme`, `plasma-apply-desktoptheme`,
`kwriteconfig6`, Python 3, and the Breeze Dark color scheme/GTK theme. The command
installs the repository's KumiOS desktop style, applies Breeze Dark, and sets GTK
3/4 and (when available) GNOME/libadwaita dark preferences. Reopening an application
may be necessary. Applications with their own appearance settings may need those
settings adjusted separately.

Each run prints a backup directory under `~/.config/kumios/appearance-backup-*`
(or `$XDG_CONFIG_HOME/kumios`). It saves the previous KDE and GTK settings and the
previous installed KumiOS style. GNOME appearance preferences are recorded there
when available. Restore the saved config files to their original locations and
reapply the previous color scheme to revert.

This command preserves the current panels, dock, wallpaper, shortcuts, and display
configuration. It applies appearance defaults to the user running it; run it once
for each new user after Plasma is installed. It does not provision a complete
Plasma desktop or automatically seed system-wide accounts. The existing panel
layout sources are in `plasma/shell/`; `layout-v2.js` reconciles panels in place. Use the backed-up setup command
documented in [plasma/README.md](../plasma/README.md), after approving the live change.

## Plasma Control Center

The Plasma widget sources are in `plasma/plasmoids/org.kumios.controlcenter`.
Its Wi-Fi detail page filters out wired, bridge, loopback, and VPN entries before
layout and sorts wireless networks by signal strength. Active connections have
a checkmark. Opening the page or pressing Refresh requests a scan; the list is
hidden when Wi-Fi is off and shows an empty/scanning message when appropriate.

Click an available network to connect. Saved profiles are reused; new open and
personal Wi-Fi networks are added through NetworkManager. Plasma's native secrets
agent requests passwords, keeping credentials out of widget state and command
arguments. Initial enterprise/certificate setup belongs in Plasma Network Settings;
after a profile is saved it can be selected here.

The page shows connection progress, prevents duplicate requests, and offers Cancel.
Success follows the active connection's state, rather than just accepting a request.
Backend request errors and failed/cancelled authentication are shown inline, with
NetworkManager reasons for missing passwords, authentication timeouts, unreachable
access points, and address configuration failures. Cancellation waits for the
active connection to stop before reporting completion. A slow
request shows a warning after 90 seconds and remains cancellable. NetworkManager
may save a new profile even if activation fails or is cancelled; use Forget to
remove an unwanted saved profile. A connected state does not imply Internet reachability.

The active network's disconnect icon disconnects its Wi-Fi adapter without turning
the radio off or forgetting the saved profile. It waits for the adapter to become
disconnected and reports errors inline. NetworkManager's device-level Disconnect
prevents an immediate automatic reconnect; select a network to connect again.
Concurrent connection, disconnect, and Forget requests are blocked while an operation
is pending.

Saved wireless rows have a Forget icon, including profiles outside scan range.
An inline confirmation replaces the list until you choose Cancel or Forget. It
identifies the selected profile, explains removal of its saved password, and warns
that an active connection may be interrupted. Cancel, leaving the Wi-Fi page, or
turning the radio off dismisses the confirmation without deleting anything.
Forgetting a profile does not hide an access point that is still being broadcast;
it becomes an available network again. Other profiles for the same SSID are retained.

The confirmation keeps a copy of the selected profile's identity through scan/model
changes. Before deletion the widget rechecks the UUID and wireless profile type
using GetSettings, which excludes secrets. Errors, including authorization failures
and profiles removed elsewhere, are shown inline. A timeout tells you to check the
current saved state before retrying; it does not claim the deletion was undone.

Requires Plasma Network Management, KDE's `org.kde.kitemmodels` and
`org.kde.plasma.plasma5support` QML modules, `gdbus` (GLib), and the running Plasma
NetworkManager secrets agent. New-profile creation uses `gdbus` because Plasma's
QML D-Bus encoder currently marshals nested settings dictionaries as `a{sv}` instead
of NetworkManager's required `a{sa{sv}}`. Device and access-point arguments are shell
quoted. Saved-profile activation, cancellation, and deletion use the QML D-Bus API directly.

The installed widget is a separate copy. Use the backed-up widget-only upgrade and
validation commands in [the Plasma runbook](../plasma/README.md). A Plasma restart
requires explicit approval; file installation alone does not refresh cached QML.

The tests use mock connection requests and scan handlers. Live desktop check:
verify only wireless entries appear, connect to a saved network, try a new personal
network's password dialog, cancel authentication, and retry after an error. Check
that progress and the connected checkmark follow the actual NetworkManager state.
Use the disconnect icon on an active row, confirm the radio stays on, then select
that saved network to reconnect.

Verified in a live Plasma session on 2026-10-18 using the installed Wi-Fi components:
saved-profile disconnect/reconnect, cancellation of an activation followed by retry,
native password-dialog cancellation followed by saved-profile recovery, and a
successful fresh-profile connection after entering the password in Plasma. The
original saved connection was restored and temporary test profiles were removed.
An earlier fresh-profile attempt failed association; that failure prompted the
more specific NetworkManager error messages.
Forget verification on 2026-10-18 used a disposable profile with autoconnect disabled:
confirmation cancellation, deletion through the real NetworkManager API, and removal
from saved settings were checked without deleting an existing user profile. The QML
suite also checks denied requests, profile identity changes, timeouts, and retries.

These steps may switch the active network; use a network you can safely test.
