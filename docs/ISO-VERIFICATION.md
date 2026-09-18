# Aven ISO verification — candidate 5

This is the historical **0.1.0 Breeze** artifact. The current Union release has
its own [0.3.1 verification report](UNION-ISO-0.3.1.md); the scores below do not
apply to Union.

**Accepted for prototype ISO release.** Candidate 5 passes media integrity,
BIOS/UEFI optical boot, offline public installation, native first-user setup,
automatic Aven defaults, installed Atomic/source/font checks, three native preview
handoffs, focused application smoke and second disk-only boot persistence.
The independent installed-ISO 1× critic passes at **8.27 overall, 8.5 Chinese**,
with an affirmative three-second differentiation judgment. The integrator accepts
this exact artifact with the documented scope and two nonblocking polish issues.
GitHub asset verification and publication are recorded separately in
[STATUS.json](STATUS.json).

## Artifact identity

| Field | Exact value |
|---|---|
| Image | `Aven-Atomic-KDE-44-0.1.0-prototype-x86_64.iso` |
| Bytes | `7,890,075,648` |
| SHA-256 | `ae91559362ecfb87fa4f630882a78c41f699540d0ffda25ccea66c7be00e34e0` |
| Source commit | `9500b72a79320ce062a8b7360eac5806b142c93a` |
| Source state | Clean; all 150 embedded files match the build manifest |
| Fedora base | `44.20260913.0` |
| Base commit | `be803f3e3bcdcc54885264702655e6e071864504154bc46044a08cc2aa2ce5df` |
| Local layered commit | `37fc46fea2b1059cdbc35c4ff88a2b40ede7fcc105cca76693f11cc4cdffd551` |

The original [build manifest](../evidence/verification/iso-candidate5/build-manifest.json)
is preserved. The Fedora parent and locally generated layer are distinct; the
layer is not Fedora-signed. This ISO is an Anaconda installer, not a live desktop.
Public storage choices and Fedora's native first-user setup remain interactive.

## Current evidence

