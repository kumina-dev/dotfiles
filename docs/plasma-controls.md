# Plasma appearance and Control Center

Detailed behavior and prerequisites for the KumiOS Plasma appearance defaults and
Control Center widget. For setup, upgrade, recovery and acceptance, see the
[Plasma runbook](../plasma/README.md).

## Appearance: wallpaper accent and light/dark

Since 0.3.0 the KumiOS appearance is not a fixed dark palette. KDE supplies both
parts through maintained services:

- **Accent from the wallpaper.** KDE's accent color service derives the accent
  (selection, focus and highlights) from the current wallpaper and updates it when
  the wallpaper changes. KumiOS enables `accentColorFromWallpaper` in `kdeglobals`.
- **Light, Dark or Automatic.** Two appearance-only global themes,
  `org.kumios.light` and `org.kumios.dark` (`plasma/lookandfeel/`), select the
  Breeze Light or Breeze Dark color scheme, the matching Breeze icons and the
  KumiOS Plasma style. Automatic uses KDE's look-and-feel switcher with this pair.
  It follows KDE's day/night schedule (the KNightTime service, configured on the
  Day-Night Cycle settings page), which is separate from Night Light: Automatic
  works with Night Light off. When Automatic is chosen, KumiOS starts in the
  variant that schedule gives for now, or keeps the current one if no schedule
  is available. KDE may wait until the session is idle before switching at a
  transition (Global Theme settings). Choosing Light or Dark turns Automatic off.

The KumiOS Plasma style ships no palette of its own: the panel SVG draws with the
active color scheme's window background, so the top bar and dock follow light/dark
mode and the accent. Breeze's own global themes are not used for switching because
they also replace the wallpaper (and with it the accent) and the Plasma style; the
KumiOS themes contain no wallpaper, layout, cursor, decoration or splash settings.

GTK and libadwaita applications follow through KDE's GTK settings synchronization
and the desktop portal. KDE must own `~/.config/gtk-3.0` and `gtk-4.0`; if either
is a link to another configuration (as with the former Hyprland-era `gtk/` package,
whose fixed matugen colors overrode GTK), setup replaces it with an ordinary
directory and leaves the link target unchanged.

Change the mode from the Control Center's Appearance section (Light, Dark,
Automatic). It shows the applying state, confirms the change only when KDE's
settings report the chosen mode, and shows an inline error otherwise. If another
global theme is active, no mode is selected until one is chosen. It reads the
current state each time the popup opens, so changes made elsewhere appear there.

Set up the themes, or change the mode from a terminal, with `plasma/appearance.py`; see
[the runbook](../plasma/README.md#appearance). The mode can also be changed in
System Settings → Colors & Themes → Global Theme.

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
