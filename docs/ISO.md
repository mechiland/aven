# Aven installer ISO

The ISO installs Aven Atomic KDE 44 through Fedora's original Anaconda installer.
It is an installer, not a live desktop. Disk selection, partitions and user
credentials remain interactive. Fedora's native first-boot setup creates the
desktop user after installation. The release contains no laboratory SSH key,
preconfigured user, automatic disk erasure, automatic login or passwordless sudo.

## System and profile

The offline payload preserves the tested `44.20260913.0` Fedora base, its Fedora
signature, and the five persistent package requests. The local layered commit is
not signed by Fedora. After installation the update origin remains
`fedora:fedora/44/x86_64/kinoite`, with Fedora signature verification enabled.

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
new archive-mode OSTree repository; see the commands and verification contract
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

Record firmware boots, installation logs, Atomic origin/signature audit, first
login completion, native applications and Chinese screenshots, and a second
boot that retains the completion markers. Packaging acceptance is separate from
the historical round-4 visual score; see `docs/STATUS.json` and the ISO release
verification report.

## Download and reconstruct

GitHub limits individual release assets to less than 2 GiB. If the ISO is split,
download every numbered `.iso.part-*` file and `ISO-SHA256SUMS` from the same
release into one directory. These parts are not individually bootable.

On Linux/macOS:

```sh
cat Aven-Atomic-KDE-44-0.1.0-prototype-x86_64.iso.part-* > Aven-Atomic-KDE-44-0.1.0-prototype-x86_64.iso
sha256sum --check ISO-SHA256SUMS
```

macOS can verify a hash with `shasum -a 256 <filename>`. Windows users can use the
release's `reassemble-iso.py` with Python 3; it verifies every part and the whole
ISO and refuses to overwrite an existing output. Write the reconstructed ISO to
a USB drive of at least 16 GB using a standard image-writing tool, then boot it.
