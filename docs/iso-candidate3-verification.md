# Aven ISO verification — candidate 3 (superseded)

Candidate 3 passed installation and Atomic/font checks, but its new-user Files sidebar skipped Aven defaults because native Places initialized after profile seeding. It is not the release candidate. Candidate 4 will fix this ordering and repeat public installation verification.

## Artifact identity

| Field | Exact value |
|---|---|
| Image | `Aven-Atomic-KDE-44-0.1.0-prototype-x86_64.iso` |
| Bytes | `7,890,010,112` |
| SHA-256 | `a0849b1ff8d263813a82fd47f53eb052e3b36600b2c97a2542ee0e08afedd96f` |
| Source commit | `8adb380dfb7cf572b9ef652dfe49084dc5024115` |
| Source state | Clean; all 142 embedded files match the build manifest |
| Fedora base | `44.20260913.0` |
| Base commit | `be803f3e3bcdcc54885264702655e6e071864504154bc46044a08cc2aa2ce5df` |
| Local layered commit | `37fc46fea2b1059cdbc35c4ff88a2b40ede7fcc105cca76693f11cc4cdffd551` |

The signed Fedora parent and locally generated layer are distinct. The ISO is an
Anaconda installer, not a live desktop. Its public installer retains native disk
and storage decisions; Fedora's first-boot setup creates the desktop user.

## Current evidence

| Check | Result | Evidence / attribution |
|---|---|---|
| ISO format, complete hash, BIOS/UEFI boot entries | Pass | Independent [candidate-3 media audit](../evidence/verification/iso-candidate3-media-audit.json) |
| Offline ref, exact commit objects, source inventory | Pass | Same audit; both commit-object hashes and all 142 source files verified |
| Public Kickstart defaults | Pass | Same audit plus source review: no lab user/key, automatic disk erasure, automatic login or passwordless sudo |
| Actual BIOS optical boot | Pass | Root operated firmware boot; [native installer welcome](../evidence/verification/iso-candidate3/bios-installer-welcome.png) independently inspected |
| Actual UEFI optical boot | Pass | Root operated firmware boot; [native installer welcome](../evidence/verification/iso-candidate3/uefi-installer-welcome.png) independently inspected |
| Public UEFI installation to a fresh disk | Complete in Anaconda | Root operated unchanged native UI; [disk selection](../evidence/verification/iso-candidate3/public-disk-selection.png) and [successful completion](../evidence/verification/iso-candidate3/public-install-complete.png) independently inspected |
| Full ISO split and reassembly | Pass on Linux | Root's [full reassembly record](../evidence/verification/iso-candidate3-reassembly.json); independent [actual-part and concatenated-stream check](../evidence/verification/iso-candidate3-independent-parts-check.json) |
| Packaging failure handling | Pass | [12 temporary-file tests](../evidence/verification/iso-packaging-verification.json): corruption, truncation, missing/reordered parts, path escape, exact boundaries, and no-overwrite publication |
| Native first-user setup and first Aven login | Pass | Root created `reader` in unchanged native setup; [completion](../evidence/verification/iso-candidate3/native-first-user-complete.png) and [first desktop](../evidence/verification/iso-candidate3/first-desktop.png) independently inspected; both user completion markers collected |
| Installed Atomic identity, signature, PLM, Flatpak duplicates | Pass | Independent [read-only installed audit](../evidence/verification/iso-candidate3/installed-audit.json); exact layer/base/origin, Fedora signature, active ostreed, read-only root, SELinux Enforcing, enabled active Plasma Login Manager, no duplicate system Gwenview/Okular Flatpaks |
| Installed source, font rules and first-login records | Pass | Independent [inventory and record hashes](../evidence/verification/iso-candidate3/installed-source-and-first-login.json): all 142 source files exact, installation manifest matches, both active font rules exact, duplicate Flatpak launchers absent |
| New user's active font configuration | Pass, 42/42 | [Read-only font audit as reader](../evidence/verification/iso-candidate3/reader-font-audit.json); family/region/weight/fallback/rendering checks, with no fontconfig overrides |
| Native SC/TC text rendering | Smoke pass at captured scale | Original [SC](../evidence/verification/iso-candidate3/preview-text-sc.png) and [TC](../evidence/verification/iso-candidate3/preview-text-tc.png) paragraphs independently inspected; no new visual score or ISO scaling-matrix pass assigned |
| Native Files, preview, browser, mail and photos | In progress | Dolphin grid and SC/TC/PDF previews inspected; system-volume sidebar difference recorded below; remaining native application smoke checks pending |
| Second disk-only boot and marker persistence | Pending | Confirm profile completion markers survive and defaults are not reapplied |

The public installation used UEFI optical firmware, the ISO's own kernel/runtime
and embedded public Kickstart, with no external kernel/initrd or private Kickstart
override. Root selected only a fresh 48 GiB Virtio disk, default automatic
partitioning, English (US), US keyboard, and Asia/Shanghai timezone. QEMU's
restricted user network blocked guest internet access. The target is the
disposable `.cache/iso-test/public-installed.qcow2`; its existence is test output,
not the distributed ISO artifact.

The [public workflow record](../evidence/verification/iso-candidate3/public-workflow.json)
tracks the operator's progress. The independently inspected installer images and
their exact hashes are recorded in the
[screenshot inspection record](../evidence/verification/iso-candidate3-install-screenshot-inspection.json).
Boot mode comes from the recorded firmware setup; it cannot be inferred from a
welcome screenshot alone. Installer completion is not a substitute for a working
installed desktop.

