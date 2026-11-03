# v0.3.0 verification — wallpaper accent and light/dark appearance

Canonical repository evidence record for **v0.3.0**. Git identifies the tested
implementation; Linear (milestone "v0.3.0 — wallpaper accent and light/dark
appearance", KUM-20–22) owns issue status and acceptance. Commands live in
[README.md](README.md#appearance). Resume from `../SESSION_HANDOFF.md`.

Status 2026-11-03: **accepted by the user in the live session**, with one check
not yet observed (V030-AUTO schedule transition; see below). KUM-20–22 Done.

## Scope

- KUM-20: the KumiOS Plasma style follows the active color scheme and accent.
- KUM-21: appearance-only KumiOS Light/Dark global themes, wallpaper accent and
  `plasma/appearance.py` setup; KDE owns the GTK settings directories (user
  decision 2026-11-03).
- KUM-22: Light / Dark / Automatic choice in the Control Center.
- KUM-23 (added 2026-11-03): upgrade safety for KDE's private audio API.

## Automated evidence (branch `kumios/adaptive-appearance`)

| Check | Scope | Result |
| --- | --- | --- |
| `tests/test_desktoptheme.py` | No fixed palette; stylesheet; all 28 visible panel parts use `ColorScheme-Background`; frame ids; version | 5 pass; 31 failures against the previous theme |
| `tests/probes/run_panel_render_probe.py` | KSvg renders the panel offscreen under Breeze Light/Dark (private sessions) | Light fill (240,240,241) vs (239,240,241); Dark (33,35,40) vs (32,35,38); 78% opacity |
| `tests/test_appearance_setup.py` | Mocked: mode choice, manual vs automatic, accent/pair writes, verification, private backup, stale-file replacement, GTK handover, appearance-only theme packages | 13 pass |
| `tests/probes/run_appearance_probe.py` | Real `plasma-apply-lookandfeel`/`kwriteconfig6` in a private D-Bus session with temporary XDG dirs: every mode | 39 checks pass: colors, automatic flag, accent kept, wallpaper/layout file byte-identical, KumiOS style kept, legacy GTK package untouched |
| `tests/qml/tst_Appearance.qml` | Mocked runner: observation, each choice, confirmation only on observed state, failure, timeout, stale reply, missing themes, external change | 9 pass |
| Live read-only check `python3 plasma/appearance.py` | KDE services present; reports live state | Passed: dark, automatic off, default global theme, wallpaper accent off, GTK linked to legacy package |

Standard suites at the KUM-22 checkpoint: Python, Node layout, Qt 6 QML (66) and
the construction and fault-injection probes pass. Exact counts are in each commit.

Known limits of the automated evidence: the isolated probe has no kded services,
so it cannot show the accent service recomputing from a wallpaper, the automatic
switcher acting at a schedule transition, or GTK regeneration. The QML tests use a
fake runner, so they cannot prove the live popup's commands. Those belong to the
manual checks below.

## Automatic starting variant: KNightTime instead of Night Light (2026-11-03)

User question: does Automatic need Night Light enabled? KDE's switcher
(`lookandfeelautoswitcher`, plasma-workspace 6.8.2) links `libKNightTime` and reads
`KDarkLightScheduleProvider`. KWin's Night Light plugin and the Day-Night Cycle
settings page (`kcm_nighttime`) use the same KNightTime schedule. So KDE's switching
does not need Night Light. KumiOS, however, chose Automatic's starting variant from
KWin Night Light's `daylight` property, which need not follow the schedule when
Night Light is off. Fixed: the Control Center (`NightTime.js`) and `appearance.py`
read KNightTime's schedule (one Subscribe, immediately Unsubscribed). They use the
same rule: day from mid-morning to mid-evening transition, otherwise night, or
unknown outside the schedule, which keeps the current variant.

Evidence: `tests/test_nighttime_rule.py` (11 cases, Python and the JS rule under
Node agree; single subscribe/unsubscribe; unavailable service gives unknown);
`tst_Appearance.qml` 12 (schedule read before apply, day/night/unavailable
schedule, late schedule reply ignored). A live read-only Subscribe/Unsubscribe
returned a 7–8 day dynamic schedule that agreed with Night Light (both day). User
check 2026-11-03 after loading the fix: "Automatic works, even with Night Light
off" (the user turned Night Light off themselves).
Loaded by a fourth explicitly approved Plasma restart (consumed): service active
with a new InvocationID, no KumiOS widget errors, top bar 8 and dock 1 widgets.

## KUM-23 automated evidence

| Check | Scope | Result |
| --- | --- | --- |
| `tests/test_audio_api.py` | qmltypes parser and contract check: compatible fixture; removed type, renamed property/method/enum/value, lost singleton, removed inherited device property, read-only device property, changed device type; truncated file; report wording; QML guard lists equal the contract; only `NativeAudio.qml` imports the private module | 10 pass; installed plasma-pa 6.8.2 module passes |
| `tests/qml/tst_AudioBackend.qml` | Loader with fixtures: missing module, outdated API, compatible pass-through, reload; device with a renamed member is neither read nor written | 7 pass |
| `tests/probes/run_audio_isolation_probe.py` | Real popup offscreen with NativeAudio replaced by a missing-module import | Loads, audio reported unavailable with KDE's reason, other controls present; control (old direct import) fails to load |
| `tst_NativeAudio.qml::test_installedModuleMeetsContract` | Installed KDE module against the runtime guard (read-only) | Pass |
| `python3 plasma/audio_api.py`, `setup.py --check` | Live read-only | "KDE audio API compatible (plasma-pa 6.8.2)" |

Not exercised: an actual KDE release that changes the module. The behavior is
simulated with fixtures and a replaced `NativeAudio.qml`.

Live load: widget files installed (backed up), then a third explicitly approved
Plasma restart (consumed) on 2026-11-03: service active with a new InvocationID,
no KumiOS widget errors (including AudioBackend/NativeAudio) in its journal, and the
top bar (8) and dock (1) widgets unchanged. User check 2026-11-03 ("Everything
checks out"): volume, output mute, microphone mute and device names work as before,
with no incompatibility message. KUM-23 Done.

## Live setup — 2026-11-03 (user approved)

- `python3 plasma/appearance.py --apply current` succeeded and verified itself:
  `org.kumios.dark`, automatic off, wallpaper accent on. Independent read-back:
  KDE computed `AccentColor=129,95,175`; Plasma style KumiOS; installed style has
  no `colors` file; `~/.config/gtk-3.0`/`gtk-4.0` are KDE-managed directories with
  regenerated files; the repository (legacy `gtk/`) stayed clean; the wallpaper/layout
  file was not modified (last change predates the run). Backup kept privately
  under `~/.config/kumios/appearance-backup-*`.
- `python3 plasma/setup.py --install-widgets` succeeded; all three installed widgets
  match source. No layout change or Plasma restart. The running shell keeps cached
  Control Center code until a later login or an approved restart, so the Appearance
  section is not yet visible.
- Plasma restart, explicitly approved by the user 2026-11-03 (approval consumed):
  `plasma-plasmashell.service` returned active with a new InvocationID; no KumiOS
  widget errors in its journal since the restart; top bar and dock kept all their
  widgets. The new Control Center code is loaded for the manual checks.
- User manual check: all worked except the selected mode button not staying visibly
  selected (KDE's desktop style draws checked only on checkable buttons). Fixed in
  `bd0b97d`, widget files reinstalled, and a second explicitly approved Plasma restart
  (consumed) loaded it: service active with a new InvocationID, no KumiOS widget
  errors, top bar 8 and dock 1 widgets as before.

## Manual acceptance — 2026-11-03

The user tested the live session after the second restart and reported: "The
button stay as selected now, everything works!" (earlier: "Everything seems to
work except the button doesn't seem to stay visibly as selected", since fixed).

| Reference | Check | Result |
| --- | --- | --- |
| V030-STYLE | Top bar and dock follow Light and Dark, keeping their translucency and shape | Passed (user) |
| V030-ACCENT | Changing the wallpaper changes the accent in Plasma and Qt apps | Passed (user) |
| V030-MODES | Control Center Light, Dark and Automatic apply, show the applying state and end with the chosen button selected | Passed after `bd0b97d` (user) |
| V030-EXTERNAL | A System Settings Global Theme change shows when the popup reopens | Passed (user) |
| V030-GTK | GTK apps follow Light/Dark and the accent | Passed (user) |
| V030-PRESERVED | Wallpaper, panels, dock pins and shortcuts unchanged | Passed (user); panel widget counts unchanged after both restarts |
| V030-AUTO | Automatic starts in the right variant; a day/night schedule transition switches it | Selecting Automatic passed (user), including with Night Light off after `ba53a02`. **The transition itself is unverified**: no dusk/dawn switch has been observed. Record the result when it happens; do not force a transition to close it. |
