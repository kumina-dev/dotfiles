# v0.3.0 verification — wallpaper accent and light/dark appearance

Canonical repository evidence record for **v0.3.0**. Git identifies the tested
implementation; Linear (milestone "v0.3.0 — wallpaper accent and light/dark
appearance", KUM-20–22) owns issue status and acceptance. Commands live in
[README.md](README.md#appearance). Resume from `../SESSION_HANDOFF.md`.

Status 2026-11-03: **implemented; automated evidence passes; applied to the live
session with user approval; manual acceptance pending.** Nothing below is a user acceptance.

## Scope

- KUM-20: the KumiOS Plasma style follows the active color scheme and accent.
- KUM-21: appearance-only KumiOS Light/Dark global themes, wallpaper accent and
  `plasma/appearance.py` setup; KDE owns the GTK settings directories (user
  decision 2026-11-03).
- KUM-22: Light / Dark / Automatic choice in the Control Center.

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

## Manual acceptance (pending)

Live setup and the approved restart are done (above); all checks can now run.

| Reference | Check |
| --- | --- |
| V030-STYLE | Top bar and dock follow Light and Dark, keeping their translucency and shape. |
| V030-ACCENT | Changing the wallpaper changes the accent (selection, focus, highlights) in Plasma and Qt apps. |
| V030-MODES | Control Center Light, Dark and Automatic each apply, show the applying state, and end with the chosen button selected. |
| V030-AUTO | Automatic matches the current day/night state; a schedule transition switches it (may be observed later). |
| V030-EXTERNAL | A change in System Settings → Global Theme shows correctly when the popup reopens. |
| V030-GTK | A GTK app (and a libadwaita app, if installed) follows Light/Dark and the accent. |
| V030-PRESERVED | Wallpaper, panels, dock pins and shortcuts are unchanged after setup and each mode change. |