| Check | Result | Evidence / attribution |
|---|---|---|
| Full ISO hash, ISO9660 and BIOS/UEFI boot structures | Pass | Independent [media audit](../evidence/verification/iso-candidate5/media-audit.json) |
| Offline ref, commit objects and embedded source | Pass | Same audit: exact layer/base object hashes, archive repository and all 150 files |
| Public Kickstart defaults | Pass | Same audit and existing source review: no lab user/key, automatic erase, automatic login or passwordless sudo |
| Native preview fix included | Pass, source identity | [Inclusion record](../evidence/verification/iso-candidate5/source-fix-inclusion.json); embedded file matches the fix hash; installed runtime and native behavior verified separately below |
| Actual BIOS optical boot | Pass | Integrator operated firmware; [native welcome](../evidence/verification/iso-candidate5/bios-installer-welcome.png) independently inspected |
| Actual UEFI optical boot | Pass | Integrator operated firmware; [native welcome](../evidence/verification/iso-candidate5/uefi-installer-welcome.png) independently inspected |
| Offline public installation on a fresh disk | Complete in Anaconda | Native [disk selection](../evidence/verification/iso-candidate5/public-disk-selection.png), [ready summary](../evidence/verification/iso-candidate5/public-install-ready.png) and [successful completion](../evidence/verification/iso-candidate5/public-install-complete.png) independently inspected |
| Native first-user setup and login greeter | Pass for these stages | Unchanged setup pages, [Completed screen](../evidence/verification/iso-candidate5/native-first-user-complete.png) and [native login greeter](../evidence/verification/iso-candidate5/native-first-login.png) independently inspected |
| Automatic Aven first-login defaults | Pass on first login | Untouched [first desktop](../evidence/verification/iso-candidate5/first-desktop.png) and [Dolphin Home](../evidence/verification/iso-candidate5/first-dolphin-home.png) independently inspected; phase markers/logs collected |
| Installed Atomic identity, GPG, origin, SELinux and login service | Pass | Independent [read-only installed audit](../evidence/verification/iso-candidate5/installed-audit.json): exact layer/base/Fedora ref and persistent requests, valid signature, SELinux Enforcing, read-only root, active ostreed and enabled active Plasma Login Manager |
| Installed source and active runtime identity | Pass | [All 150 source files exact](../evidence/verification/iso-candidate5/installed-source-and-first-login.json); [all seven active code/style copies exact](../evidence/verification/iso-candidate5/runtime-versions-mounts-audit.json), including corrected preview app |
| Active fonts and app associations | Pass, 42/42 and 12/12 | [Read-only reader audit](../evidence/verification/iso-candidate5/reader-font-audit.json); no fontconfig overrides; both old system Flatpak duplicates and exported launchers absent in installed checks |
| Native Places result and ownership | Pass on first login | [Runtime audit](../evidence/verification/iso-candidate5/places-runtime-audit.json): exact native backup/before and current/after hashes, all seven owned flags present; first Home keeps shared user-data volume visible |
| Preview Enter/Open handoff | Pass, 3/3 native paths | Independent [handoff review](../evidence/verification/iso-candidate5/preview-handoff-review.json): Enter and Open button on PDF launch active Okular; Enter on image launches active Gwenview; previews are absent afterward |
| Files, browser, mail, photos and SC/TC paragraphs | Pass, focused ISO smoke | Independent [native smoke review](../evidence/verification/iso-candidate5/native-smoke-review.json): 24 original frames, real HTTPS, native file operations, chooser/download, draft save/reopen and photo viewing; scope below |
| Second disk-only boot and persistence | Pass | [24 independent checks](../evidence/verification/iso-candidate5/second-boot/persistence-review.json): different boot ID; unchanged completion markers/logs, runtime, fonts and defaults; all 150 source files exact |
| Candidate-5 split/reassembly | Pass on Linux | [Actual four-part reconstruction](../evidence/verification/iso-candidate5/parts-reassembly.json), plus independent [full reconstructed-image hash](../evidence/verification/iso-candidate5/reassembled-image-audit.json) and exact byte count |
| Installed ISO visual critic | Pass at 1×, 8.27 overall / 8.5 Chinese | [Fresh direct screenshot comparison](critic-iso-candidate5.md); three-second answer yes |
| ISO release acceptance | Accepted by integrator | Exact artifact passes the boot/install, native smoke, persistence and scoped visual gates; publication is tracked in STATUS.json |

The media audit validates boot structures; the two optical boots are separately
operated runtime checks. Commit-object hashes and detached signature metadata do
not substitute for installed signature verification. The verification agent has
made no guest GUI, source or configuration changes during this candidate's review.

## Public installer workflow

The integrator booted the public ISO through UEFI optical firmware with no private
Kickstart or external kernel/initrd. The selected target is only the fresh 48 GiB
Virtio disk `.cache/iso-test/public-candidate5.qcow2`, using native automatic
partitioning. QEMU restricts guest internet access. The native choices are English
(US), US keyboard and Asia/Shanghai. Manual clock mode was selected because this
offline guest cannot use NTP; the integrator reports leaving the displayed clock
values unchanged. The captured time page shows 20:06 on 2026-09-15.

The [operator workflow](../evidence/verification/iso-candidate5/public-workflow.json)
and independent [workflow inspection](../evidence/verification/iso-candidate5/installer-workflow-inspection.json)
record these stages, image hashes and attribution. Firmware mode comes from the
operator's boot configuration, not from a visually identical welcome screen.

Anaconda subsequently displayed Complete and its successful-installation text.
The integrator preserved the installer log on the target and read `/etc/adjtime`,
which returned `LOCAL`; the [terminal capture](../evidence/verification/iso-candidate5/installed-rtc-before-first-boot.png)
shows no clock-value edit. The operator then booted only the new disk through UEFI,
with matching local-RTC mode and restricted networking.

