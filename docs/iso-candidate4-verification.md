# Aven ISO verification — candidate 4

**Rejected for release:** candidate 4's original preview closed on Enter or its
Open button without launching the associated application on the installed Wayland
session. Media, public installation, first-user setup, Places and read-only
Atomic/font checks passed before that failure. The later single-file runtime
repair is debug evidence only and does not make this ISO accepted.

## Artifact identity

| Field | Exact value |
|---|---|
| Image | `Aven-Atomic-KDE-44-0.1.0-prototype-x86_64.iso` |
| Bytes | `7,890,075,648` |
| SHA-256 | `f3f1a37faf9aee5665c953843ffdcb23ae21ed5f96d00c698234f791e36c9eb4` |
| Source commit | `ca020b9bf2b8704c9214f9b88af1a689982a0aea` |
| Source state | Clean; all 146 embedded files match the build manifest |
| Fedora base | `44.20260913.0` |
| Base commit | `be803f3e3bcdcc54885264702655e6e071864504154bc46044a08cc2aa2ce5df` |
| Local layered commit | `37fc46fea2b1059cdbc35c4ff88a2b40ede7fcc105cca76693f11cc4cdffd551` |

The Fedora parent is signed; the locally generated layer is distinct and is not
Fedora-signed. This is an Anaconda installer, not a live desktop. Its public
Kickstart retains native storage choices and Fedora's native first-user setup.

## Current evidence

| Check | Result | Evidence / attribution |
|---|---|---|
| Complete ISO hash, ISO9660, BIOS/UEFI boot structures | Pass | Independent [media audit](../evidence/verification/iso-candidate4/media-audit.json) |
| Offline ref and commit objects, embedded source | Pass | Same audit: exact layer/base object hashes, archive repository, all 146 files |
| Public Kickstart defaults | Pass | Same audit and source review: no lab user/key, automatic erase, automatic login or passwordless sudo |
| Actual BIOS optical boot | Pass | Integrator operated firmware; [native welcome](../evidence/verification/iso-candidate4/bios-installer-welcome.png) independently inspected at original resolution; [hash and attribution](../evidence/verification/iso-candidate4/installer-screenshot-inspection.json) |
| Actual UEFI optical boot | Pass | Integrator operated firmware; [native welcome](../evidence/verification/iso-candidate4/uefi-installer-welcome.png) independently inspected |
| Public installation on a fresh disk | Complete in Anaconda | Native offline workflow, no private test Kickstart; [fresh disk selection](../evidence/verification/iso-candidate4/public-disk-selection.png) and [successful completion](../evidence/verification/iso-candidate4/public-install-complete.png) independently inspected |
| Installed RTC convention and runtime time | Pass in this VM | [Read-only adjtime output](../evidence/verification/iso-candidate4/installed-rtc-before-first-boot.png) shows LOCAL; matching VM RTC mode; [runtime query](../evidence/verification/iso-candidate4/clock-observation.json) finds guest UTC about 1.6 seconds behind host |
| Late Places source contract | Pass | Independent [review](../evidence/verification/iso-candidate4/places-source-review.json), plus [pre-build Files/verification suites](../evidence/verification/iso-candidate4/pre-build-tests.json) |
| Completion-marker failure/retry behavior | Pass, host tests | [Four focused tests](../evidence/verification/iso-candidate4/first-login-contract-tests.json); actual desktop behavior remains separate |
| Native first-user setup and automatic Aven login defaults | Pass | Integrator created `reader` through native setup; [first desktop](../evidence/verification/iso-candidate4/first-desktop.png) and [fresh Dolphin Home](../evidence/verification/iso-candidate4/first-dolphin-home.png) captured before private instrumentation, independently inspected; both phase markers collected |
| Installed Atomic identity, signature and login service | Pass | Independent [installed audit](../evidence/verification/iso-candidate4/installed-audit.json): exact layer/base/origin, valid Fedora base signature, SELinux Enforcing, read-only root, active ostreed and enabled active Plasma Login Manager |
| Installed source, font rules and phase records | Pass | [Read-only inventory](../evidence/verification/iso-candidate4/installed-source-and-first-login.json): all 146 source files exact, installation manifest exact, two active font rules exact; phase log/marker copies retain original hashes |
| Native Places result and ownership | Pass on first login | [Runtime record audit](../evidence/verification/iso-candidate4/places-runtime-audit.json): exact before/after hashes and seven current changes; first Home and [SC grid](../evidence/verification/iso-candidate4/files-sc-grid.png) independently inspected |
| New user's active font configuration | Pass, 42/42 | [Reader font audit](../evidence/verification/iso-candidate4/reader-font-audit.json), no fontconfig overrides; SC/TC families, true weights, punctuation, rendering and emoji checks |
| Default app associations and duplicate Flatpaks | Pass | Same reader audit: 12/12 expected associations; installed audit and inventory find both old system Gwenview/Okular Flatpaks and their exported launchers absent |
| Native preview handoff | Failed; release rejected | Original preview closed on Enter/Open without launching the PDF application; the retained failure and later debug results are separated below |
| Remaining SC/TC and application smoke checks | Not completed for release | Earlier observations remain valid within their scope; later repaired-runtime results are excluded |
| Second disk-only boot and marker persistence | Not completed for release | Candidate rejected before the complete acceptance sequence |
| Candidate-4 split/reassembly integrity | Pass on Linux, integrator executed | [Full reassembly record](../evidence/verification/iso-candidate4/parts-reassembly.json): all four parts checked, output bytes and complete SHA match candidate 4 |

