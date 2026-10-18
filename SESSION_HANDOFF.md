# KumiOS session handoff

Snapshot: 2026-10-18. Read this index, then reconstruct live state from Git and
Linear; do not treat a previous conversation or this snapshot as a live database.

## Git checkpoint

- Project: KumiOS (`kumina-dev/dotfiles`), workspace/team Kumina / KUM.
- Milestone: **v0.2.0 — dependable everyday controls**; no next feature milestone.
- Active branch: `kumios/dependable-controls`.
- Implementation commit: `c937bc10d74f39579adbc1226f7a98dbb9a2a181`.
- Latest documentation checkpoint: the commit containing this handoff; resolve it
  with `git log -1 --format='%H %s' -- SESSION_HANDOFF.md`. Obtain actual latest
  HEAD with `git log -1 --oneline`; compare before resuming rather than recording
  an impossible self-referential commit hash inside its own file.
- Working tree: clean at completion of this checkpoint. Always recheck
  `git status --short --branch`; later local edits take precedence over this snapshot.
- Only release tag: local `v0.1.0` at `b197802`. Source version is `0.2.0-dev`.
  Neither checkpoint is a release approval. Nothing pushed/published.

## Linear and acceptance

| Issues | State at handoff | Remaining outcome |
| --- | --- | --- |
| KUM-5–7 | Done | v0.1.0 outcomes accepted; no reimplementation |
| KUM-8 | Todo, outside v0.2.0 | User's later voluntary login/reboot layout/pin check; unverified |
| KUM-9–12 | In Review | Implemented, automatically checked, installed and activated; user/manual acceptance pending |

[Project](https://linear.app/kumina/project/kumios-83beb6551c62).
Shared Linear verification index:
https://linear.app/kumina/document/v020-verification-and-acceptance-68a1551a0eb3
Read issue-specific acceptance criteria in Linear. No implementation blocker is
known; remaining gates are manual evidence/user acceptance, not a failed build.
If the connector is unavailable, record sync debt here and continue safe local
inspection; never guess issue completion or request pasted credentials.

## Architecture and constraints

See `plasma/README.md` for decision rationale and commands. KDE supplies audio
Context/default devices, BluezQt events, PlasmaNM wireless state and native settings;
custom QML supplies the agreed presentation and confirmed-request/error behavior.
The private KDE audio API needs compatibility checks after KDE upgrades. Layout
source is unchanged by v0.2.0. Legacy services/configuration remain for compatibility.
No new architecture, authentication migration or provisioning work is approved here.

## Verified state and manual gaps

Canonical evidence: `plasma/verification-0.2.0.md` (includes test scopes/limits).
At this checkpoint, standard QML 57, Node 5, Python 4 and private-bus 5 checks
passed again; preflight, installed-source equality and Git whitespace checks pass.
Earlier native audio-client reconnect/device-read/offscreen probes passed; those
were not repeated merely to change documentation.

The prior explicitly approved Plasma restart succeeded. Post-restart inventory
preserved panel/widget identities, order and launcher shortcut; no widget-load
errors were observed. This audit read current shell/audio health without another
restart. Activation is complete, not pending. Widget files match source.

Still unverified: live v0.2.0 output/mic/keyboard/popup acceptance, physical device
hotplug/default switches, Bluetooth reconnect/adapters, radio/brightness transitions,
and audio-daemon restart recovery. KUM-8's full-session persistence check is separate.
Automated mocks and test-client reconnect do not prove those behaviors.

## Next authorized action

Collect the user's v0.2.0 manual results when ready; the shared report lists the
short checklist. Fix observed regressions only, validate affected units, make local
checkpoint commits, and update the relevant issue plus shared evidence once per
meaningful transition. Do not start a new feature milestone or force KUM-8.

Approval boundaries and resume procedure are in `AGENTS.md`. No further desktop/
audio restart, logout, disruptive device test, release tag, push or publication is
authorized by this handoff. Routine reversible source/docs work remains authorized.