## Installed-system observations

The verification agent streamed read-only Python and commands over SSH after the
integrator completed native first login. SSH access was added to the disposable
test system only after that login, using ordinary sudo; it was not shipped in the
ISO or used to repair the product. These probes did not change guest files,
settings, windows, or services.

The booted deployment is the exact locally layered commit above. Its Fedora
parent signature verifies, the Fedora tracking ref resolves to that parent, and
the origin is `fedora:fedora/44/x86_64/kinoite`. All five package requests persist:
`glibc-langpack-zh`, `gwenview`, `okular`, `python3-pyside6`, and `thunderbird`.
PySide6 is already supplied by the base, so only four packages appear as active
layers. No live update or rollback was exercised by this read-only audit.

The collected [installation record](../evidence/verification/iso-candidate3/installation-record.json),
[install log](../evidence/verification/iso-candidate3/aven-install.log),
[seed marker](../evidence/verification/iso-candidate3/reader-iso-seed-v1.json),
[layout marker](../evidence/verification/iso-candidate3/reader-iso-layout-v1.json),
and both phase logs retain their original bytes. Guest/host copy hashes, modes,
owners and modification times are in the inventory report. The install log
contains nonfatal `bwrap: pivot_root: Invalid argument` messages from Flatpak
triggers in the installer chroot. The final installation completed, and independent
runtime checks found both targeted Flatpaks and their exported launchers absent.

The [failed-unit journal](../evidence/verification/iso-candidate3/failed-unit-journal.json)
retains three failures: the baseline's unsupported-CPU `mcelog` and overlay
`systemd-remount-fs` errors, plus `rpm-ostree-countme` failing Fedora HTTPS requests
with guest internet access restricted. `rpm-ostreed` itself is active. The audit
does not describe the system as having zero failed services.

The [clock observation](../evidence/verification/iso-candidate3/clock-observation.json)
records guest UTC eight hours behind host UTC, `Asia/Shanghai`, local RTC enabled,
and no NTP synchronization. A QEMU RTC/local-time mismatch is a possible cause;
it was not changed or confirmed experimentally. Use hashes and host collection
timestamps for evidence identity; guest log and marker timestamps are not directly
comparable with host chronology.

The original desktop and Chinese preview frames have an independent
[inspection record](../evidence/verification/iso-candidate3-desktop-screenshot-inspection.json).
The first desktop visibly receives Aven's wallpaper and centered panel. The new
user's font settings use Noto Sans normal weight 400 and window-title weight 500;
SC and TC preview paragraphs, Latin text, punctuation and emoji render visibly.
This does not replace the historical matched scaling and critic evaluation.

**Visible ISO difference:** Dolphin's first-user sidebar still lists internal
system volumes, including an unlabeled red capacity bar, `vda2` and
`fedora_fedora`. This differs from the evaluated round-4 sidebar. It is retained
in the [actual grid capture](../evidence/verification/iso-candidate3/files-sc-grid.png)
and has not been hidden through a test-only guest repair.

## Failed candidate and debug recovery

Candidate 2 had SHA-256
`05e98ac160c99556af081798672aad1a6fdd0394d2902dfbc06323d9af65000b`.
Its media audit and optical boots passed, but installation failed in the public
post-install script's `/var` mount check. Anaconda binds the deployment at
`/mnt/sysroot` and mounts child filesystems there; the original physical deployment
path does not expose those child mounts.

The corrected helper was exercised against that disposable target for debugging.
It restored the intended origin, imported and verified the Fedora base, copied
the profile source, and removed the two old system Flatpak duplicates. That
recovered disk is **excluded from candidate-3 release installation evidence**.
See the retained [candidate-2 outcome](../evidence/verification/iso-candidate2/outcome.json)
and [original failed post-install log](../evidence/verification/iso-candidate2/aven-post.log).

Candidate 3 incorporates the mounted-target correction, narrowly removes the
Gwenview and Okular system Flatpak duplicates, and skips profile seeding for system
accounts so native first-user setup remains unchanged. Its clean public install
is the relevant packaging test.

## Relationship to the round-4 desktop evaluation

The [round-4 critic](critic-round-04.md) passed the focused VM prototype at 8.33
overall and 8.5 for Chinese typography, with an affirmative three-second
differentiation judgment. Its paired screenshots, operations and motion evidence
remain the basis for that historical judgment.

Those scores are not new scores for the ISO installation. The ISO adds an
installation and first-user profile path that must be verified separately. This
report will record actual installed-system checks without deriving visual quality
from source hashes, identical package commits, or English-only screenshots.

## Remaining limits

- No physical hardware installation, Secure Boot, live Atomic rollback, or
  physical display frame-pacing result is claimed.
- BIOS optical startup is tested; the full public installation currently covers
  UEFI. Other storage layouts and filesystems have not been exercised.
- Full reassembly was exercised on Linux. Windows and macOS execution remain
  untested; the helper's publication step needs a filesystem with hard links.
- Four release parts each fit below 2 GiB and concatenate to the exact ISO hash.
  The individual parts are not bootable media.
- Final release acceptance stays pending until the remaining installed-system
  rows above are backed by evidence. `docs/STATUS.json` is owned by the integrator.