The integrator owns GUI operation, builds and final release acceptance. The
verification agent has made no guest GUI, configuration or file changes during
this candidate's review. A boot entry or source hash does not establish installed
behavior or visual quality.

## Public installation observations

The integrator booted the exact candidate-4 ISO through UEFI optical firmware,
used its public Kickstart and unchanged Anaconda GUI, and selected only a fresh
48 GiB Virtio disk with automatic partitioning. Guest internet access was blocked.
The selected locale was English (US), keyboard US and timezone Asia/Shanghai.
The [public workflow record](../evidence/verification/iso-candidate4/public-workflow.json)
records these choices; the independent
[completion and RTC inspection record](../evidence/verification/iso-candidate4/public-install-screenshot-inspection.json)
records exact screenshot hashes and operator attribution.

After Anaconda reported successful completion, the integrator preserved its
post-install log as `/var/log/aven-install.log` on the target and read the target's
`/etc/adjtime`, which displayed `LOCAL`. The terminal capture shows no clock-value
edit. The disposable disk `.cache/iso-test/public-candidate4.qcow2` was powered off
cleanly and booted with no optical drive, using UEFI and the matching QEMU local
RTC mode. Native Fedora setup created `reader`. Its completion page, first Aven
desktop and fresh Dolphin Home were inspected at original resolution; their
hashes and attribution are in the
[first-login inspection record](../evidence/verification/iso-candidate4/first-login-screenshot-inspection.json).

## Independent installed-system audit

Private SSH access was added to this disposable test system only after the first
Aven login, through ordinary native sudo. The integrator reports no profile
repair. The verification agent streamed read-only Python over root/reader SSH;
the probes did not write guest files, rebuild font caches, launch GUI applications
or change services. Demonstration files for subsequent application screenshots
are test fixtures, not installed user data from the ISO.

The exact layered deployment and its Fedora parent are present; the parent
signature verifies and the Fedora tracking ref resolves to it. The origin remains
`fedora:fedora/44/x86_64/kinoite`, with all five persistent requests:
`glibc-langpack-zh`, `gwenview`, `okular`, `python3-pyside6`, and `thunderbird`.
PySide6 is already in the base, so only four appear as active package layers.
Root is read-only, SELinux is Enforcing, and rpm-ostreed and Plasma Login Manager
are active. The two recorded failed units are the historical baseline's
unsupported-CPU `mcelog` and overlay `systemd-remount-fs` errors; the raw journal
is retained in the inventory. No live update or Atomic rollback was exercised.

The [installation record](../evidence/verification/iso-candidate4/installation-record.json),
[post-install log](../evidence/verification/iso-candidate4/aven-install.log),
[seed marker](../evidence/verification/iso-candidate4/reader-iso-seed-v1.json),
[layout marker](../evidence/verification/iso-candidate4/reader-iso-layout-v1.json),
and phase logs retain their original bytes. The inventory records guest/host-copy
hashes, modes, owners and modification times for later boot comparison. The install
log retains nonfatal `bwrap: pivot_root: Invalid argument` messages from Flatpak
triggers inside the installer chroot. Runtime checks independently verify both
targeted application removals and absence of their exported desktop launchers.

Reader's 42 active font queries pass with no fontconfig overrides. Plasma uses
Noto Sans normal weight 400 and title weight 500. The 12 default MIME/scheme
associations resolve to Firefox, Thunderbird, Gwenview, Okular and Dolphin as
intended. These queries establish configuration; Chinese paragraphs and actual
application opening still require native screenshots and operations.

The runtime clock query records `Asia/Shanghai`, `LocalRTC=yes`, and
`NTPSynchronized=no` on the offline guest. Guest UTC is approximately 1.6 seconds
behind the host, resolving the prior candidate's eight-hour VM mismatch under
the matching local-RTC harness setting. The initial combined-property query
returned empty output despite exit 0; a separately recorded query with repeated
property options supplies the actual values. No guest clock edit was made.

