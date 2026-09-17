# Union typography candidate, round 06

The inspected macOS references are `15-Sequoia-Applications.png`,
`15-Sequoia-Mail.png`, `15-Sequoia-Safari-v18.png`, and
`15-Sequoia-Photos.png` in `/home/michael/Downloads/macOS15Screens`.
The inspected existing Union captures are
`evidence/aven/round-05/union-files-ready-1x.png` and
`evidence/aven/round-05/union-files-sc-final-1x.png`.

The reference UI uses a compact text hierarchy: ordinary sidebar rows and
toolbar labels have regular weight; window titles, section labels, and unread
senders carry selective emphasis. The current Union captures show larger UI
text and a particularly heavy current-location breadcrumb. The existing
Chinese capture is legible, but its size and dark breadcrumb compete with
the surrounding framework. The supplied macOS references contain no equivalent
Chinese UI, so they cannot establish a Chinese glyph or rendering match.

`roles.json` now requests a 13 logical px regular UI, 12 px secondary text,
11 px captions, 11 px semibold section labels, and 14 px medium window titles.
The point values assume 96 logical dpi; the reference PNG files contain no dpi
metadata. These values are a candidate to verify in native 1x and 2x captures,
not measurements of the source device's scale. Reading text remains 16 px Latin
and 17 px Chinese with its previous line heights.

Adwaita Sans replaces Noto Sans for Latin UI roles. It is an Inter variant
available as Fedora's `adwaita-sans-fonts`, licensed OFL-1.1; the running Union
guest already contains `50.0-1.fc44`. It provides real Regular, Medium, and
SemiBold instances. The choice is intended to bring the UI's compact, neutral
shapes closer to the inspected references; it is not a claim of identical
Apple glyphs. See the [GNOME source](https://github.com/GNOME/adwaita-fonts/)
and [Fedora package](https://packages.fedoraproject.org/pkgs/adwaita-fonts/adwaita-sans-fonts/).

Noto Sans remains an explicit document family and Latin fallback. Noto Sans
CJK SC, TC, and HK remain region-specific fallbacks; untagged Chinese uses SC.
Japanese, Korean, monospace CJK, and color emoji routing remain intact.
The Noto alias retains the original request's binding so a distribution's weak
Noto default cannot take precedence over the Adwaita UI choice. Explicitly
requested document faces remain ahead of generic defaults.

Grayscale antialiasing, slight hinting, native hints, and outline rendering
remain unchanged. Synthetic emboldening is disabled for the new UI family as
well as Noto. The same two installed config filenames and existing timestamped
backup workflow preserve rollback compatibility.

The isolated fontconfig audit passes 59/59 checks using read-only copies of
the running Union guest's font files and system font configuration, with the
two candidate files substituted only in the local copy. The full result is
`round06-font-resolution.json`. This checks matching and available weight
instances, not toolkit shaping or visual quality. In particular, Noto CJK has
no named 600 instance: a normal demibold query can select named Bold, whereas
`variable=true` can interpolate 600. The audit checks that interpolation is
available and does not assert that Qt selects it. No global weight remapping
or gamma adjustment is introduced.

Integration requirements: Qt must use `QFont.setPointSizeF` for fractional point
values, GTK must receive `Adwaita Sans 9.75`, native titles must request 500,
and browser/mail chrome must consume the UI role. The guest's active audit,
actual Chinese title shaping, UI clipping, and 1x/2x visual comparison remain
pending until root activates and captures the candidate. All quality scores
remain unassigned here.

The original title candidate requested 600. After inspecting the native round
06 captures, the title role was reduced to named Medium (500) to address the
visibly heavier Chinese portions of mixed-script titles. The rationale and
pending recapture are recorded in [the native review](round06-native-review.md).