Native Fedora first-user setup displayed its unchanged welcome, language, keyboard,
appearance, initially blank account form, hostname and timezone pages, followed by
Completed. The selected visible defaults were American English, standard US
keyboard, light appearance and Asia/Shanghai. The hostname screenshot shows the
initial `fedora` default; the integrator reports editing it to `aven-iso-test`
before Next. The independent second-boot query confirms `aven-iso-test`. The resulting
login greeter displays the newly created Aven ISO Test account. The integrator
then completed login and captured the untouched Aven desktop and first Dolphin
Home before adding private SSH access or demonstration files. The independent
[desktop inspection record](../evidence/verification/iso-candidate5/first-desktop-inspection.json)
records exact hashes. These English frames establish visible defaults, not Chinese
typography quality or application handoff behavior.

## Independent installed-system checks

After that untouched first login, private laboratory SSH access was added through
ordinary native sudo. The integrator reports no profile repair. The verification
agent streamed read-only Python as root and reader; no guest files, windows,
services, settings or font caches were changed. The exact streamed probes are
retained with the reports. Fixtures later staged for application screenshots are
test data rather than content shipped into a user's home by the ISO.

The booted local layer and signed Fedora parent match the artifact table. The
Fedora tracking ref resolves to the signed parent, and the update origin remains
`fedora:fedora/44/x86_64/kinoite`. All five package requests persist; PySide6 is
already in the base, so only four appear as active layers. The root mount is
read-only, SELinux is Enforcing, and rpm-ostreed and Plasma Login Manager are
active. Two failed units remain: the historical baseline's unsupported-CPU
`mcelog` and overlay `systemd-remount-fs` errors. Their journal is retained in the
inventory report. No live update or Atomic rollback was exercised.

The installed source contains exactly 150 files matching the ISO manifest. All
four user preview Python files, Firefox chrome stylesheet and two Thunderbird
chrome stylesheets match their installed sources. The active preview `app.py`
therefore contains the candidate-5 fix, without a debug runtime replacement.
The native handoff observations below verify the installed behavior separately.

The [installation record](../evidence/verification/iso-candidate5/installation-record.json),
[post-install log](../evidence/verification/iso-candidate5/aven-install.log),
[seed marker](../evidence/verification/iso-candidate5/reader-iso-seed-v1.json),
[layout marker](../evidence/verification/iso-candidate5/reader-iso-layout-v1.json),
phase logs and immutable Places record retain their original bytes. The inventory
records hashes, sizes, owners, modes and modification times. The installer log
retains nonfatal `bwrap: pivot_root: Invalid argument` warnings from Flatpak
triggers in the chroot; runtime queries independently confirm both targeted
applications and their exported launchers are absent.

The Places finalizer completed after three readiness attempts, hiding four
default bookmarks plus the immutable root, EFI and boot entries. Its record's
before hash matches the preserved native backup, and its after hash exactly
matches the collected XBEL. All seven owned hidden flags are present; the fresh
Dolphin frame retains the shared `fedora_fedora` data volume. Reader's 42 active
font queries pass, including regional Chinese families, real weights, punctuation,
rendering properties and emoji. All 12 requested default app associations resolve
correctly. Native Chinese paragraphs and application opening are not inferred
from these configuration checks.

Runtime versions are Plasma/KWin 6.7.5, Dolphin/Gwenview/Okular 26.08.1, Firefox
155.0, Thunderbird 153.0.2 and Qt/PySide6 6.11.2. Package versions and the complete
mount inventory are retained in the runtime report. The offline guest reports
Asia/Shanghai, `LocalRTC=yes`, no NTP synchronization and UTC approximately
1.35 seconds behind the host with the matching local-RTC harness option.

