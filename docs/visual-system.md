# Aven Mist — focused visual system

The visual system is installed and booted. The independent round 4 comparison
scored visual coherence **8.3**, with a positive three-second judgment. The final
focused prototype passes overall 8.33 / Chinese 8.5, recorded in `STATUS.json`;
native Chinese screenshots and observed interaction remain the evidence.

## Intent

Warm paper for reading, pale mineral surfaces for navigation, deep jade for the
current action, and dark graphite text. The distinction should come from a small
number of consistent decisions across Files, browser, mail and photos. Large
quiet fields in the original Estuary wallpaper leave room for application
windows. No gradients, glass, or ornamental borders are added to app content.

The font stack belongs to `typography/`. The two agents agreed on Noto Sans 11pt
Regular for UI, 11pt Medium for titles, and 10pt for genuinely secondary text.
Chinese and Latin UI retain the same nominal size; owned reading surfaces may
use 16px Latin at 1.65 line height and 17px Chinese at 1.75. Neither prose target
is forced into native menu or file rows. These sizes require screenshot review.

## Minimum tokens

The machine-readable source is [`visual/tokens.json`](../visual/tokens.json).

| Role | Value | Use |
| --- | --- | --- |
| Content | `#FDFCF9` | Files, messages, owned reading surfaces |
| Chrome | `#F1F3EF` | Title, navigation and tool surfaces |
| Alternate content | `#F7F7F3` | Restrained row alternation |
| Raised | `#FFFFFF` | Menus and controls |
| Main text | `#26342F` | Labels, names, prose |
| Secondary text | `#65706A` | Metadata |
| Accent | `#326B60` | Selection and keyboard focus |
| Hover | `#E5ECE6` | Pointer feedback |
| Boundary | `#D7DDD5`, 1px | Necessary separation |
| Spacing | 4, 8, 12, 16, 24, 32px | Related to separate groups |
| Control target | 32–36px | Native geometry where configurable |
| Corner target | 4, 6, 10, 12px | Small controls through preview |
| Icons | 22px toolbar/sidebar, 48px folders, 96px file previews, 240px photo grid | Retain application icon identity |
| Title region | 38px | Original optional Aurorae frame |

The color scheme supplies native KDE color roles. Breeze remains the Qt style.
Tokens do not imply that stock Breeze exposes arbitrary corner, spacing or row
height controls. Do not use global QSS or an application fork to force those
targets. Document any visible mismatch in the critic round.

## Assets and installation contract

Run `python3 visual/generate_assets.py` after changing generated asset inputs.
The generator only writes under `visual/`. The integrator installs these paths
in the image or the test user's XDG data directory:

| Repository source | System destination | Activation |
| --- | --- | --- |
| `visual/color-schemes/AvenMist.colors` | `/usr/share/color-schemes/AvenMist.colors` | `plasma-apply-colorscheme AvenMist` in guest session |
| `visual/icons/Aven/` | `/usr/share/icons/Aven/` | `kdeglobals`, group `Icons`, `Theme=Aven` |
| `visual/wallpapers/AvenEstuary/` | `/usr/share/wallpapers/AvenEstuary/` | Plasma image wallpaper path to its `contents/images/3840x2160.svg` |
| `visual/aurorae/Aven/` | `/usr/share/aurorae/themes/Aven/` | Candidate: `org.kde.kdecoration2`, `library=org.kde.kwin.aurorae`, `theme=__aurorae__svg__Aven` |

For reversible per-user testing, substitute `~/.local/share/` for `/usr/share/`.
Only the root integrator changes Plasma/KWin configuration. There is deliberately
no global theme, login screen, splash screen, Settings, installer or updater asset.

### Files icons

The Aven icon theme overrides only the common folder, Documents, Downloads,
Pictures and Home places. A quiet jade body and a dark semantic glyph distinguish
them. Every other icon inherits Breeze, then hicolor. Application identities and
native action symbols are preserved. Inspect the glyphs at 22px and 64px; simplify
them if the smaller rendering becomes unclear.

### Optional window decoration

An original vector Aurorae frame uses left-aligned titles, monochrome buttons on
the right, a 10px outer corner, 1px boundary and restrained vector shadow. Close
only acquires a muted red surface when hovered or pressed. There are assets for
all optional button types so customizing the titlebar does not remove controls.
Transparent mask slices define the rounded outer edge. Opaque client content and
full-screen/maximized behavior must be checked in the actual compositor.

The candidate is maintained as a short Python generator plus standard SVG/rc
files; it does not add executable QML or a KWin plugin. Select it only as a tested
round candidate. If native resizing, fractional scaling or maximization fail,
keep the Breeze decoration using Aven's colors and fix the SVG before reevaluation.

### Motion integration targets

Aim for immediate feedback: hover 100ms, menus 120ms, windows 160ms, preview 140ms,
image transitions 120ms, overview 180ms, with ease-out motion. KWin's native effect
settings take precedence where an effect does not expose duration. Keep one
window opening/closing effect; disable wobble, magic-lamp distortion, desktop
cubes, fall-apart and distracting pointer effects. Preserve useful overview and
ordinary focus cues. A reduced-motion setting must remove motion while retaining
state feedback. Static screenshots cannot verify this section; capture short
screen recordings or observe the guest directly.

## Review obligations

Inspect a stock/after pair at the same resolution, scale, window size, content and
locale. Required visual checks: active/inactive/maximized frames; Chinese folder
names and punctuation; selection contrast; sidebar density; thumbnail clarity;
browser tabs/address bar; mail list/body/compose; image viewer controls; menu and
preview focus. Repeat at 100%, 150% and 200% where the guest supports them.

The original wallpaper and native application surfaces have now been inspected
in stock/Aven framebuffer pairs. Earlier asset-only checks remain separate from
those OS comparisons. Read `critic-round-03.md` for exact visible strengths,
remaining native limitations, scores and screenshot references.

## Native interface references

The palette uses KDE's standard color-role groups, following the upstream
[Breeze light scheme structure](https://github.com/KDE/qqc2-breeze-style/blob/master/style/BreezeLight.colors).
The decoration follows KDE's documented SVG element names, button states and
layout keys in [Aurorae window decorations](https://develop.kde.org/docs/plasma/aurorae/).
The narrow theme inheritance uses the standard
[icon theme specification](https://specifications.freedesktop.org/icon-theme-spec/latest/).

## License

Original Estuary wallpaper: CC0-1.0. Original Aven theme assets, tokens and
generator: MIT. No third-party theme assets are bundled; installed Breeze icons
are inherited at runtime under their upstream license.
