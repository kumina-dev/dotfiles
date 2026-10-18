# v0.2.0 verification — accepted with documented limitations

Audited 2026-10-18. This is the canonical repository evidence record for
**v0.2.0 — dependable everyday controls**. Git identifies the tested implementation;
Linear owns issue status and acceptance. Implementation checkpoint: `c937bc1`. Resume from `../SESSION_HANDOFF.md`.
Shared Linear index: https://linear.app/kumina/document/v020-verification-and-acceptance-68a1551a0eb3
Do not copy this report into every issue. Commands live in `README.md` here.

## Final acceptance — 2026-10-18

The user explicitly accepted KumiOS v0.2.0 using the successful automated tests,
simulated failure scenarios and normal desktop operation as sufficient milestone
evidence. KUM-9, KUM-10 and KUM-12 are Done with the limitations below; KUM-11
was already Done. This resolves the acceptance gate without claiming missing tests
passed. Historical pre-acceptance evidence remains below for traceability.

| Scenario reference | Unverified scenario | Traceability and accepted evidence |
| --- | --- | --- |
| V020-AUDIO-RESTART | Native KDE audio-backend restart/recovery | KUM-9; native read-only/client reconnect, user hotplug/default/control checks and legacy-service continuity passed. The legacy service is not the native backend. |
| V020-BT-HARDWARE | Physical Bluetooth adapter removal or hardware blocking | KUM-10; simulated no-adapter/blocked/removal/recovery and user reconnect/power checks passed. Physical removal/blocking and multi-adapter behavior are not claimed. |
| V020-LIVE-ERROR | Error notification/display and retry under a real live-shell failure | KUM-12; controlled offscreen popup and isolated D-Bus denial/timeout/retry passed. No real live-shell fault was induced or observed. |

These references remain **unverified**, explicitly accepted as milestone limitations,
not passed checks or unfinished acceptance gates. Any future investigation must cite
the relevant reference and issue; do not run disruptive tests merely to close them.

KUM-8 was reviewed separately: its existing criterion requires the user's report
that top bar, centered dock, unified launcher and saved pins persist across a voluntary
login/reboot. The earlier “Login/reboot check passed” report followed those criteria
and satisfies them; KUM-8 remains Done independently of this milestone acceptance.

Acceptance authorizes no Git tag, GitHub release, deployment, additional service
restart or v0.3.0 work. Source version remains `0.2.0-dev`; only local `v0.1.0` exists.

## Implementation and activation

| Outcome | Implementation | Linear |
| --- | --- | --- |
| Default-device audio, quick microphone mute, recovery | NativeAudio + AudioEndpoint; KDE plasma-pa/PulseAudioQt | KUM-9, Done (V020-AUDIO-RESTART) |
| Adapter/device-aware Bluetooth | BluezQt discovery/events; confirmed power changes | KUM-10, Done (V020-BT-HARDWARE) |
| Accurate Wi-Fi and active-app status | PlasmaNM wireless rows/decoded SSIDs; clear invalid active tasks | KUM-11, Done |
| Pending states and recoverable errors | ControlRequest + BackendChange; native settings recovery | KUM-12, Done (V020-LIVE-ERROR) |

Widget-only installation completed with private backup
`~/.config/kumios/layout-backup-6dinrdk1`. The user then explicitly approved a
Plasma shell restart. It succeeded; post-restart panel/widget identities, order
and Meta+Space binding matched the pre-restart inventory. No widget-loading errors
were observed at startup. KWin and audio services stayed active. The audit confirms
Plasma is running and installed widget files still match repository source.
**Activation and milestone acceptance are complete; release actions remain unauthorized.**

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
| Native audio probe | 4 checks passed; re-run at this checkpoint | Reads real default devices; only the test client's connection is reconnected and defaults recover. No daemon restart or device/mute/volume/routing writes |
| Native device probe | 4 checks passed; re-run at this checkpoint | Read-only BluezQt adapter and PlasmaNM wireless discovery; no scan, pairing or radio/network change |
| Offscreen popup probe | 3 checks passed; re-run at this checkpoint | Construction and default-font geometry (preferred height 358); not live scaling or worst-case error layout |
| Read-only preflight, installed-source comparison, whitespace checks | Passed at this checkpoint | Current dependencies/audio reachability, copied widget equality and diff hygiene |

Qt counts include suite lifecycle checks. Model/endpoint doubles do not prove
real hardware behavior. Transient native audio model warnings occurred while the
test client reconnected and then recovered. Offscreen PlasmoidItem hosting and
opaque/dynamic native types produce tooling warnings; no compile/test failures
were observed. Do not treat these warnings as verified user-facing defects.

