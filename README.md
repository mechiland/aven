# Aven — focused Atomic KDE prototype

Aven explores a calmer daily desktop on Fedora Kinoite 44: **Files, browser,
mail, photos, and Noto Latin/Chinese typography**. Dolphin remains the file
manager. Fedora's Atomic deployments, update path, SELinux and rollback remain
part of the product.

The experimental **Union variant** uses Plasma 6.8 Beta and a native Aven Mist
Union theme. The latest unreleased change is the
[full-width translucent panel](docs/UNION-FULL-WIDTH-PANEL.md). See also the
[500 emphasis and translucent dock revision](docs/UNION-DOCK-MEDIUM.md),
the [macOS 15 framework revision](docs/UNION-SEQUOIA.md)
and [Union build and verification](docs/UNION.md).
Its status is separate from the earlier Breeze prototype results below.

The earlier Breeze **round 4 prototype passed** the independent focused review:
**8.33 overall, 8.5 Chinese typography**, and **yes** on three-second refinement.
The strict evidence gate passes with zero errors. All 17 required native
operations and 75 automated tests pass; current SC/TC UI/prose pairs cover
100%, 125%, 150% and 200%. The authoritative result is in
[docs/STATUS.json](docs/STATUS.json). These scores describe the assessed desktop
prototype; installer acceptance is recorded separately in the
[ISO verification report](docs/ISO-VERIFICATION.md).

Both independent VM disks use signed, pinned **Fedora Kinoite 44.20260913.0**,
Plasma 6.7.5, Dolphin/Gwenview/Okular 26.08.1, Firefox 155 and Thunderbird
153.0.2. The original ISO deployment remains available for Atomic rollback.

## Install from ISO

The release artifact is a **bootable x86_64 installer ISO** with an offline Aven
payload and Fedora's native Anaconda installer and first-user setup.

