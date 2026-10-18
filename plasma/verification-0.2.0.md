# v0.2.0 verification — awaiting user acceptance

Audited 2026-10-18. This is the canonical repository evidence record for
**v0.2.0 — dependable everyday controls**. Git identifies the tested implementation;
Linear owns issue status and acceptance. Implementation checkpoint: `c937bc1`. Resume from `../SESSION_HANDOFF.md`.
Shared Linear index: https://linear.app/kumina/document/v020-verification-and-acceptance-68a1551a0eb3
Do not copy this report into every issue. Commands live in `README.md` here.

## Implementation and activation

| Outcome | Implementation | Linear |
| --- | --- | --- |
| Default-device audio, quick microphone mute, recovery | NativeAudio + AudioEndpoint; KDE plasma-pa/PulseAudioQt | KUM-9, In Review |
| Adapter/device-aware Bluetooth | BluezQt discovery/events; confirmed power changes | KUM-10, In Review |
| Accurate Wi-Fi and active-app status | PlasmaNM wireless rows/decoded SSIDs; clear invalid active tasks | KUM-11, In Review |
| Pending states and recoverable errors | ControlRequest + BackendChange; native settings recovery | KUM-12, In Review |

Widget-only installation completed with private backup
`~/.config/kumios/layout-backup-6dinrdk1`. The user then explicitly approved a
Plasma shell restart. It succeeded; post-restart panel/widget identities, order
and Meta+Space binding matched the pre-restart inventory. No widget-loading errors
were observed at startup. KWin and audio services stayed active. The audit confirms
Plasma is running and installed widget files still match repository source.
**Activation is complete; final v0.2.0 acceptance is not.**

Only the local `v0.1.0` tag exists. No new release tag, GitHub release or deployment
is authorized. Validated development-branch pushes are authorized and required at
checkpoints; remote synchronization is separate from manual/release acceptance.

## Evidence and limits

| Validation | Result | What it establishes |
| --- | --- | --- |
| Standard QML suite | 57 checks passed; re-run at this checkpoint | Endpoint/default changes, unavailable/recovered states, confirmation, clamping, duplicate/late replies, simulated Bluetooth changes, mixed network states, Unicode SSIDs, invalid tasks, existing Wi-Fi operations and compilation |
| Node layout suite | 5 passed; re-run | Reconciliation/failure behavior with API doubles; not physical persistence |
| Python setup suite | 4 passed; re-run | Preflight boundaries, backups and widget-only installation without layout evaluation |
| Private D-Bus probe | 5 checks passed; re-run | Actual `(ssv)` boolean and `(iu)` brightness marshalling, observed-state notifications and permission errors on a fake private service |
| Native audio probe | 4 checks passed during implementation | Reads real default devices; only the test client's connection is reconnected and defaults recover. No daemon restart or device/mute/volume/routing writes |
| Native device probe | 4 checks passed during implementation | Read-only BluezQt adapter and PlasmaNM wireless discovery; no scan, pairing or radio/network change |
| Offscreen popup probe | 3 checks passed during implementation | Construction and default-font geometry (preferred height 358); not live scaling or worst-case error layout |
| Read-only preflight, installed-source comparison, whitespace checks | Passed at this checkpoint | Current dependencies/audio reachability, copied widget equality and diff hygiene |

Qt counts include suite lifecycle checks. Model/endpoint doubles do not prove
real hardware behavior. Transient native audio model warnings occurred while the
test client reconnected and then recovered. Offscreen PlasmoidItem hosting and
opaque/dynamic native types produce tooling warnings; no compile/test failures
were observed. Do not treat these warnings as verified user-facing defects.

## Outstanding manual checks

No user acceptance of the activated v0.2.0 controls has been recorded yet.

- [ ] Output volume/mute, input/output names and quick microphone mute.
- [ ] Headset/microphone unplug/replug and changing defaults through KDE settings.
- [ ] Bluetooth device-name/reconnect updates; adapter removal/power changes only
      when convenient. Multiple adapters require appropriate hardware.
- [ ] Wi-Fi radio/network changes, brightness, and pending/error presentation.
- [ ] Popup sizing at the user's scale, keyboard controls, tooltips and unchanged
      launcher/top-bar/dock experience.
- [ ] Actual audio-daemon restart recovery remains unverified; do not interrupt
      active audio to test it without explicit authorization.

[KUM-8](https://linear.app/kumina/issue/KUM-8) remains **Todo**, pending only the
user's later layout/pin persistence check across a voluntary login/reboot. It is
outside this milestone; a shell restart or automated test does not complete it.
The user accepted releasing v0.1.0 before that check, not automatic acceptance of
v0.2.0. No new feature milestone should start before the current acceptance checkpoint.

## Known constraints and next action

KDE's audio QML API is private and needs compatibility validation after KDE upgrades.
The legacy audio service remains installed for compatibility; new controls do not
use it. Setup updates the existing desktop rather than provisioning a fresh machine.
Tests have not established multi-adapter selection or physical recovery reliability.

Next: collect the outstanding manual results when the user is ready; fix only
observed regressions, revalidate affected units, and request acceptance before any
v0.2.0 release action. Do not restart the desktop or trigger KUM-8 for this purpose.