## Manual evidence and unverified scenarios

Partial user acceptance recorded 2026-10-18: the user reported all three guided
checks passed: input/output labels agree with KDE Audio; output volume, output mute
and microphone mute agree with KDE; Tab navigation, slider arrow keys, tooltips,
Escape dismissal, popup fit and native settings links work. This covers current-session
audio and popup interaction; further physical evidence is recorded below.

The user also passed all three desktop/status checks on 2026-10-18: active-app
labels follow two applications and clear on showing the desktop; current Wi-Fi
name/status agrees with KDE; Meta+Space opens the usual dashboard and the top
bar/dock behave normally. Subsequent network/radio evidence is recorded below.

User passed the next three guided checks on 2026-10-18: audio unplug/replug and
KDE default switching with labels/controls following and recovering; spare Bluetooth
device reconnect with name/state updates and native settings accessible; brightness
adjustment/restoration without a stuck control. This does not establish Bluetooth
adapter changes, live error/retry presentation or actual audio-daemon restart recovery.

User then passed Wi-Fi off/on/reconnect with accurate status and no stuck controls,
and Bluetooth off/on with correct state and settings accessible on 2026-10-18.
KUM-11 is Done on combined automated, native and user task/network evidence.
Physical wired/VPN-only topology was conditional in the instructions and was not
separately identified in the user's reply; it is not claimed as independently tested.
Before final acceptance, KUM-9, KUM-10 and KUM-12 remained In Review for the
recovery/adapter/error limits below; the explicit decision above resolves that gate.

Resume audit on 2026-10-18 at source HEAD `bfb21cd`: all eight documented
suites/probes passed (82 checks including Qt lifecycle checks). Read-only preflight
passed, all 15 installed widget files matched source, and Plasma, KWin, PipeWire,
pipewire-pulse and WirePlumber were active. GitHub metadata and fetched Git agreed
on the repository; development HEAD matched the actual remote with 0/0 divergence.
No source changes, desktop restarts or live device writes were needed.

Hands-on sequence; report each group as pass, fail (with symptom), or untested.
Restore your original settings after intentional changes. Do device/network changes
only when they will not interrupt work; do not send device or network identifiers.

1. **KUM-9 / KUM-12 — audio and presentation:** open Control Center; compare input/
   output labels and mute states with KDE Audio settings. Make a small output-volume
   change, mute/unmute output and microphone, and verify KDE agrees after each.
   No microphone recording is required. Check Tab/Shift+Tab, slider arrow keys,
   tooltips, Escape dismissal and popup fit at your normal display scale. Confirm
   no stuck pending state and that settings links open the correct native page.
2. **KUM-11 — desktop/status:** switch between two applications, then show the
   desktop; confirm the active-app label follows the task and clears when none is
   valid. Check current Wi-Fi status against KDE. Confirm Meta+Space opens the usual
   dashboard and the top bar/dock still behave as expected.
3. **KUM-9–12 — hardware/transitions, when convenient:** unplug/replug an unused
   headset/microphone and change defaults in KDE; confirm names/controls recover.
   Reconnect a spare Bluetooth device and observe its name/state; test power only
   if no keyboard, pointer or active audio depends on it. Test Wi-Fi off/on or a
   network change only with a safe connection plan; verify wired/VPN alone is not
   labelled Wi-Fi. Move brightness slightly and restore it. For any naturally
   occurring error, check readable detail, native settings recovery and retry;
   do not manufacture a disruptive failure. Record unavailable hardware as untested.
4. **KUM-8 — passed:** user reported “Login/reboot check passed” on 2026-10-18
   after being given the layout/dashboard/dock/pins persistence criteria. This is
   user acceptance evidence for the normal session boundary, separate from probes.

Audio-daemon restart recovery needs a separately approved maintenance action and
remains untested. Missing physical/error scenarios remain open evidence gaps until
performed or explicitly resolved through an acceptance/scope decision.

- [x] Output volume/mute, input/output names and quick microphone mute (user passed).
- [x] Audio unplug/replug and changing defaults through KDE settings (user passed).
- [x] Bluetooth device-name/reconnect updates and native settings access (user passed).
- [x] Bluetooth power off/on, state updates and settings access (user passed).
- [ ] Bluetooth adapter removal/blocked states; multiple adapters need appropriate hardware.
- [x] Brightness adjustment/restoration without a stuck control (user passed).
- [x] Controlled offscreen pending/error/retry presentation (simulated; see follow-up).
- [ ] Live-shell error/retry observation remains unverified.
- [x] Popup sizing at the user's scale, keyboard controls, tooltips and settings links (user passed).
- [x] Launcher/top-bar/dock experience, active-app switching/clearing and current Wi-Fi status (user passed).
- [x] Wi-Fi off/on/reconnect status and no stuck controls (user passed).
- [ ] Actual audio-daemon restart recovery remains unverified; do not interrupt
      active audio to test it without explicit authorization.

