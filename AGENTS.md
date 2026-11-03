# KumiOS engineering guide

## Repository and architecture

Personal Arch Linux/KDE Plasma Wayland daily driver. Preserve the compact top bar,
centered dock, unified KDE Dashboard launcher and cohesive controls. Prefer maintained
KDE backends; retain custom presentation where useful. No new feature milestone
until the current acceptance checkpoint is resolved.

- `plasma/`: supported QML widgets, layout reconciliation and backed-up setup.
- `services/kumi-audio/`: legacy Python bridge; current controls use KDE audio.
- `hypr/`, GTK utilities and `greeter/`: legacy configuration; do not migrate,
  remove or change authentication just because those files exist.
- `tests/qml/`: mocked component/state tests; `tests/probes/`: explicit native or
  private-bus probes. Architecture decisions and validation commands: `plasma/README.md`.

## Authoritative state and resume

Git owns code, commits, branch/tag identity, actual worktree state and verified
remote synchronization. Linear
workspace **Kumina**, team **KUM**, project **KumiOS** owns scope/status/acceptance.
Each other product has its own project. Never substitute conversation history for
these records or assume a connector remains available.

Start each conversation:
1. Read `SESSION_HANDOFF.md`, then inspect `git status --short --branch`,
   `git log -3 --oneline`, `git tag --list`, `git branch -vv` and relevant diffs.
   Inspect sanitized remote URLs/upstream tracking, fetch without tags when reachable,
   and compare outgoing/divergent commits. Preserve unrelated edits.
2. Read the current shared verification report and relevant runbook sections only.
3. Read the current Linear milestone/issues/statuses. Reconcile discrepancies;
   do not silently mark missing evidence accepted. If Linear is inaccessible,
   continue safe local work and record the sync debt in the handoff.
4. Resume the next authorized action. Do not repeat established product/setup
   questions unless an actual conflict or new architectural fork requires it.

## Engineering and checkpoints

Use `rg`, Git, Bash, Python 3/unittest, Node's test runner, Qt **6** qmltestrunner/
qmllint, qdbus6, kcmshell6 and read-only systemctl/journalctl as applicable. Inspect
installed KDE types/docs for API compatibility; do not assume private QML APIs stable.
The Linear connector is preferred over raw tokens. Do not install tools speculatively.

Work in small independently testable units. Run relevant checks before completing
one; repeat broader checks only for a changed dependency, failure or checkpoint.
Commit coherent implementation + tests locally when stable, even if user acceptance
is pending. Name that state accurately; a checkpoint is not a release. Review the
staged diff and worktree, avoid `git add .`, and never include unrelated user edits.
Do not amend tags or rewrite shared history. Refresh the handoff at stable stops.

After each validated checkpoint, push its relevant development branch to the verified
configured remote and set upstream tracking if missing. A clean tree alone is not
completion. Before pushing, verify fetch/push URLs, target branch/refspec, worktree,
remote tip and outgoing commits; check repository automation so a routine push does
not trigger an unauthorized deployment or cost. Use an explicit branch refspec and
suppress implicit tag following. Do not silently push unrelated branches or tags.

A push to `main` is authorized only when validated, fast-forward and consistent with
branch-protection/review policies. Otherwise use the development branch and required
review flow; never bypass protection. Never force-push, rewrite published history or
delete remote branches without explicit approval. If the remote advances, fetch and
reconcile through ordinary history-preserving operations; do not force an update.

After pushing, query the actual remote branch (for example `git ls-remote`) and verify
it contains the expected commit; refresh tracking and check ahead/behind state. Report
both local HEAD and verified remote status. On auth/network/protection/divergence
failure, report the actual blocker and record sync debt in the handoff; do not claim
success or spin on retries. Avoid logging credentials from remote URLs.

Keep durable information in one place: runbook for commands/architecture, roadmap
for scope/deferred work, verification report for release evidence/manual gaps,
Linear for outcomes/acceptance, handoff for the resume snapshot. Update meaningful
state transitions, not every command. Add an ADR only for a substantial new decision.

## Linear workflow

Use existing statuses; do not change workspace workflow settings:
- Backlog: candidate scope; Todo: agreed but not started (including a deferred user check).
- In Progress: implementation/rework in motion.
- In Review: implemented and automated checks passed; review/manual acceptance pending.
- Done: outcome-specific evidence and required acceptance recorded.
No separate Blocked status exists: retain the accurate stage, state the blocker and
next unblock action, and use blocking relations when another issue is the cause.
Do not create a redundant issue merely to represent waiting for user acceptance.
Use milestones/shared verification documents for release gates; issue descriptions
contain focused acceptance criteria, test/source pointers and unique unresolved gaps.

## Authorization and safety

Routine reversible source/local changes, necessary dependencies, local branches,
commits, ordinary development pushes, local migration tests and agreed Linear work
are authorized. Reversible live widget-file updates are allowed with backups; prefer widget-only installation
for upgrades. Never reapply layout merely to update QML or claim file copy refreshed
cached widgets. Verify installed files separately from loaded behavior.

Ask before major scope/architecture changes, spending/recurring costs, production
changes, GitHub releases, production deployments, deleting valuable resources,
irreversible changes, Plasma/audio-service restarts, logout or disrupting active work. A one-time
restart approval is consumed by that action, not authorization for future restarts.
The v0.1.0 tag stays local; its source commits may be synchronized. No new v0.2.0
tag or GitHub release before user acceptance and release authorization. Ordinary
validated branch pushes do not require another approval. KUM-8 stays pending the
user's own-time persistence check.

Automated, isolated, read-only native, physical-device and user acceptance evidence
are distinct. Never infer one from another. Do not toggle radios, change default
routing/mute/volume, capture microphone audio or disconnect devices as a convenience
test during active work. Investigate login warnings only for a user-visible symptom.

Never store credentials, tokens, private keys, personal device/network identifiers,
schedules or sensitive configuration in Git, agent docs, handoffs or Linear. Private
runtime backups stay outside the repo. Avoid dumping environment values or raw logs;
store only sanitized findings and necessary paths. No automatic external messaging.
