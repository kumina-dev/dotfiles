# KumiOS Plasma daily driver

The supported first-release target is Arch Linux with KDE Plasma on Wayland.
Preserve the compact top bar, centered dock, one application dashboard and cohesive
quick controls. Reuse maintained KDE components for launching, window management,
notifications and detailed settings. The Hyprland/GTK implementation is not on
`main`; it is preserved on the `legacy/hyprland` branch.

## Layout and components

The top bar contains, in order: KumiOS system menu, KDE Application Dashboard,
active application, global application menu, spacer, KumiOS Control Center,
KDE clock, and KDE notifications. The bottom dock uses KDE's Icons-only Task Manager.
Panel click, Meta+Space and `plasma/scripts/kumios-launcher` target the same KDE
launcher. KRunner remains independently available through Alt+F2.

The custom presentation delegates Bluetooth devices to `kcm_bluetooth`, audio
output/input selection and microphone controls to `kcm_pulseaudio`, and About This
PC to `kcm_about-distro`, using KDE's KCMLauncher API. The 0.2.0 controls
use KDE's plasma-pa audio context and live default devices directly, including quick
microphone mute; they no longer depend on the custom KumiOS audio service, which was
retired in 0.3.0 (KUM-24: stopped, disabled and removed from the repository).
BluezQt supplies adapters and device events. See [0.2.0 verification](verification-0.2.0.md).
The 0.3.0 Control Center adds Light / Dark / Automatic appearance and links to
`kcm_lookandfeel`; the accent follows the wallpaper. See [Appearance](#appearance).

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
Wi-Fi prerequisites are documented in [docs/plasma-controls.md](../docs/plasma-controls.md). Resolve missing dependencies
before applying; do not restart the desktop as part of preflight.

## Upgrade widget files without reapplying layout

```sh
python3 plasma/setup.py --install-widgets
```

This backs up and copies the custom widgets only. It does not change panel layout
or restart Plasma. QML may remain cached until an explicitly approved shell restart
or normal login. 0.2.0 verification evidence and accepted limitations are in
[verification-0.2.0.md](verification-0.2.0.md).

## Apply only after session approval

```sh
python3 plasma/setup.py --apply-layout
```

This is a visible live desktop change. Respect the session's authorization; the
user has authorized reversible live updates, while Plasma restarts, logout and
disruption of active work still require approval. It installs repository custom widgets and reconciles
panels through Plasma's supported scripting API; it does not restart Plasma,
log out, or change appearance (see [Appearance](#appearance)). Existing widget instances can retain cached
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

## Appearance

The accent follows the wallpaper, and the user chooses Light, Dark or Automatic.
Background and design: [docs/plasma-controls.md](../docs/plasma-controls.md#appearance-wallpaper-accent-and-lightdark).

```sh
python3 plasma/appearance.py                 # read-only check and current state
python3 plasma/appearance.py --apply current # set up, keeping the current light/dark
python3 plasma/appearance.py --apply light   # or dark, or auto
```

`--apply` changes the live appearance, so obtain session approval first. It
requires the running KDE accent, look-and-feel switcher and GTK sync services
(the check verifies them), then:

1. Saves a private backup under `$XDG_CONFIG_HOME/kumios/appearance-backup-*`:
   `kdeglobals`, `plasmarc`, their `kdedefaults/` copies, real GTK directories,
   `gtk-links.json` (previous GTK symlink targets), the previously installed KumiOS
   style and themes, and `absent.json`.
2. Installs the KumiOS Plasma style and `org.kumios.light`/`org.kumios.dark`,
   replacing the installed copies (so files removed from the source do not linger).
3. Replaces `~/.config/gtk-3.0`/`gtk-4.0` symlinks with KDE-managed directories,
   carrying over KDE's generated `settings.ini`/`colors.css`. Link targets are not modified.
4. Enables the wallpaper accent, registers the KumiOS light/dark pair and applies the mode.
5. Reads the result back; a mismatch is reported as a failure, not success.

It never changes the wallpaper or panels and never restarts Plasma. Applications
that cache colors may need reopening. The Plasma style and themes apply to the
running shell immediately; the accent updates the next time KDE evaluates the
wallpaper (for example after a wallpaper change).

### Lock screen

The lock screen is KDE's own (kscreenlocker); its UI comes from Plasma's shell and
is not replaced. It follows Light/Dark and the wallpaper accent through the KumiOS
Plasma style and color scheme. Its wallpaper is set to the desktop's and kept in sync:

```sh
python3 plasma/lockscreen.py                # read-only status
python3 plasma/lockscreen.py install-sync   # back up kscreenlockerrc, sync, keep in sync
python3 plasma/lockscreen.py remove-sync    # stop syncing (current wallpaper stays)
```

`install-sync` adds the user units `kumios-lockscreen-sync.path` and `.service`,
which re-run `lockscreen.py sync` when `plasma-org.kde.plasma.desktop-appletsrc`
(wallpaper) or `kdeglobals` (Light/Dark, which selects a wallpaper package's dark
image) changes. Syncing only writes when the wallpaper differs. The backup is in
`~/.config/kumios/lockscreen-backup-*`. It never locks the session; check the
result by locking (Meta+L).

### Security key unlock

A touch of the registered security key unlocks the lock screen; the password
always works too. kscreenlocker runs the PAM service `kde-smartcard` in parallel
with the password service `kde`. KumiOS overrides only that service with
`plasma/pam/kde-smartcard` (touch-only `pam_u2f`, the same options as sudo and
greetd use here):

```sh
python3 plasma/security_key.py           # read-only status and readiness
python3 plasma/security_key.py install   # back up and install (your sudo)
python3 plasma/security_key.py remove    # KDE's vendor kde-smartcard applies again
```

The stack accepts only a key touch (no password module), keeps `faillock preauth`
so a password-locked account stays locked, and has no `authfail`, so a missing or
untouched key never counts towards a lockout. The lock screen's own hint reads
"(or scan your smartcard)". Touch only means possession of the key unlocks.
`tests/probes/run_lockscreen_unlock_probe.py` checks a key touch in kscreenlocker's
testing greeter under a virtual KWin, without locking the session.

### Login greeter

The login screen is greetd + ReGreet, started on KWin and themed from KDE (colors,
wallpaper accent, current wallpaper, Light/Dark). Preview, install, restore and TTY
recovery: [greeter/README.md](greeter/README.md). `install-sync` keeps the theme in sync with the
desktop through a sandboxed root service that reads your files only as you. The install uses the user's sudo and
takes effect at the next logout or reboot.

### kitty terminal

`~/.config/kitty` links to `plasma/kitty/`. `kitty.conf` holds only font, opacity
and padding; colors come from `light-theme.auto.conf`, `dark-theme.auto.conf` and
`no-preference-theme.auto.conf`, which kitty (0.38 or later) switches between when
KDE's light/dark preference changes. Install or repair the link with
`ln -sfn ../dotfiles/plasma/kitty ~/.config/kitty`. After a KDE update that changes
Breeze, run `python3 plasma/kitty_theme.py --check`, then `python3 plasma/kitty_theme.py`
to regenerate the themes if they are out of date.

### Appearance recovery

Copy the backed-up `kdeglobals`/`plasmarc` (and `kdedefaults/` files) back into
`$XDG_CONFIG_HOME`; restore a GTK link with `ln -sfn <target> ~/.config/gtk-3.0`
after moving the new directory aside, using `gtk-links.json`. Then reapply the
previous scheme, for example `plasma-apply-colorscheme BreezeDark`, or choose a
global theme in System Settings. The previous KumiOS style is in the backup's
`plasma/desktoptheme/KumiOS`.

## After a KDE upgrade

The Control Center's audio controls depend on KDE's private
`org.kde.plasma.private.volume` module (plasma-pa). After upgrading KDE, run:

```sh
python3 plasma/audio_api.py
```

It reads the installed module's type description (read-only) and checks every
type, property, method and enum value in `plasma/audio-api-contract.json`.
`setup.py` runs the same check during preflight and prints a warning, without
blocking, when it fails. Results:

- **Compatible, same version:** nothing to do.
- **Compatible, newer version:** it asks for a recheck. Confirm volume, output
  mute, microphone mute and device names in the Control Center, then update
  `verified_with` in the contract.
- **Incompatible:** it lists each removed or renamed member. The Control Center
  still loads; its audio section explains the problem and links to Devices &
  Microphone (`kcm_pulseaudio`). Adapt `NativeAudio.qml`/`AudioEndpoint.qml` and
  the contract together, then rerun the tests and this check.

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
layout/pin persistence verification. The user later reported that check passed and
KUM-8 is Done; see [release notes](../releases/0.1.0.md).

## Architecture decisions

- KDE owns device discovery, audio client reconnection, window management and
  detailed settings. QML retains KumiOS presentation rather than adding services.
- `NativeAudio` binds KDE plasma-pa defaults; `AudioEndpoint` observes confirmation
  and invalidates pending writes when the target disappears/changes. The private
  KDE audio API can change in any KDE release, so only `NativeAudio.qml` imports it
  and `AudioBackend` loads it at runtime: an incompatible module disables the audio
  controls (pointing to Sound settings) instead of the whole Control Center. A
  runtime member check and `audio_api.py` both use `audio-api-contract.json`.
- `BluetoothControl` consumes BluezQt adapter/device signals; `WiFiStatus` consumes
  PlasmaNM wireless rows and decoded SSIDs instead of global wired/VPN state.
- `ControlRequest` and `BackendChange` bound waits and reject stale replies. D-Bus
  acceptance alone is not success: observed state must agree. Timeout does not undo
  an operation. Wi-Fi connection/cancel/forget state remains in `WiFiConnection`.
- Layout reconciliation preserves panel/task-manager identity and pins. Widget-only
  upgrades copy files with backups and do not reapply layout. Cached code requires
  explicit activation; restarting Plasma is not a login/persistence test.
- Appearance uses KDE's wallpaper accent service and look-and-feel switcher.
  KumiOS ships appearance-only Light/Dark global themes because Breeze's replace the
  wallpaper and Plasma style. The Plasma style has no palette; KDE owns GTK settings.
- Native secrets agents keep credentials out of widget arguments/state. The legacy
  audio service was retired in 0.3.0, and the Hyprland-era code left `main` in
  0.4.0 (branch `legacy/hyprland`).

## Additional validation tools

Use the standard suites above for implementation checkpoints. Optional probes are
separate: never run the entire probes directory because DBusRoundTrip needs its
private service. With the same Qt 6/offscreen flags, invoke one file at a time:

- `tests/probes/tst_NativeAudio.qml`: reads defaults and reconnects only its test
  client; no audio-daemon restart, recording or routing writes.
- `tests/probes/tst_NativeDevices.qml`: reads adapters/wireless rows without scans.
- `tests/probes/tst_ControlCenter.qml`: offscreen construction/geometry, not visual acceptance.
- `python3 tests/probes/run_control_fault_probe.py`: copies the production popup
  into a temporary directory and adds test-only aliases/object names. Injects fake
  audio writers, a fake Bluetooth manager/bus and brightness replies; verifies
  actual popup pending/error labels, full tooltip text and retry clearing. No
  installed-widget changes, service restarts or device writes. Run via the Python
  wrapper only; the QML file needs the disposable `ui/` copy.
- `python3 tests/probes/run_panel_render_probe.py`: renders the KumiOS panel SVG
  offscreen with KDE's SVG engine under Breeze Light and Breeze Dark, in private
  D-Bus sessions with temporary config. It checks the panel takes each scheme's window
  background at its designed translucency; it does not read or change live appearance.
- `python3 tests/probes/run_appearance_probe.py`: runs `appearance.py`'s backup,
  install, GTK handover and every `--apply` mode with the real KDE tools in a private
  D-Bus session with temporary HOME/XDG directories. Checks colors, automatic mode,
  accent, wallpaper/layout file, Plasma style and the linked GTK target. Skips the
  kded preflight, which needs the live session; does not read or change live appearance.
- `python3 tests/probes/run_audio_isolation_probe.py`: copies the production widget,
  replaces `NativeAudio.qml` with one importing a missing module, and constructs the
  real popup offscreen. It must load with audio reported unavailable and other
  controls present. As a control, the same break with the old direct `NativeAudio`
  instantiation must fail to load. Touches no installed files or devices.
- `tests/probes/tst_NativeAudio.qml` also checks that the installed KDE module meets
  the runtime contract (`test_installedModuleMeetsContract`, read-only).
- `python3 tests/probes/run_greeter_kwin_probe.py`: runs ReGreet's demo with the KumiOS
  theme under a virtual KWin in a private D-Bus session (temporary HOME/XDG) and checks
  that the window maps, is fullscreen, covers the output and stays up. It does not use
  greetd, PAM, `/etc` or the live session, and cannot exercise DRM or the greeter account.
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