## Late Places correction

Candidate 3 completed a public installation and first-user login, but native
Dolphin still showed immutable system entries. Headless seeding ran before KDE
created the new user's native Places list. Candidate 4 finishes this work in the
session-dependent layout phase before publishing its completion marker.

The finalizer waits for an existing native XBEL bookmark list and two consecutive
complete Solid device inventories. It reuses the existing scoped writer and
immutable actual-change ownership records. Explicit visibility choices,
removable/hot-pluggable disks, unknown devices and user-data volumes remain
unchanged. In particular the shared Fedora root/home data volume remains visible;
the intended result does not hide the entire Storage Devices group.

The new host tests exercise a Places timeout followed by successful retry,
no reapplication after completion, refusal to complete layout without seeding,
and the system-user guard that leaves native Fedora setup alone. They confirm
marker behavior without operating a desktop. Native bookmark/model updates are
asynchronous. On candidate 4's actual first login, the finalizer completed after
three readiness attempts, hid four default bookmarks plus the immutable root,
EFI and boot entries, and published one immutable ownership record. Its recorded
before hash matches the preserved native backup, and its after hash exactly
matches the independently collected current XBEL. All seven owned flags are
present and hidden. Fresh Home and SC grid screenshots confirm the effective
sidebar while retaining `fedora_fedora`. Persistence after a second boot remains
pending.

## Release rejection and later debug repair

The integrator observed the original preview close on Enter/Open without launching
an application; native Dolphin opened the same PDF in Okular. The
[retained failure frame](../evidence/verification/iso-candidate4/preview-open-pdf-no-window-observed.png)
was independently inspected. A single static frame shows the resulting visible
state; the triggering action and failure sequence are attributed to the integrator.

After the untouched installed audit, the integrator replaced only
`reader`'s `.local/libexec/aven-preview/aven_preview/app.py` for debugging. The
source under `/var/lib/aven/source` remains the original 146-file candidate-4
payload from `ca020b9bf2b8704c9214f9b88af1a689982a0aea`. The
[read-only hash record](../evidence/verification/iso-candidate4/debug-runtime-hashes.json)
confirms the modified runtime matches the current fix and differs from that source.

The Files agent diagnosed an immediate-close race with the asynchronous Qt Wayland
handoff. The fix keeps the preview alive while a QProcess runs `/usr/bin/kde-open`
until its native opening job completes. The independent
[debug handoff review](../evidence/verification/iso-candidate4/debug-handoff-review.json)
records the exact fix hash, three original screenshots and matching KWin inventories:
Enter on PDF and the Open button each leave an active Okular document window;
Enter on an image leaves an active Gwenview image window. The screenshots visibly
render the corresponding files.

**These three successful repaired-runtime handoffs are excluded from ISO release
proof.** Candidate 5 must contain the fix and pass the native handoffs after its
own unmodified public installation and first-user workflow. The original candidate-4
reports and their hashes are preserved; they are not retroactively rewritten as
an audit of the repaired runtime.

## Earlier candidates and historical visual evaluation

The [candidate-3 report](iso-candidate3-verification.md) is preserved with its
different hash, 142-file source inventory, successful public installation,
read-only Atomic/font checks, observed sidebar issue and first-boot clock caveat.
Its successes are not counted as candidate-4 runtime checks. Candidate 2's failed
post-install mount check and debug recovery also remain excluded from release
installation proof.

The [round-4 critic](critic-round-04.md) passed the focused VM prototype at 8.33
overall and 8.5 for Chinese typography, with an affirmative three-second judgment.
Those scores belong to that paired VM evaluation. No new ISO visual score or
fractional-scaling pass is inferred from identical packages or source.

## Limits

- Candidate 4 is rejected for release. Its later debug repair is not a tested
  replacement ISO, and incomplete acceptance rows remain unverified.
- Physical hardware installation, Secure Boot, live Atomic rollback, and
  physical display frame pacing have not been demonstrated.
- BIOS firmware startup and a full public UEFI installation are separate checks;
  other storage layouts and filesystems need their own verification.
- Packaging corruption, truncation, missing/reordered parts, path escape and
  no-overwrite handling have [12 host tests](../evidence/verification/iso-packaging-verification.json).
  The integrator's actual candidate-4 reassembly also passes on Linux.
  Windows/macOS execution is untested; the helper's publication step requires
  hard-link support.
- Numbered release parts are not individually bootable. Only the reconstructed
  ISO matching the full hash is the installer artifact.
