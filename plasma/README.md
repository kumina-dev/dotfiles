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
PC to `kcm_about-distro`, using KDE's KCMLauncher API. Unreleased 0.2.0 controls
use KDE's plasma-pa audio context and live default devices directly, including quick
microphone mute; they no longer depend on the custom KumiOS audio service. The old
service remains installed for legacy compatibility and is not automatically disabled.
BluezQt supplies adapters and device events. See [0.2.0 verification](verification-0.2.0.md).

## Read-only preflight

Run from the repository:

```sh
python3 plasma/setup.py --check
```

Default invocation is also read-only. Requires a running Plasma session, Python 3,
`qdbus6`, `kcmshell6`, `pactl`, Qt's `qtpaths6` runtime tool, installed native
widgets/settings modules, plasma-pa and BluezQt QML modules, and a reachable audio
backend. This is a layout reconciler for an existing KumiOS
installation, not a fresh-machine provisioning tool. It does not install packages,
change authentication or enable services. Custom widgets also require KDE's
`org.kde.kcmutils`, `org.kde.kirigami`, session-management and QML D-Bus modules;
Wi-Fi prerequisites are documented in the root README. Resolve missing dependencies
before applying; do not restart the desktop as part of preflight.

## Upgrade widget files without reapplying layout

```sh
python3 plasma/setup.py --install-widgets
```

This backs up and copies the custom widgets only. It does not change panel layout
or restart Plasma. QML may remain cached until an explicitly approved shell restart
or normal login. Current 0.2.0 verification and outstanding manual checks are in
[verification-0.2.0.md](verification-0.2.0.md).

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

## Architecture decisions

- KDE owns device discovery, audio client reconnection, window management and
  detailed settings. QML retains KumiOS presentation rather than adding services.
- `NativeAudio` binds KDE plasma-pa defaults; `AudioEndpoint` observes confirmation
  and invalidates pending writes when the target disappears/changes. The private
  KDE audio API is a compatibility risk checked against the installed version.
- `BluetoothControl` consumes BluezQt adapter/device signals; `WiFiStatus` consumes
  PlasmaNM wireless rows and decoded SSIDs instead of global wired/VPN state.
- `ControlRequest` and `BackendChange` bound waits and reject stale replies. D-Bus
  acceptance alone is not success: observed state must agree. Timeout does not undo
  an operation. Wi-Fi connection/cancel/forget state remains in `WiFiConnection`.
- Layout reconciliation preserves panel/task-manager identity and pins. Widget-only
  upgrades copy files with backups and do not reapply layout. Cached code requires
  explicit activation; restarting Plasma is not a login/persistence test.
- Native secrets agents keep credentials out of widget arguments/state. The old
  audio service/Hyprland utilities remain for compatibility, not new expansion.

## Additional validation tools

Use the standard suites above for implementation checkpoints. Optional probes are
separate: never run the entire probes directory because DBusRoundTrip needs its
private service. With the same Qt 6/offscreen flags, invoke one file at a time:

- `tests/probes/tst_NativeAudio.qml`: reads defaults and reconnects only its test
  client; no audio-daemon restart, recording or routing writes.
- `tests/probes/tst_NativeDevices.qml`: reads adapters/wireless rows without scans.
- `tests/probes/tst_ControlCenter.qml`: offscreen construction/geometry, not visual acceptance.
- `python3 tests/probes/run_dbus_probe.py`: starts a private dbus-run-session fake
  service to check typed roundtrips and errors; needs system PyGObject.

Use Qt 6 `qmllint` on changed QML and interpret opaque native/dynamic-model warnings
alongside compile/runtime evidence. Run `git diff --check` before staging, then
`git diff --cached --check` and inspect the staged diff before committing. After a
validated checkpoint, push the relevant branch under the Git policy in AGENTS.md,
verify the actual remote tip/upstream relation, and report both local and remote
state. A clean working tree alone does not complete a checkpoint. Shell pipelines
that report test results must enable `set -o pipefail`.

## Engineering state

Read `../AGENTS.md` for conventions and approval boundaries and
`../SESSION_HANDOFF.md` for the current resume snapshot. The roadmap owns future
scope; `verification-0.2.0.md` owns this milestone's evidence/manual gaps. Linear
Kumina / KUM / KumiOS owns issue status; each other product uses its own project.
Avoid repeating that state in this runbook.

API reference: https://develop.kde.org/docs/plasma/scripting/api/