The [first-boot persistence baseline](../evidence/verification/iso-candidate5/first-boot-persistence-baseline.json)
was compared with a second UEFI disk-only boot after native password login. Its
kernel boot ID changed from `2e5c67bf-f3aa-4f1e-a264-68ce1e5628e9` to
`37806618-6973-4c46-ad8c-4743e2db8318`. Both completion markers, both phase logs
and the immutable Places record retained their bytes, sizes, modification times,
owners and modes. No extra Places record appeared. All seven active code/style
copies, both font rules and all 12 associations were unchanged; all 150 installed
source files remained exact. The [persistence review](../evidence/verification/iso-candidate5/second-boot/persistence-review.json)
passes all 24 checks and records each comparison.

The second [desktop](../evidence/verification/iso-candidate5/second-desktop.png)
and [Dolphin Home](../evidence/verification/iso-candidate5/second-dolphin-home.png)
were independently inspected. Aven's panel, wallpaper and focused Places persist;
all seven owned hidden flags remain present, and the shared user-data volume is
visible. The repeated Atomic/signature/origin/SELinux, 42 font checks and 12 default
association checks pass. The same two baseline failed units remain. This boot
used matching local RTC and online networking for the HTTPS smoke check; UTC was
approximately 1.24 seconds behind the host, with no NTP synchronization reported.
Ordinary application preferences can change through legitimate use; whole browser
or mail profile hashes were not used as a persistence condition.

## Preview correction and acceptance boundary

[Candidate 4 was rejected](iso-candidate4-verification.md) because its original
preview closed without launching the associated application on Wayland. After
its untouched audit, the integrator copied one corrected file into the user's
local preview runtime. Enter on PDF, the Open button on PDF and Enter on an image
then opened the expected active native apps. The independently inspected
[debug evidence](../evidence/verification/iso-candidate4/debug-handoff-review.json)
is retained and excluded from release proof.

Candidate 5 embeds `preview/aven_preview/app.py` with SHA-256
`99d794d2c9f148d164b979547dd839cd41906a5b219434a9f3cc21bf7366a695`.
The fix keeps the preview alive while `/usr/bin/kde-open` completes its document
opening job. The runtime identity audit confirms the user copy matches this hash.
The integrator then operated each native path on the unmodified candidate-5
installation: select the file in Dolphin, open preview with Ctrl+Alt+P, and use
Enter or the preview's Open button. No runtime patch or profile repair was applied.

The independent [handoff review](../evidence/verification/iso-candidate5/preview-handoff-review.json)
records original-resolution image inspection and exact image/inventory hashes:

- [Enter on PDF](../evidence/verification/iso-candidate5/preview-enter-pdf.png)
  opens the Weekend walk document in native Okular.
- [Open button on PDF](../evidence/verification/iso-candidate5/preview-button-pdf.png)
  opens the same document in another native Okular window.
- [Enter on image](../evidence/verification/iso-candidate5/preview-enter-image.png)
  opens the selected waterfall JPEG in native Gwenview.

All three matching KWin inventories identify the expected window as active,
visible and not minimized, with no preview window remaining. The triggering
input sequences are attributed to the integrator; the verification agent
independently inspected their resulting frames and public KWin inventories.
This establishes these three handoffs on candidate 5. Application smoke and
second-boot checks have their own evidence and acceptance rows.

## Focused native application smoke

The integrator operated the applications on the unmodified candidate-5 runtime.
The independent [smoke review](../evidence/verification/iso-candidate5/native-smoke-review.json)
records 24 individually inspected original screenshots, exact hashes and the
distinction between native operation and independent observation.

- **Files:** the same mixed folder renders in list and grid views with image,
  WebM and PDF thumbnails and Chinese/Latin filenames. A native copy to Downloads,
  rename to `ISO-copy.txt`, move to Documents and move to Trash are evidenced by
  resulting native views. Independent second-boot reads confirm the original and
  trashed copy still share the same 160-byte SHA-256; the moved file is absent
  from Documents.
