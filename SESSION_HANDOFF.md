# KumiOS session handoff

Snapshot: 2026-11-03 (v0.3.0 in progress). Read this index, then reconstruct live state from Git and
Linear; do not treat a previous conversation or this snapshot as a live database.

## Git checkpoint

- Project: KumiOS (`kumina-dev/dotfiles`), workspace/team Kumina / KUM.
- Milestone: **v0.3.0 — wallpaper accent and light/dark appearance**, authorized by
  the user on 2026-11-03. v0.2.0 is accepted (2026-10-18) and tagged.
- Active branch: `kumios/adaptive-appearance` (from `main` at `e4a34e3`), tracking
  `origin/kumios/adaptive-appearance`. Not merged into `main`.
- Implementation commits: `aed52c5` (KUM-20), `bc0b565` (KUM-21), `04b66fa` (KUM-22).
- Latest documentation checkpoint: the commit containing this handoff; resolve it
  with `git log -1 --format='%H %s' -- SESSION_HANDOFF.md`. Obtain actual latest
  HEAD with `git log -1 --oneline`; compare before resuming rather than recording
  an impossible self-referential commit hash inside its own file.
- Working tree: clean at completion of this checkpoint. Always recheck
  `git status --short --branch`; later local edits take precedence over this snapshot.
- Release tags: `v0.1.0` at `b197802` and `v0.2.0` (2026-11-03), both published
  on GitHub. Source version is `0.3.0-dev`. No GitHub releases exist; creating one or a
  new version tag requires explicit release authorization.
- Remote target: `origin` = `https://github.com/kumina-dev/dotfiles.git`, branch
  `kumios/adaptive-appearance`. Verify synchronization after pushing: `git fetch --no-tags origin`, then
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
The private KDE audio API needs compatibility checks after KDE upgrades. Layout
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

## v0.3.0 state

| Issues | State | Remaining outcome |
| --- | --- | --- |
| KUM-20 | In Review | Live visual check of the adaptive Plasma style |
| KUM-21 | In Review | Live `appearance.py --apply`; accent and GTK checks |
| KUM-22 | In Review | Live Control Center mode switching |

Decisions: KDE services provide the accent (`accentColorFromWallpaper`) and the
light/dark switch (look-and-feel auto-switcher). KumiOS ships appearance-only
Light/Dark global themes because Breeze's replace the wallpaper and Plasma style.
KDE owns `~/.config/gtk-3.0`/`gtk-4.0` (user decision 2026-11-03); the legacy `gtk/`
package stays unchanged. Evidence and manual checks: `plasma/verification-0.3.0.md`.

## Next authorized action

Live setup ran with user approval on 2026-11-03 (`appearance.py --apply current`,
`setup.py --install-widgets`; see the verification report). The new Control Center
section needs a later login or an explicitly approved Plasma restart. Run the V030
manual checks with the user and record results in the
verification report and Linear. No GitHub release, version tag, deployment or
Plasma restart is authorized without separate approval. v0.2.0's three unverified
limitations remain as recorded; do not run disruptive tests to close them.
