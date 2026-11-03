# KumiOS session handoff

Snapshot: 2026-11-03 (v0.3.0 in progress). Read this index, then reconstruct live state from Git and
Linear; do not treat a previous conversation or this snapshot as a live database.

## Git checkpoint

- Project: KumiOS (`kumina-dev/dotfiles`), workspace/team Kumina / KUM.
- Milestone: **v0.4.0 — Plasma-only main, Hyprland preserved on a branch**,
  authorized by the user on 2026-11-03. v0.3.0 is accepted and tagged.
- Active branch: `kumios/plasma-only` (from `main` at `v0.3.0`). `legacy/hyprland`
  preserves the Hyprland-era tree. v0.3.0's branch was merged (`7d5ad50`) and deleted.
- Implementation commits: `aed52c5` (KUM-20), `bc0b565` (KUM-21), `04b66fa` and
  `bd0b97d`/`ba53a02` (KUM-22), `fe09274` (KUM-23), `03c00ef` (KUM-24).
- Latest documentation checkpoint: the commit containing this handoff; resolve it
  with `git log -1 --format='%H %s' -- SESSION_HANDOFF.md`. Obtain actual latest
  HEAD with `git log -1 --oneline`; compare before resuming rather than recording
  an impossible self-referential commit hash inside its own file.
- Working tree: clean at completion of this checkpoint. Always recheck
  `git status --short --branch`; later local edits take precedence over this snapshot.
- Release tags: `v0.1.0` at `b197802`, `v0.2.0` and `v0.3.0` (both 2026-11-03), all
  published on GitHub. Source version is `0.4.0-dev` (root `VERSION`). No GitHub releases exist; creating
  one or a new version tag requires explicit release authorization.
- Remote target: `origin` = `https://github.com/kumina-dev/dotfiles.git`, branch
  `kumios/plasma-only`. Verify synchronization after pushing: `git fetch --no-tags origin`, then
  `git rev-list --left-right --count HEAD...@{upstream}` must be `0 0`.
  A clean worktree is insufficient; rerun these commands rather than trusting a
  stale snapshot.

## Linear and acceptance

| Issues | State at handoff | Remaining outcome |
| --- | --- | --- |
| KUM-5–7 | Done | v0.1.0 outcomes accepted; no reimplementation |
| KUM-8 | Done, outside v0.2.0 | User reported login/reboot persistence check passed on 2026-10-18 |
| KUM-11 | Done | User task/current-network/radio checks passed; automated mixed-state evidence retained |
| KUM-9, KUM-10, KUM-12 | Done | Explicitly accepted with V020-AUDIO-RESTART / V020-BT-HARDWARE / V020-LIVE-ERROR unverified |

[Project](https://linear.app/kumina/project/kumios-83beb6551c62).
Shared Linear verification index:
https://linear.app/kumina/document/v020-verification-and-acceptance-68a1551a0eb3
Read issue-specific acceptance criteria in Linear. No implementation blocker is
known. Final user acceptance is recorded; unverified scenarios are limitations,
not passed tests. KUM-8 was separately reviewed and its existing user-report
criterion is satisfied by the earlier voluntary login/reboot pass.
If the connector is unavailable, record sync debt here and continue safe local
inspection; never guess issue completion or request pasted credentials.

## Architecture and constraints

See `plasma/README.md` for decision rationale and commands. KDE supplies audio
Context/default devices, BluezQt events, PlasmaNM wireless state and native settings;
custom QML supplies the agreed presentation and confirmed-request/error behavior.
The private KDE audio API is isolated and checked (KUM-23): after KDE upgrades run
`python3 plasma/audio_api.py` (see the runbook). Layout
source is unchanged by v0.2.0. Legacy services/configuration remain for compatibility.
No new architecture, authentication migration or provisioning work is approved here.

## Verified state and manual gaps

Canonical evidence: `plasma/verification-0.2.0.md` (includes test scopes/limits).
At this checkpoint, standard QML 57, Node 5, Python 4 and private-bus 5 checks
passed again; preflight, installed-source equality and Git whitespace checks pass.
Native audio-client reconnect/device-read/offscreen probes also passed in the
autonomous resume audit (82 total suite/probe checks). All 15 installed widget files
match source; Plasma/KWin/audio services are active. The verification report now
contains the evidence sequence and explicit final user acceptance; no unverified
scenario has been reclassified as passed.

The prior explicitly approved Plasma restart succeeded. Post-restart inventory
preserved panel/widget identities, order and launcher shortcut; no widget-load
errors were observed. This audit read current shell/audio health without another
restart. Activation is complete, not pending. Widget files match source.

User passed live output/mic labels and controls, keyboard/popup/tooltips/settings
links on 2026-10-18. User also passed active-app switching/clearing, current Wi-Fi
status against KDE, Meta+Space dashboard and top-bar/dock behavior.
User also passed audio unplug/replug/default switching and recovery, Bluetooth
reconnect/name/state/settings access, and brightness adjustment/restoration.
User passed Wi-Fi off/on/reconnect and Bluetooth power/state/settings checks.
KUM-11 is Done. Still unverified: Bluetooth adapter removal/blocked states,
live-shell error/retry observation and actual native audio-daemon restart recovery.
Controlled follow-up: Bluetooth suite 7, popup fault probe 6 and private-bus 5 checks
passed. One explicitly approved kumi-audio.service restart passed a passive native
continuity observer (3 checks); the five protected native audio/desktop service
InvocationIDs stayed unchanged. Legacy-service independence is not backend restart
recovery. Approval is consumed; no other restart is authorized. See the canonical
report for exact scopes and harness limitations.
KUM-8's separate full-session persistence check
was reported passed by the user on 2026-10-18.
Automated mocks and test-client reconnect do not prove those behaviors.

## v0.4.0 state

Branch `kumios/plasma-only` (from `main` at `v0.3.0`). `legacy/hyprland` (pushed)
preserves the complete Hyprland-era tree at v0.3.0 with history.

| Issue | State | Notes |
| --- | --- | --- |
| KUM-26 | In Progress | Hyprland-era code removed from this branch; `VERSION` at root; the 6 Hyprland session links were retired with a backup (`~/.config/kumios/hyprland-links-backup-*`, including ignored generated files such as monitors.lua) |
| KUM-27 | In Review | kitty config in `plasma/kitty/` with Breeze-generated Light/Dark themes; `~/.config/kitty` repointed (old target and matugen colors.conf in the backup) |
| KUM-28 | In Review | ReGreet theme in `plasma/greeter/` with KDE colors/accent/wallpaper and Light/Dark; restored `test_greeter_setup.py` (wrongly removed with the legacy tests, then adapted) |
| KUM-29 | In Review | Installed by the user 2026-11-03 (greetd now starts ReGreet on KWin; verified read-only). Backup: `/etc/greetd/kumios-backup.xsQDDA`. Pending: the user's logout/login test |
| KUM-25 | Backlog (optional) | Multi-monitor layout; needs a second monitor |

v0.3.0 is tagged and accepted; its open items (V030-AUTO transition, real KDE audio
API change) remain as recorded in `plasma/verification-0.3.0.md`.

## Next authorized action

Continue v0.4.0: finish KUM-26 docs/tests, then KUM-27, KUM-28 and KUM-29 in that
order. The greeter switch (KUM-29) needs a nested KWin pre-check, a backup of
`/etc/greetd`, the user's own sudo, documented TTY recovery and a logout/login test.
Never change greetd/PAM authentication. No GitHub release, version tag or Plasma
restart without the user's instruction.