- **Preview:** image, PDF and SC/TC paragraphs render in the lightweight preview.
  Media frames show distinct playing/paused states and a five-second duration;
  static frames do not establish smooth frame pacing. The three required native
  app handoffs pass separately above.
- **Browser:** local SC and TC paragraphs render, Firefox's native popover reports
  a completed 428-byte download, and the KDE chooser returns a selected local
  image. The download hash persists after reboot. On the online second boot,
  native navigation to Mozilla redirects to the rendered
  [official Firefox Chinese page](../evidence/verification/iso-candidate5/browser-https.png).
  The operator reports no certificate override; the original first translation
  prompt and session hint are preserved in a separate frame.
- **Mail:** the isolated local `c5-demo` fixture supports SC/TC reading and native
  draft editing, saving and reopening. The reopened draft visibly includes
  `补充：路线已经核对，周六见。`; the narrow composer visibly wraps the longer
  paragraph. Independent mbox parsing after reboot confirms the saved text and
  unchanged draft-file SHA-256. No email was sent and no real account was added.
- **Photos:** all eight album thumbnails render in Gwenview. Native image viewing,
  the next image, fullscreen and the exact river fixture are visibly confirmed.

The [independent persisted-operation check](../evidence/verification/iso-candidate5/second-boot/operations-persistence.json)
corroborates the Files, browser download and mail results without launching an app
or changing the guest. These are focused ISO smoke checks; they do not rerun every
historical 17-operation or six-motion sequence, establish live mail transport, or
provide new fractional-scale measurements.

## Installed ISO visual acceptance

The independent [candidate-5 critic](critic-iso-candidate5.md) inspected 47 current
original PNGs and 36 stock/accepted reference originals across 18 comparison groups.
Its mean is 8.2667, Chinese typography 8.5, and three-second answer yes. The current
1× review meets the requested overall ≥8 and Chinese ≥8.5 gate. Source identity is
provenance only; these scores come from the newly installed system's screenshots.

Two visible issues remain: the initial Everyday list uses approximately 26px rows,
changing to 36px after visiting grid, and native Gwenview resizing leaves a taller
filmstrip that reduces the exact river image's fit from accepted 79% to 73%.
The critic records both as nonblocking, with Files 8.2 and photos 7.8. No runtime
repair or replacement was applied to hide either result.

The integrator accepts this exact ISO for the requested prototype release. Current
full fractional-scale and motion reruns remain unverified; their existing round-4
evidence is historical and is not relabeled as candidate-5 validation.

## Earlier evidence and limits

The [candidate-3](iso-candidate3-verification.md) and
[candidate-4](iso-candidate4-verification.md) reports preserve their distinct
hashes, successes, failures and debug boundaries. No earlier installed-system
result is counted as a candidate-5 runtime pass.

The historical [round-4 critic](critic-round-04.md) passed the focused VM prototype
at 8.33 overall and 8.5 for Chinese typography, with an affirmative three-second
judgment. Those scores belong to the paired VM evaluation. No new ISO visual score
or fractional-scaling result is inferred from package or source identity.

- Physical hardware installation, Secure Boot, live Atomic rollback and physical
  display frame pacing have not been demonstrated.
- Firmware startup, full installation and first-user completion are separate
  checks. Other storage layouts and filesystems require their own tests.
- Packaging failure handling has [12 host tests](../evidence/verification/iso-packaging-verification.json).
  Actual candidate-5 four-part reassembly passed, and the verification agent
  independently rehashed all 7,890,075,648 reconstructed bytes to the exact ISO hash.
- Windows/macOS execution is untested; the reconstruction helper requires a
  filesystem with hard-link support. Numbered parts are not individually bootable.
- Publication status and server asset verification are tracked separately in
  [STATUS.json](STATUS.json); ISO acceptance does not by itself claim publication.