The current experimental **Union 0.3.1** image contains the refined app frames,
500 emphasis and translucent dock. Download the complete 8.05 GB
[ISO from Cloudflare R2](https://aven-downloads.mechiland.workers.dev/releases/v0.3.1/Aven-Union-44-0.3.1-x86_64.iso)
and its [checksum file](https://aven-downloads.mechiland.workers.dev/releases/v0.3.1/Aven-Union-0.3.1-SHA256SUMS),
then verify:

```sh
sha256sum --check Aven-Union-0.3.1-SHA256SUMS
```

Write the image to a USB drive of at least 16 GB, or attach it as a virtual
optical drive. No reassembly is needed. See the [ISO guide](docs/ISO.md),
[Union installation evidence](docs/UNION-ISO-0.3.1.md) and
[release notes](https://github.com/mechiland/aven/releases/tag/v0.3.1).
Current Union visual scores remain pending; the earlier Breeze scores above
do not assess this ISO.

## Inspect the existing laboratory prototype

The live lab disks are `.cache/vm/stock.qcow2` and `.cache/vm/aven.qcow2`.
The [portable disk](output/aven-prototype-round04.qcow2) and
[source/evidence archive](output/aven-source-and-evidence-round04.tar.gz) have
build records and checksums in [output/BUILD.json](output/BUILD.json). To boot
the Aven guest when it is stopped:

```sh
python3 scripts/vm.py boot --name aven --gpu
```

Connect a VNC viewer to `127.0.0.1:5921` for Aven or `127.0.0.1:5920` for stock.
The native applications remain Dolphin, Firefox, Thunderbird and Gwenview.
Select a file in Dolphin and press **Ctrl+Alt+P** for quick preview; **Esc**
returns to Files. Images, PDFs, bounded text and common media use existing Qt/KDE
decoders. Preview does not edit the selected file.

See [how to try the prototype](docs/TRY.md) and the [before/after index](docs/COMPARISON.md).
Start with the [final critic report](docs/critic-round-04.md),
[current Chinese scale review](docs/typography-round04-findings.md), and [restore guide](docs/restore.md).
Scores come from inspected native framebuffers; no mockups are used as evidence.

## Laboratory

Requires Linux x86_64, accessible KVM, QEMU, xorriso, cpio, Python 3 and OpenSSH.
Run from this repository:

```sh
python3 scripts/fetch-base.py
python3 scripts/vm.py prepare
python3 scripts/vm.py install
# Installation powers the guest off. Inspect .cache/vm/stock.serial.log.
python3 scripts/vm.py boot --gpu
python3 scripts/vm.py ssh 'rpm-ostree status'
python3 scripts/vm.py screenshot evidence/stock/desktop.png
python3 scripts/sync-guest.py --guest stock
python3 scripts/vm.py ssh 'python3 ~/aven/scripts/seed-fixtures.py'
python3 scripts/vm.py ssh 'python3 ~/aven/photos/copy-fixtures.py --home "$HOME"'
python3 scripts/vm.py ssh 'python3 ~/aven/integration/prepare-packages.py --upgrade'
# Power off, then boot again to activate the stable deployment.
python3 scripts/vm.py ssh 'sudo systemctl poweroff'
python3 scripts/vm.py boot --gpu
python3 scripts/vm.py ssh 'python3 ~/aven/integration/native-apps.py --apply'
```

The VM uses a new 48 GB sparse virtual disk, 6 GB RAM, four virtual CPUs, a
loopback-only SSH port (stock 2222, Aven 2223), and loopback-only VNC (5920/5921).
`--gpu` uses virtio graphics and the host render node; omit for software rendering.
Screenshots are QEMU framebuffer captures, not mockups. GPU scanout uses a
lossless read-only VNC reader when QMP has no software surface. The evidence
capture script records which transport supplied the actual pixels.

`baseline/stock.ks.in` is a disposable VM automation harness. Its SSH key,
passwordless sudo and autologin are confined to this laboratory, **not distribution
defaults**. It installs the official signed ISO's stock OSTree payload. The local
ISO repository is trusted only after the signed image checksum passes.
The emulated audio device uses a silent host backend; playback progress and
decoding can be tested, but this harness does not establish speaker sound quality.

Capture the stock scenarios before applying any Aven preferences. Then shut
stock down cleanly and create an independent comparison disk:

```sh
python3 scripts/vm.py ssh 'sudo systemctl poweroff'
python3 scripts/vm.py clone
python3 scripts/vm.py boot --name aven --gpu
python3 scripts/sync-guest.py --guest aven
python3 scripts/vm.py --name aven ssh 'bash ~/aven/scripts/guest-session.sh python3 ~/aven/integration/apply-profile.py --decoration aven'
python3 scripts/vm.py --name aven ssh 'sudo systemctl reboot'
```

The Aven disk is independent, so later stock captures cannot alter Aven's data.
Large downloads, disks, private VM keys and logs stay in ignored `.cache/`.

The profile applies the Noto font stack first, then Dolphin and quick preview,
Firefox, Thunderbird, Gwenview, and the shared Aven surfaces and motion settings.
Close these applications before applying it. App installers seed preferences
without overwriting existing personal browser or mail profiles. The normal mail
launcher is online; the evidence mailbox is a separate fictional offline profile.
Configuration backups live in the guest's `~/.local/state/aven/` and the component
installers' recorded backup paths. OSTree rollback restores system deployments;
it does not undo preferences in `/etc` or the home directory.

Use [the paired baseline protocol](docs/baseline-protocol.md) and
[verification instructions](docs/verification.md) for capture, native operations,
scale checks and the independent critic. `scripts/capture.py` records an actual
Wayland/Qt probe, image hash, package versions and framebuffer provenance.

## Scope and evidence

The two guests must use the same files, application versions, viewport and scale
for direct comparisons. A clean installed mail app can be added to the stock
baseline if the official image has none; record the addition. Include Simplified
Chinese, Traditional Chinese, mixed punctuation, 100/125/150/200% scale checks,
real operations and motion inspection. A static screenshot cannot prove motion.

No redesign of Settings, installer, updater, login, or unrelated OS areas.
No application forks or generic macOS themes. Pass requires overall ≥8,
Chinese typography ≥8.5, and clear refinement in a three-second comparison.

Base release: [Fedora Kinoite 44](https://fedoraproject.org/atomic-desktops/kinoite/download/).

## Repository and release assets

Source, reports, capture metadata and still screenshots are versioned in Git.
Large VM/ISO artifacts, the complete source/evidence archive and raw motion PNG
sequences are distributed as GitHub Release assets. To run the full evidence
gate from a fresh checkout, extract the matching evidence archive and copy its
`aven/evidence/interaction/` directory into this repository; the recorded hashes
remain authoritative. The previously exported round 4 VM archive preserves the
exact assessed snapshot, while later ISO packaging changes have their own build
and installation verification records.
