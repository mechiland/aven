# Union 0.3.1 ISO

This release packages the [macOS 15 framework revision](UNION-SEQUOIA.md) and
[500 emphasis / translucent dock revision](UNION-DOCK-MEDIUM.md) for a fresh
installation. It is an experimental Plasma Beta prototype. The current Union
visual score and three-second differentiation judgment remain pending; the
older Breeze scores are not reused.

## Artifact

| Field | Value |
| --- | --- |
| Image | `Aven-Union-44-0.3.1-x86_64.iso` |
| Bytes | `8051228672` |
| SHA-256 | `59d81e2afb1c7241c274f961ae83cb13dd54d77a15459b266c87c1f458ef23eb` |
| Runtime source commit | `3cea3e1` (clean isolated build checkout) |
| Fedora base | `44.20260913.0` |
| Base commit | `be803f3e3bcdcc54885264702655e6e071864504154bc46044a08cc2aa2ce5df` |
| Union layered commit | `fbd330e4728599c337170d1b79608a64c1a6d989982554a4fd82a5ccdfa51026` |
| Update origin | `fedora:fedora/44/x86_64/kinoite` |

The [build manifest](../output/Aven-Union-44-0.3.1-x86_64.json) preserves the exact
embedded source inventory. Its `boot_install_verified: false` is the immutable
build-time state; later runtime verification belongs to the evidence below.
The release commit also includes external audit tools, website and documentation
that were added after the runtime source was frozen.

The image preserves Fedora's installer runtime and BIOS/UEFI boot structures.
It installs the tested Union tree offline, then imports the signed base and all
103 rpm-ostree package-cache refs. The origin records five named package requests,
two exact local additions and 84 exact local replacements. The Fedora base
signature is checked during installation. The locally assembled Union layer is
not signed by Fedora.

## Validation

The [media audit](../evidence/verification/union-iso-031/media-audit.json) passes
with no errors. Actual BIOS and UEFI optical boots reached Fedora Anaconda.
The public Chinese graphical installer completed offline on a fresh 48 GiB
virtual disk, without a private Kickstart overlay. Fedora's native first-user
setup and login automatically applied the Union profile.

Independent [first-boot](../evidence/verification/union-iso-031/independent-review.json)
and [second-boot](../evidence/verification/union-iso-031/second-boot-review.json)
audits pass: all 186 embedded files match, all 68 font checks pass, and all 103
package-cache refs are present. The second UEFI boot used only the installed
disk. First-login marker/log hashes and modification times, fonts and actual
Dock properties remained unchanged. The online second boot let Discover advance
the signed Fedora tracking ref to `44.20260917.0`; the running base and layer
still match the exact release identities above.

The [native workflow index](../evidence/verification/union-iso-031/native-workflow.json)
links inspected, unmodified framebuffer captures of installation, first login,
Chinese Files, PDF Preview and handoff to Okular, Chinese/Latin browser content,
HTTPS browsing, Thunderbird account setup and Gwenview photo display. Mail
sending/receiving was not tested on this fresh account. The disposable SSH/sudo
audit fixture was added only after observing the first desktop and is absent
from the ISO. Temporary capture-related power-management changes were restored.

All 116 external verification tests and 15 download Worker protocol tests pass.
These packaging and native smoke results do not establish a new visual score.

## Download and hosting

The [single ISO download](https://aven-downloads.mechiland.workers.dev/releases/v0.3.1/Aven-Union-44-0.3.1-x86_64.iso)
is stored in the dedicated Cloudflare R2 bucket `aven-releases`. A read-only
Worker streams it with byte-range support for resumable downloads. The
[website](https://aven-website.mechiland.workers.dev) links to the same immutable
versioned object. See [ISO.md](ISO.md) for hash verification and installation.

All 240 uploaded parts were compared against local MD5 values, and the completed
multipart ETag and object size match. Public download headers, beginning/middle/end
ranges, conditional requests, checksum file and build manifest are verified in
[the public download report](../evidence/verification/union-iso-031/public-download.json).

The download Worker exposes only the configured published release prefix.
Uploads use separate temporary authenticated infrastructure; no upload token
or upload route is shipped in the public Worker or website. The ISO is kept
out of Git; GitHub Release carries its checksum and build manifest.

## Limits

- The native KIO current-location breadcrumb still requests Bold. Managed
  emphasis uses 500; arbitrary web/document headings retain their own weights.
- Application icons, the retained system tray and native app-specific controls
  still differ from macOS. This release does not claim pixel parity.
- A fresh Chinese account has English profile-created folders alongside native
  Chinese standard folders. Gwenview's initial small window clips some native
  sidebar labels; both remain polish work.
- Fractional-scale, animation, the full operation matrix and a fresh scored
  stock/Union visual comparison are not repeated for this ISO.
- Fedora Atomic origin, signed base and package request metadata are preserved.
  An upgrade transaction and a rollback execution are not exercised in this
  release round. A fresh install starts with one deployment; later successful
  updates retain the preceding deployment.
- Plasma 6.8 Beta is locally pinned. Future Fedora/application upgrades require
  another compatibility check. No separate Aven system update channel is added.