[KUM-8](https://linear.app/kumina/issue/KUM-8) is **Done**: the user reported the
voluntary login/reboot layout/pin persistence check passed on 2026-10-18. It remains
outside this milestone. This user report supplies the evidence a shell restart or
automated test could not establish.
The user accepted releasing v0.1.0 before that check, not automatic acceptance of
v0.2.0. No new feature milestone should start before the current acceptance checkpoint.

## Controlled verification follow-up — 2026-10-18

The user authorized one restart of **only `kumi-audio.service`**, requested safe
simulated Bluetooth/fault-injection tests, and required a final acceptance summary
before any release-status change. That restart approval has been consumed.

| Verification | Evidence | Limit |
| --- | --- | --- |
| Legacy KumiOS audio service restart | Passed: passive `tst_LegacyAudioContinuity.qml` observer, 3 Qt checks including lifecycle, monitored native readiness and unchanged output/input names, output volume/mute and mic mute during one external `systemctl --user restart kumi-audio.service`. New legacy-service InvocationID; all six audited units active afterward. | NativeAudio stayed ready; it did not lose/recover its backend. The current controls do not use this legacy bridge. This is continuity/independence evidence, **not native audio-daemon restart recovery** or live-popup observation. |
| Protected services | PipeWire, pipewire-pulse, WirePlumber, Plasma and KWin InvocationIDs unchanged across the approved restart. | No restart of these services was performed or authorized. |
| Simulated Bluetooth states | Existing `tst_Bluetooth.qml`: 7 checks passed. New popup fault probe covers no adapter, blocked label/action, no write while blocked, removal during pending operation, ignored stale reply, restoration and successful retry. | Fake manager/bus, actual production popup bindings in a disposable instrumented copy. No physical removal, driver unload, rfkill or live Bluetooth write. Physical/multi-adapter behavior is not claimed. |
| Popup controlled errors/retry | `python3 tests/probes/run_control_fault_probe.py`: 6 checks passed. Audio withheld confirmation shows pending then timeout, authoritative unchanged volume, settings enabled, successful retry clears errors. Bluetooth long denial exposes full tooltip text with three-line display limit and retry clears it. Brightness denial shows an error without changing observed state; confirmed retry clears it. | Offscreen actual popup copy at width 320/default scale. Test aliases/object names expose internals; writers target doubles. No live-shell fault injection or new live visual acceptance. Existing offscreen hosting warnings persist without failures. |
| Typed private-bus denial/retry | `run_dbus_probe.py`: 5 checks passed. Denial and successful retry/reset now asserted within the same test, not inferred from a later case. | Real D-Bus marshalling against an isolated fake service, no actual policy failure induced. |

The first audio-observer attempt failed to compile because it used an absolute QML
import without a URL scheme; no restart ran in that attempt. The corrected observer
passed and the service was restarted exactly once. Initial popup visibility checks
failed because the offscreen test host was invisible; making only the test host
visible fixed the harness. No production source fix or widget installation was needed.

**Acceptance summary:** all requested safe simulated/error tests passed. The
approved legacy-service continuity check passed. Actual native backend restart
recovery remains **unverified**: testing it requires separate authorization for an
appropriate native audio-service interruption; the supplied approval expressly
excludes that. Physical adapter/blocked-state tests and live-shell fault observation
also remain unverified; simulations are not physical/user evidence. KUM-9, KUM-10
and KUM-12 were held In Review until the explicit acceptance decision above. The
three scenario references preserve the unverified evidence after closure. No release
status, tag, publication, desktop restart or v0.3.0 work is authorized here.

## Known constraints and next action

KDE's audio QML API is private and needs compatibility validation after KDE upgrades.
The legacy audio service remains installed for compatibility; new controls do not
use it. Setup updates the existing desktop rather than provisioning a fresh machine.
Physical audio hotplug/default recovery and Bluetooth reconnect have user evidence;
multi-adapter selection and daemon-restart recovery remain unverified.

Milestone accepted. Preserve the unverified scenario references and existing evidence.
No further disruptive testing is requested; await a separately authorized next task.
No release tag/publication/deployment or v0.3.0 work is authorized.
