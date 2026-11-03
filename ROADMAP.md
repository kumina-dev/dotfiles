# KumiOS roadmap

Goal: a cohesive KDE Plasma Wayland daily driver with minimal tinkering. Preserve
the top bar, centered dock, unified launcher and cohesive controls; integrate
maintained KDE components before building custom backends.

## Release scope

- **v0.1.0:** first Plasma daily driver, tagged `v0.1.0`. Scope and limits:
  [release notes](releases/0.1.0.md).
- **v0.2.0 — dependable everyday controls:** audio defaults/microphone/recovery,
  Bluetooth adapter/device state, truthful network/task labels and recoverable
  quick-control feedback. Accepted 2026-10-18 with explicit unverified limitations;
  tagged `v0.2.0` on 2026-11-03. Evidence: [verification](plasma/verification-0.2.0.md).
- **KUM-8:** layout and pinned-app persistence across login confirmed 2026-10-18.
- **v0.3.0 — wallpaper accent and light/dark appearance:** the accent follows the
  wallpaper and the user chooses Light, Dark or Automatic, replacing the hardcoded
  dark style. Accepted by the user 2026-11-03 in the live session; the Automatic
  schedule transition is not yet observed. Also in v0.3.0: upgrade safety for KDE's
  private audio API (KUM-23) and retiring the legacy audio service (KUM-24). On `kumios/adaptive-appearance`, not yet
  merged or tagged. Evidence: [verification](plasma/verification-0.3.0.md).

No GitHub release, new version tag or deployment is authorized. Ordinary validated
development-branch synchronization is authorized; follow AGENTS.md and report the
verified remote commit. Issue state and acceptance live in Linear.

## Deferred scope

Fresh-machine provisioning, broader visual redesign, login-stack replacement,
cloud calendars, custom device backends and legacy Hyprland utility expansion are
outside current scope. Login warnings warrant investigation only for real symptoms.

Optional, not a release gate: a deliberate multi-monitor panel layout (KUM-25).
It needs a second physical monitor to test, which is not available. Until then the
top bar and dock stay on their current screen and other screens use Plasma's defaults.

Start engineering work from [AGENTS.md](AGENTS.md) and the current
[handoff](SESSION_HANDOFF.md). Architecture/commands belong in the Plasma runbook;
completed behavior in the changelog/release notes; issue status and acceptance in
Linear. Revisit this roadmap when scope changes, not after each implementation command.
