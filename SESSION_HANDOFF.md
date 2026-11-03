# KumiOS session handoff

Snapshot: 2026-11-03 (v0.3.0 in progress). Read this index, then reconstruct live state from Git and
Linear; do not treat a previous conversation or this snapshot as a live database.

## Git checkpoint

- Project: KumiOS (`kumina-dev/dotfiles`), workspace/team Kumina / KUM.
- Milestone: **v0.3.0 — wallpaper accent and light/dark appearance**, accepted by the
  user on 2026-11-03. v0.2.0 is accepted (2026-10-18) and tagged.
- Active branch: `main`. `kumios/adaptive-appearance` was merged into `main` on
  2026-11-03 (merge `7d5ad50`).
- Implementation commits: `aed52c5` (KUM-20), `bc0b565` (KUM-21), `04b66fa` and
  `bd0b97d`/`ba53a02` (KUM-22), `fe09274` (KUM-23), `03c00ef` (KUM-24).
- Latest documentation checkpoint: the commit containing this handoff; resolve it
  with `git log -1 --format='%H %s' -- SESSION_HANDOFF.md`. Obtain actual latest
  HEAD with `git log -1 --oneline`; compare before resuming rather than recording
  an impossible self-referential commit hash inside its own file.
- Working tree: clean at completion of this checkpoint. Always recheck
  `git status --short --branch`; later local edits take precedence over this snapshot.
- Release tags: `v0.1.0` at `b197802` and `v0.2.0` (2026-11-03), both published
  on GitHub. Source version is `0.3.0` (not tagged). No GitHub releases exist;
  creating one or a new version tag requires explicit release authorization.
- Remote target: `origin` = `https://github.com/kumina-dev/dotfiles.git`, branch
  `main`. Verify synchronization after pushing: `git fetch --no-tags origin`, then
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

## v0.3.0 state

| Issues | State | Notes |
| --- | --- | --- |
| KUM-20 | Done | Adaptive Plasma style; user passed V030-STYLE |
| KUM-21 | Done | appearance.py, KumiOS Light/Dark themes, accent, KDE-owned GTK; user passed V030-ACCENT/GTK/PRESERVED |
| KUM-22 | Done | Control Center modes; button highlight fixed in `bd0b97d`; user passed V030-MODES/EXTERNAL |
| KUM-23 | Done | Private KDE audio API isolation and upgrade check (`fe09274`); loaded after an approved restart; user confirmed audio controls work |
| KUM-24 | Done | Legacy `kumi-audio.service` retired: stopped, disabled, unlinked and removed from the repo; KDE audio verified unaffected; its venv deleted at the user's request |
| KUM-25 | Backlog (optional) | Deliberate multi-monitor layout; needs a second monitor; not a release gate |

User accepted the live result on 2026-11-03. V030-AUTO's schedule transition is
unverified (Automatic selection passed). Decisions: KDE services provide the accent
and the light/dark switch; KumiOS ships appearance-only Light/Dark global themes
because Breeze's replace the wallpaper and Plasma style; KDE owns
`~/.config/gtk-3.0`/`gtk-4.0` (user decision); the legacy `gtk/` package is
unchanged. Evidence: `plasma/verification-0.3.0.md`.

## Next authorized action

v0.3.0 is accepted, merged into `main` and versioned 0.3.0 (2026-11-03), but not
tagged or released. A `v0.3.0` tag and any GitHub release each need the user's
instruction. The merged `kumios/adaptive-appearance` branch still exists locally and
on GitHub. All four approved Plasma restarts are consumed. Record the V030-AUTO
transition when the user observes one. v0.2.0's three unverified limitations
remain as recorded.
