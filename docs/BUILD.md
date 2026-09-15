# Booted prototype build

The prototype consists of two independent QEMU disks and the source in this
repository. Stock was installed, booted and captured before Aven preferences
were applied to a full, powered-off clone. Neither guest depends on a backing
file in the other guest.

## Pinned platform

| Component | Captured version |
| --- | --- |
| Base | Fedora Kinoite 44.20260913.0, x86_64 |
| Plasma | 6.7.5 |
| Dolphin, Gwenview, Okular | 26.08.1 |
| Firefox | 155.0 |
| Thunderbird | 153.0.2 |
| Qt / PySide | 6.11.2 |

Official ISO: `Fedora-Kinoite-ostree-x86_64-44-1.7.iso`.
Its SHA-256 is
`4a944312b4e861ab625fd9786957174ef122a8a406bbb54caba7665e0d9f0e92`.
The checksum signature was verified with Fedora's release 44 key
`36F612DCF27F7D1A48A835E4DBFCF71C6D9F90A6`.

The current base commit is
`be803f3e3bcdcc54885264702655e6e071864504154bc46044a08cc2aa2ce5df`.
The identical layered commit in both guests is
`37fc46fea2b1059cdbc35c4ff88a2b40ede7fcc105cca76693f11cc4cdffd551`.
The requested layers are `glibc-langpack-zh`, `gwenview`, `okular`,
`python3-pyside6` and `thunderbird`.

The original bundled Gwenview Flatpak failed to load `libraw.so.24`. Both guests
therefore use the matched native package. The broken duplicate launcher was
removed before cloning; application data was retained. This choice is recorded
in the baseline and reproduced by `integration/native-apps.py`.

## Build and runtime evidence

- `evidence/verification/round04-install.log`: full profile installation before
  the current reboot.
- `evidence/aven/round-04/desktop-1x.json`: actual post-boot framebuffer, runtime
  probe, versions, hashes and display scale.
- `evidence/verification/stock-atomic-final-v2.json` and
  `aven-atomic-final-v2.json`: read-only platform health checks. SELinux is
  enforcing; rpm-ostreed is active; the signed deployment is pinned and booted.
- `docs/STATUS.json`: critic rounds, acceptance scores and remaining work.

The two guests show the same stock `mcelog` virtual-CPU failure and root-remount
warning. Aven introduces no additional failed service in this check. The first
health report's combined `findmnt` invocation was invalid; the `v2` reports use
separate target queries. The earlier report is retained as diagnostic history.

The original 44.1.7 deployment remains listed for rollback. A live Atomic
rollback has not been performed. Deployment rollback and user-preference
restoration are different operations; use [restore.md](restore.md) for the latter.

## Scope and maintenance

The profile changes fonts, per-user application defaults, the focused native
desktop surfaces, and narrow motion settings. It adds one small read-only Qt
preview container through Dolphin's native service-menu action. It contains no
application fork, replacement file manager, browser, mail or photo application.

Firefox and Thunderbird use small unsupported chrome stylesheets. Review their
selectors against each application update and inspect real read/compose/browser
screenshots. Native Breeze control geometry and Gwenview's 250 ms image fade
remain upstream behavior. The regular UI uses Noto Sans 400; native location
emphasis uses genuine 700. No failed font remapping workaround is installed.

The VM's automatic login, test user, passwordless sudo, SSH authorization and
disabled idle lock belong to the laboratory harness. They are not distribution
defaults. The emulated audio output is silent; decoded frames and playback
progress do not establish speaker sound quality. Motion recordings sample
actual VM frames and cannot establish physical 60/120 Hz frame pacing.

## Portable handoff

[TRY.md](TRY.md) describes the existing laboratory guest and a separate writable
overlay for the exported disk. The export is a full independent compressed
QCOW2, created after guest shutdown. `output/export-record.json` records the
conversion and original disk identity; `output/BUILD.json` records final hashes,
virtual-content comparison and the acceptance evidence.

The source/evidence archive excludes `.cache`, VM private keys, the official ISO
and all QCOW2 files. Extract it beside the portable disk to retain the report and
screenshot links. The installed preview and Mozilla style files were also
checked against the final source, including both normal and offline mail
profiles: [runtime hashes](../evidence/verification/round04-runtime-source-hashes.json).
