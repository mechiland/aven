# Aven Union 0.3.1 installer ISO

Download the complete [Aven Union 0.3.1 ISO](https://aven-downloads.mechiland.workers.dev/releases/v0.3.1/Aven-Union-44-0.3.1-x86_64.iso)
and [SHA-256 file](https://aven-downloads.mechiland.workers.dev/releases/v0.3.1/Aven-Union-0.3.1-SHA256SUMS)
from Cloudflare R2 through Aven's read-only download Worker. The image is
8,051,228,672 bytes (8.05 GB). No part reassembly is needed.

```sh
sha256sum --check Aven-Union-0.3.1-SHA256SUMS
```

On macOS use `shasum -a 256 Aven-Union-44-0.3.1-x86_64.iso`; on Windows use
`Get-FileHash Aven-Union-44-0.3.1-x86_64.iso -Algorithm SHA256` in PowerShell.
The expected hash is:

```text
59d81e2afb1c7241c274f961ae83cb13dd54d77a15459b266c87c1f458ef23eb
```

Write the ISO as a disk image to a USB drive of at least 16 GB, or attach it to
a virtual optical drive. Writing an image replaces the selected USB drive's
contents. Keep the full ISO on a filesystem that supports files larger than 4 GB.
Release notes and the build manifest are on the
[v0.3.1 release](https://github.com/mechiland/aven/releases/tag/v0.3.1).

The ISO installs Aven Atomic KDE 44 through Fedora's original Anaconda installer.
It is an installer, not a live desktop. Disk selection, partitions and user
credentials remain interactive. Fedora's native first-boot setup creates the
desktop user after installation. The release contains no laboratory SSH key,
preconfigured user, automatic disk erasure, automatic login or passwordless sudo.

## System and profile

The offline payload preserves the tested `44.20260913.0` Fedora base, its Fedora
signature, five persistent package requests, two local additions and 84 local
Beta replacements. All 103 package-cache refs are included so rpm-ostree retains
the local package objects needed for later transactions. The exact identities
are recorded in [iso/platform.json](../iso/platform.json). The local layered
commit is not signed by Fedora. After installation the update origin remains
`fedora:fedora/44/x86_64/kinoite`, with Fedora signature verification enabled.

This experimental version uses Plasma 6.8 Beta (RPM 6.7.90), the Aven Mist Union
theme, 500 emphasis for managed typography roles, and a translucent dock with
small dark running indicators. Local Beta overrides remain pinned until explicitly
replaced or reset; this is not an automatic Beta update channel. The remaining
appearance and verification limits are in [the Union ISO report](UNION-ISO-0.3.1.md).

A fresh installation starts with one deployment. Later Fedora Atomic updates
create a new deployment and retain the previous one for rollback.

The installer places fontconfig under `/etc` and Aven source under
`/var/lib/aven/source`. On each user's first Plasma login, the profile seeds their
own fonts, Dolphin/preview, Firefox, Thunderbird, Gwenview and visual defaults.
The native panel is configured through Plasma's scripting API. Completion markers
under `~/.local/state/aven/iso-*-v1.json` prevent reapplying defaults on later logins.
Normal browser/mail profiles start empty; demonstration data is not imported.

Aven's profile survives ordinary Atomic updates through `/etc`, `/var` and the
user's home. Fedora remains responsible for system updates. This prototype does
not provide an Aven update channel, and integration with later application
versions needs a new verification round.

## Build

Install QEMU/KVM, xorriso, mtools and isomd5sum on the build host. No host root
mounts are required. First build and verify the prototype as described in
[BUILD.md](BUILD.md). Export the exact layered commit and its signed base to a
new archive-mode OSTree repository, including every `package_cache_refs` entry
from `iso/platform.json`; see the commands and verification contract
in [iso-contract.md](../verification/iso-contract.md).

```sh
python3 scripts/build-iso.py --repo /path/to/exported/ostree/repo
```

The builder verifies the official ISO and exact commit/ref identifiers, preserves
its BIOS/UEFI boot structures, updates both external and EFI-partition GRUB
configurations, adds the offline payload, and regenerates/checks the media
checksum. The final `.json` records the complete ISO SHA-256, source file hashes
and source commit. The official installer runtime is retained verbatim, including
its original repository cache, so this first prototype favors a straightforward
build over a smaller download.

## Verify

```sh
python3 scripts/iso-vm.py optical
python3 scripts/iso-vm.py optical --uefi
python3 scripts/iso-vm.py prepare
python3 scripts/iso-vm.py install
python3 scripts/iso-vm.py boot
```

Run each boot after shutting down the preceding test VM. The optical checks boot
from firmware and the public ISO itself. The automated installation uses the
same ISO kernel/runtime and public Aven Kickstart, plus a private disposable test
Kickstart appended to the initrd. It creates only `.cache/iso-test/installed.qcow2`;
the private SSH key and automatic partitioning never enter the published ISO.
QEMU blocks the guest's internet access during installation. Booting the resulting
disk omits the optical drive entirely.

The release acceptance path uses the public graphical installer and native
first-user setup, without the private automation overlay:

```sh
python3 scripts/iso-vm.py public-install --uefi --disk .cache/iso-test/public-installed.qcow2
# Complete Anaconda, then shut the guest down cleanly.
python3 scripts/iso-vm.py boot --uefi --disk .cache/iso-test/public-installed.qcow2
```

Use `--online` on a later disk boot for ordinary browsing checks. If the guest
was configured to interpret the hardware clock as local time, add `--local-rtc`
to match it. These are laboratory options, not changes to the ISO.

Record firmware boots, installation logs, Atomic origin/signature audit, first
login completion, native applications and Chinese screenshots, and a second
boot that retains the completion markers. Packaging acceptance is separate from
the historical round-4 visual score; see `docs/STATUS.json` and the ISO release
verification report.

## Earlier release

The [0.1.0 Breeze prototype](https://github.com/mechiland/aven/releases/tag/v0.1.0-prototype)
remains available with its original split-image reconstruction helper and
[candidate-5 verification](ISO-VERIFICATION.md). Its visual scores apply only to
that older artifact. Union 0.3.1 uses the single R2 download above.
