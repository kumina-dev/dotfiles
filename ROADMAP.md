# KumiOS roadmap

Goal: a cohesive KDE Plasma Wayland daily driver with minimal tinkering. Preserve
the top bar, centered dock, unified launcher and cohesive controls; integrate
maintained KDE components before building custom backends.

## Release scope

- **v0.1.0:** created locally and accepted for current-session use. The user accepted
  release before the separate persistence check. Historical scope/limits:
  [release notes](releases/0.1.0.md). Keep this tag local.
- **v0.2.0 — dependable everyday controls:** audio defaults/microphone/recovery,
  Bluetooth adapter/device state, truthful network/task labels and recoverable
  quick-control feedback. Implemented and activated; acceptance pending. Current
  evidence/gates: [verification](plasma/verification-0.2.0.md); authoritative issue
  state is in Linear KUM-9–12, not duplicated as checkboxes here.
- **KUM-8:** remains separately pending the user's voluntary login/reboot layout
  and pinned-app persistence check. Never trigger or silently waive that check.

Do not start another feature milestone before resolving the current checkpoint
with the user. No v0.2.0 release action before acceptance and authorization.

## Deferred scope

Fresh-machine provisioning, broader visual redesign, login-stack replacement,
cloud calendars, custom device backends and legacy Hyprland utility expansion are
outside current scope. Login warnings warrant investigation only for real symptoms.

Start engineering work from [AGENTS.md](AGENTS.md) and the current
[handoff](SESSION_HANDOFF.md). Architecture/commands belong in the Plasma runbook;
completed behavior in the changelog/release notes; issue status and acceptance in
Linear. Revisit this roadmap when scope changes, not after each implementation command.
