# KumiOS first-release roadmap

Target: a cohesive KDE Plasma Wayland daily driver with minimal tinkering.
Keep the top bar, centered dock, unified launcher and custom quick-control
presentation. Prefer maintained KDE components and native detailed settings.

## Current release

- [x] Inspect source and active desktop; record functional gaps.
- [x] Create separate product projects in Linear; prioritize KumiOS.
- [x] Implement in-place layout reconciliation with dock-pin/panel retention.
- [x] Add read-only preflight and explicit application with private backups.
- [x] Prepare maintained KDE Dashboard and unified launcher shortcut/helper.
- [x] Connect custom Bluetooth, audio/microphone and About controls to KDE settings.
- [x] Test reconciliation and failure boundaries without touching live panels.
- [x] Apply prepared changes with user approval, preserving live panel and task-manager identities.
- [x] User confirmed current-session desktop acceptance after approved Plasma restart.
- [ ] Verify persistence at the next voluntary login; investigate login warnings
      only if they affect actual use.
- [x] Prepare local 0.1.0 release commit and annotated v0.1.0 tag; no external publication.

## Deferred

- Broader redesigns, a replacement login stack, cloud calendar integration,
  custom device-management backends and legacy Hyprland utility expansion.
- Bluetooth adapter discovery beyond the current hardcoded hci0 quick toggle;
  native device settings remain the intended detailed-management surface.
- Fresh-machine package/service provisioning: this release's setup utility
  reconciles the existing desktop and requires its audio service to be available.

KUM-5 through KUM-8 track the release. Automated success does not substitute for
live checks. Reversible live updates are authorized. No logout, Plasma restart or disruption of active work without user approval.

Release decision: user accepts releasing before next-login layout/pin persistence
verification. KUM-5–7 accepted; KUM-8 tracks only the deferred persistence check.
