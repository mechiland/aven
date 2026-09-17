# Aven Union prototype

The current running VM has the [Medium emphasis and dock revision (0.3.1)](UNION-DOCK-MEDIUM.md),
building on the [macOS 15 framework revision](UNION-SEQUOIA.md). Its screenshots,
profile bundle and limits are recorded there. The 0.2.0 disk export described
below is the earlier build and has not been rebuilt for these appearance changes.

This variant keeps Aven's focused Files, browser, mail, photos and Latin/Chinese
typography scope. It uses Fedora Kinoite 44 with the KDE SIG's Plasma 6.8 Beta
(RPM version 6.7.90) and an Aven Mist Union theme. Dolphin, Firefox, Thunderbird,
Gwenview and the existing Qt previewer remain the applications.

The current integration and evidence status is recorded separately as
`union_dock_medium_candidate` and `union_iso_031` in [STATUS.json](STATUS.json). The earlier round-4 and ISO
candidate-5 scores assess the Breeze prototype, not this Union variant.

## Try the built version

For a fresh installation, use the [Union 0.3.1 ISO](ISO.md). It includes the
current theme, Medium emphasis and translucent dock. The
[installation report](UNION-ISO-0.3.1.md) records its exact artifact and checks.

The local test image is
[`output/Aven-Union-0.2.0-x86_64.qcow2`](../output/Aven-Union-0.2.0-x86_64.qcow2).
On this Linux/KVM host, start it from the repository:

```sh
./scripts/run-union-vm.sh
```

Connect a VNC client to `127.0.0.1:5922`. The `aven` desktop logs in automatically.
This launcher uses its own writable working disk and SSH port `2224`; it does
not use the running r4 VM. Shut down through the desktop when finished.
This older exported artifact is a bootable VM disk; its lab launcher is separate
from the public Union 0.3.1 installer.

[`Aven-Mist-0.2.0.unionstyle`](../output/Aven-Mist-0.2.0.unionstyle) is also
packaged with KDE's `union-styletool`. It contains the native Union CSS theme;
the complete Aven profile additionally supplies colors, fonts, app configuration
and the Files compatibility launcher described below.

## Build and run

Start from the official Kinoite baseline described in [BUILD.md](BUILD.md).
The existing lab guest can be prepared from this branch:

```sh
python3 scripts/vm.py boot --name aven --gpu
python3 scripts/sync-guest.py --guest aven
python3 scripts/vm.py ssh --name aven 'python3 ~/aven/integration/prepare-union.py --stage'
python3 scripts/vm.py ssh --name aven 'sudo systemctl reboot'
```

The package script selects the installed Fedora 44 package counterparts from
the KDE SIG `kde-beta` repository, verifies repository checksums and RPM
signatures, and stages them with rpm-ostree. It adds `plasma-union` and its CSS
parser. This is a Fedora base with KDE SIG Beta replacements, not a stock Fedora
6.8 compose. Package versions and hashes are recorded in the guest's
`~/.cache/aven-union-platform/plan.json`.

After the desktop has restarted, close the focused applications and apply:

```sh
python3 scripts/vm.py ssh --name aven \
  'bash ~/aven/scripts/guest-session.sh python3 ~/aven/integration/apply-profile.py --style union --decoration aven'
python3 scripts/vm.py ssh --name aven 'sudo systemctl reboot'
```

The existing VNC endpoint is `127.0.0.1:5921`. [TRY.md](TRY.md) describes the
existing fixture locations and native Preview shortcut.

## Theme implementation

- `visual/union/aven-mist` is a native Union CSS style package. It inherits the
  installed Union Breeze controls and their interaction states, then adds Aven's
  control geometry, quiet borders, hover colors and surface corners.
- `integration/union_theme.py` generates the CSS variables from
  `visual/tokens.json` into `~/.local/share/union/styles/aven-mist`.
- The profile selects `widgetStyle=Union` and `unionStyle=aven-mist` through
  KDE's configuration interface. It checks that the real QtWidgets plugin and
  packaged Union base style exist before enabling the theme.
- Fontconfig, fractional font sizes, Chinese locale shaping and application
  layouts are supplied by the focused profile. See the current revision's guide
  for the Adwaita/Noto roles. Union does not add letter spacing to Chinese.
- Firefox and Thunderbird retain their focused Mozilla stylesheets. Union does
  not style their main interfaces. No new Settings, installer or login design is
  introduced.

### Plasma 6.8 Beta compatibility

The 6.7.90 QtWidgets adapter rendered Dolphin's `KUrlNavigator` with dark text
on a dark background. A narrowly scoped Qt stylesheet fixes that custom widget's
surface, text and border. The rest of Dolphin still uses the installed Union
plugin; no application or Union binary is forked.

`integration/union_theme.py` installs the same launcher for the desktop entry,
directory MIME handler, FileManager1 service and `~/.local/bin/dolphin`.
The last path matters: Dolphin's own New Window and FileManager1 implementation
launch the bare `dolphin --new-window` command. Desktop launch, D-Bus activation
and Ctrl+N were tested independently. Invoking `/usr/bin/dolphin` directly
bypasses this compatibility layer. Recheck and remove the shim when the upstream
adapter handles this control correctly.

Union's list-header alignment is set to the leading edge. Selected file rows
use a light blue background and a blue border so Dolphin's independently
painted ordinary and secondary text remains readable.

## Verification

Run `verification/union_probe.py` through the guest session wrapper. It reports
the actual Qt style class, theme hashes, versions and Union library mappings in
running native apps. These observations establish activation, not visual quality.

Real captures for this variant are stored in `evidence/aven/round-05`; deployment
and activation evidence is under `evidence/verification/union`. Chinese and
native-operation findings must be based on these new captures. No earlier
visual score carries over automatically.

The completed checks and their exact limits are recorded in
[`union/review.json`](../evidence/verification/union/review.json):

- 88 verification tests, 26 Files tests and 15 preview tests pass; the existing
  offscreen preview decode smoke also passes. These establish behavior, not
  visual quality.
- Native Files copy, move, Unicode rename, trash and restore preserve bytes.
  Native Ctrl+Alt+P opens Chinese text, and Escape returns focus to Files when
  no other application intervenes.
- Real SC and TC Files screenshots were inspected at 100%, 125%, 150% and 200%,
  including native UI text and mixed Latin/Chinese filenames.
- Native Firefox Chinese reading, local-only Thunderbird mail reading, Gwenview
  image navigation and EXIF orientation 6 were inspected. No message was sent.
- Formal stock-versus-Union scoring, the three-second differentiation judgment,
  the complete prose scale matrix and the full 17-operation/motion review remain
  pending. Scores and acceptance stay null.

The diagnostic images are retained alongside the final captures, with explicit
exclusion notes. One initial preview capture actually showed Firefox in front,
and an initial D-Bus launch exposed the missing PATH entry; neither is treated
as a successful preview or final Files capture.

Upstream references: [6.8 Beta announcement](https://kde.org/announcements/plasma/6/6.7.90/),
[KDE SIG Beta repository](https://copr.fedorainfracloud.org/coprs/g/kdesig/kde-beta/),
[Union documentation](https://api.kde.org/union-index.html).
