# KumiOS Plasma daily driver

The supported first-release target is Arch Linux with KDE Plasma on Wayland.
Preserve the compact top bar, centered dock, one application dashboard and cohesive
quick controls. Reuse maintained KDE components for launching, window management,
notifications and detailed settings. The Hyprland/GTK implementation remains in
this repository as legacy material, not the Plasma release checklist.

## Layout and components

The top bar contains, in order: KumiOS system menu, KDE Application Dashboard,
active application, global application menu, spacer, KumiOS Control Center,
KDE clock, and KDE notifications. The bottom dock uses KDE's Icons-only Task Manager.
Panel click, Meta+Space and `plasma/scripts/kumios-launcher` target the same KDE
launcher. KRunner remains independently available through Alt+F2.

The custom presentation delegates Bluetooth devices to `kcm_bluetooth`, audio
output/input selection and microphone controls to `kcm_pulseaudio`, and About This
PC to `kcm_about-distro`, using KDE's KCMLauncher API. Output quick volume still
uses the existing KumiOS audio service; this iteration does not replace or expand it.
The display control and Wi-Fi implementation are retained.

## Read-only preflight

Run from the repository:

```sh
python3 plasma/setup.py --check
```

Default invocation is also read-only. Requires a running Plasma session, Python 3,
`qdbus6`, `kcmshell6`, installed native widgets/settings modules, and the existing
active `kumi-audio.service`. This is a layout reconciler for an existing KumiOS
installation, not a fresh-machine provisioning tool. It does not install packages,
change authentication or enable services. Custom widgets also require KDE's
`org.kde.kcmutils`, `org.kde.kirigami`, session-management and QML D-Bus modules;
Wi-Fi prerequisites are documented in the root README. Resolve missing dependencies
before applying; do not restart the desktop as part of preflight.

## Apply only after session approval

```sh
python3 plasma/setup.py --apply-layout
```

This is a visible live desktop change. Respect the session's authorization; the
user has authorized reversible live updates, while Plasma restarts, logout and
disruption of active work still require approval. It installs repository custom widgets and reconciles
panels through Plasma's supported scripting API; it does not restart Plasma,
log out, or run the appearance script. Existing widget instances can retain cached
code until a later voluntary login; do not claim new settings actions are live
merely because installation succeeded.

The script retains existing panels, desktop/wallpaper, task-manager instance and
pinned apps. It adds missing widgets and orders the essential top-bar widgets
before other personal widgets. Only the incompatible AppGrid widget is removed,
after creating KDE's Dashboard. AppGrid-specific configuration is preserved in the
backup but is not translated to KDE favorites. KDE's own favorite settings are retained.
Existing top/bottom panels are selected by location and known widget identity;
multiple matching panels or duplicate essential widgets stop the operation.
Other panels are left alone. The script targets the existing bar/dock's display;
new panels use Plasma defaults, not a prescribed multi-monitor layout.

Each apply saves a private directory under `$XDG_CONFIG_HOME/kumios/layout-backup-*`
(default `~/.config/kumios`). It contains the live layout export, widget inventory,
panel/shortcut config files, old installed custom widgets and an absence manifest.
The backup path is printed before installation. If application fails, stop and
inspect the printed error and backup; some live mutations may already have happened.

### Recovery

Do not overwrite panel config files while Plasma is running: its in-memory state
can overwrite them. Keep the printed backup and arrange an approved maintenance
window. After ending the graphical session, restore backed-up config files into
`$XDG_CONFIG_HOME` and backed-up widget directories into
`$XDG_DATA_HOME/plasma/plasmoids` (defaults `~/.config` and `~/.local/share`).
Use `absent.json` to identify files/packages introduced by this apply; remove them
only after reviewing for subsequent valuable changes. Log in normally afterwards.
`layout.js` also captures the live layout for investigation; do not blindly run it
on top of a running layout, which could duplicate panels. No automatic rollback,
logout or restart is performed.

## Verification

```sh
node --test tests/plasma-layout.test.cjs
python3 -m unittest discover -s tests -p test_plasma_setup.py
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software \
  /usr/lib/qt6/bin/qmltestrunner -input tests/qml -o -,txt
```

Layout tests cover repeated reconciliation, pin/panel retention, preflight failures,
ambiguous targets and failed launcher creation. They use API doubles; they do not
prove live rendering or Plasma shortcut activation. QML Wi-Fi tests mock network
operations. Node is only a test dependency, not a desktop runtime dependency.

Before a release tag, check on the desktop after an approved apply:

- Panel launcher, Meta+Space, search, favorites, Escape dismissal, and app launch.
- Alt+F2 fallback; Alt+Tab switching; Meta+arrow tiling; dock launch/pins/autohide.
- Top-bar order, global app menu support, popup size, focus and intended display scaling.
- Wi-Fi saved connection/retry; native authentication only on an approved test network.
- Bluetooth pairing/reconnect; output selection, microphone selection/mute, and headphone routing.
- About values, notification popup/history, Do Not Disturb and resuming notifications.
- At the next voluntary lock/login: unlock, launcher/pin persistence and secret prompts.

Do not investigate login keyring warnings unless they correspond to a real prompt,
lost secret, failed connection or another user-visible problem. For 0.1.0, the user
confirmed current-session checks and explicitly accepted releasing before next-login
layout/pin persistence verification. That check remains unverified under KUM-8;
see [release notes](../releases/0.1.0.md).

## Tracking

Workspace/team: Kumina / KUM. Each product has its own project:

- KumiOS: https://linear.app/kumina/project/kumios-83beb6551c62
- Tempo: https://linear.app/kumina/project/tempo-f51377d8898a
- TaisteluTanner: https://linear.app/kumina/project/taistelutanner-e7488b5d3e90
- Creator Alerts: https://linear.app/kumina/project/creator-alerts-a883cd12e695

KumiOS release work: KUM-5 reproducibility, KUM-6 launcher, KUM-7 native settings,
KUM-8 live acceptance. Source changes and automated checks can be ready for review
while deployment and hands-on verification remain outstanding.

API reference: https://develop.kde.org/docs/plasma/scripting/api/
