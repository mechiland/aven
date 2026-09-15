# Aven typography — first candidate

Status: the final round 4 focused prototype passes at **Chinese 8.5 / overall 8.33**.
All 16 current Aven SC/TC UI/prose captures and their canonical stock counterparts
were opened at original resolution across 100/125/150/200%; actual-scale checks
pass. See [current findings](typography-round04-findings.md) and the
[independent final critic](critic-round-04.md). The 42 font-resolution checks pass.
Native UI readability and reading/writing rhythm improve visibly; a dramatic
controlled-paragraph rasterization gain over stock is not established. Earlier
round 2/3 reports remain historical evidence.

Round 04 retains the fontconfig and QFont settings. Its [complete SC/TC matrix](typography-round04-findings.md) now contains 16 current Aven captures inspected against all 16 original stock counterparts, with matching runtime scales and package/base provenance; the independent current-round judgment is separate. Historical round 02 evidence is preserved. The [compose rhythm supplement](compose-rhythm-review.md) confirms a visible correction in a separate screenshot without awarding a new score.

## Font and size contract

| Role | Family | Size | Weight |
|---|---|---:|---:|
| UI, menus, filenames, toolbar labels | Noto Sans | 11 pt | 400 |
| Window title, selected section, short emphasis | Noto Sans | 11 pt | 500 |
| Secondary metadata | Noto Sans | 10 pt | 400 |
| Monospace | Noto Sans Mono | 10 pt | 400 |
| Owned Latin reading content | Noto Sans | 16 logical px; line height 1.65 | 400 |
| Owned Chinese reading content | Regional Noto Sans CJK fallback | 17 logical px; line height 1.75 | 400 |
| Emoji | Noto Color Emoji | Inherit surrounding size | Native |

These match `typography/roles.json` and the visual system's initial roles. At 96 logical DPI, 11 pt is about 14.67 logical pixels. Qt widget row heights remain toolkit-controlled. Reading metrics are applied to owned fixtures and preview content, and through narrowly scoped Thunderbird reading/compose styles. They are not a global paragraph override for application widgets or arbitrary web pages.

The initial CJK regular weight is 400, not a lighter weight selected to make screenshots look delicate. Dense characters need enough contrast at 100%. Use 500 sparingly for hierarchy; reserve 700 for real content emphasis. Noto's native weights handle emphasis without globally thickening strokes.

These are Aven's requested roles, not an override of every native control. KDE's current-location breadcrumb explicitly requests bold. The [native weight investigation](typography-bold-investigation.md) confirmed actual 700 shaping, distinct from 900; an isolated application-scoped fontconfig weight remap did not change Qt's selected outlines and was rejected. Regular UI remains 400.

## Fallback and Chinese regional forms

| Text language | Han fallback after Noto Sans | Monospace Han fallback |
|---|---|---|
| `zh-CN`, `zh-SG`, untagged | Noto Sans CJK SC | Noto Sans Mono CJK SC |
| `zh-TW` | Noto Sans CJK TC | Noto Sans Mono CJK TC |
| `zh-HK`, `zh-MO` | Noto Sans CJK HK | Noto Sans Mono CJK HK |
| `ja` | Noto Sans CJK JP | Noto Sans Mono CJK JP |
| `ko` | Noto Sans CJK KR | Noto Sans Mono CJK KR |

Noto Sans supplies Latin in mixed text; regional CJK faces supply Han and CJK punctuation. Emoji is the last explicit fallback. Fontconfig's generic `sans-serif`, `system-ui`, `monospace`, and `emoji` aliases select this stack. Explicit document font choices and serif content remain available. Do not replace web authors' styles or force every paragraph to sans-serif.

Regional glyph differences are real, even where Unicode characters are shared. Fontconfig uses region-style language tags; browsers and shaping engines also need correct document language. The HTML specimen tags SC, Taiwan, Hong Kong, and Japanese text separately. Plain text cannot declare its language: open the Traditional Chinese fixture in a `zh_TW` application/session, or explicitly choose TC for that content. An English-locale untagged filename deliberately uses SC. This is a policy choice, not automatic detection of Traditional Chinese. [Fontconfig language matching](https://fontconfig.pages.freedesktop.org/fontconfig/fontconfig-user.html), [Noto CJK formats and language selection](https://github.com/notofonts/noto-cjk/blob/main/Sans/README.md).

## Rendering candidate

`99-aven-rendering.conf` requests antialiasing, grayscale coverage (`rgba=none`), slight hinting, and native light hinting where available (`autohint=false`). Outline fonts avoid embedded monochrome strikes; color emoji retains bitmap support. The Noto Sans rules request no synthetic emboldening. Strong bindings preserve Latin Noto ahead of CJK fallbacks even if distribution aliases inserted a weak Noto family first. [Fontconfig configuration and bindings](https://fontconfig.pages.freedesktop.org/fontconfig/fontconfig-user.html).

Slight hinting emphasizes vertical grid fitting while preserving horizontal spacing better than full grid fitting. It is a starting candidate, not a guarantee: FreeType notes that light rendering may look softer and the native hinter can affect results. Grayscale avoids assuming an RGB/BGR panel order and is suitable for comparing fractional scales. At 100%, the critic must explicitly compare stroke clarity with stock. [FreeType light hinting reference](https://freetype.org/freetype2/docs/reference/ft2-glyph_retrieval.html).

No global FreeType stem-darkening or gamma environment hack is installed. Gamma, coverage blending, and text rasterization are partly toolkit responsibilities; a fontconfig file cannot make Qt and Gecko identical. FreeType explains why extra darkening without matching compositing can create heavy text. Its historical discussion is rationale for restraint, not a claim about every current toolkit. [FreeType rendering background](https://freetype.org/freetype2/docs/hinting/text-rendering-general.html).

No glyph scaling, aspect-ratio change, forced punctuation substitution, global `palt` feature, or added CJK letter spacing is applied. Preserve native fullwidth CJK punctuation and natural Latin advances; inspect quote pairs, brackets, ellipses, dates, paths, and paragraph wrapping. In owned HTML, language tags allow the browser's line-breaking rules to operate. A font stack alone cannot implement Chinese line breaking inside every application.

## Installation in the guest

Do this only **after stock baseline screenshots** are complete. Install the native packages listed in `typography/fedora-packages.txt` using the integrator's Atomic image/layering workflow. They provide Noto Sans, Noto Sans Mono, all five regional CJK faces, the CJK mono faces, and color emoji. The separate CJK mono VF package is necessary. Do not download Google Fonts subsets or install duplicate static and variable CJK families as a workaround. [Fedora Noto Sans](https://packages.fedoraproject.org/pkgs/google-noto-fonts/google-noto-sans-vf-fonts/), [CJK VF](https://packages.fedoraproject.org/pkgs/google-noto-sans-cjk-vf-fonts/google-noto-sans-cjk-vf-fonts/), [CJK Mono VF](https://packages.fedoraproject.org/pkgs/google-noto-sans-cjk-vf-fonts/google-noto-sans-mono-cjk-vf-fonts/), [Noto Color Emoji](https://packages.fedoraproject.org/pkgs/google-noto-emoji-fonts/google-noto-color-emoji-fonts/).

From the repository in the guest:

```sh
sudo python3 typography/install.py --root /
fc-cache -f
python3 typography/audit.py --active --output evidence/typography/guest-font-audit.json
```

For an image staging tree, use `--root /path/to/image-root`. The installer writes only the two Aven files under `etc/fonts/conf.d`, preserving changed previous versions beside them. It does not modify host font settings unless explicitly aimed at the host root. Native packages belong in the image's existing package workflow. Restart applications after changing fonts; Plasma's font roles, GTK integration, and application-specific defaults belong to the shared integrator.

Per-user fontconfig files are loaded at the distribution's `50-user.conf` position. A filename starting with `99` in a user directory still precedes later system rules. Install these system-wide files in `/etc/fonts/conf.d` so the rendering rule runs late; inspect active matching afterward. Flatpak applications may expose a different fontconfig environment and must be checked in the actual sandbox too.

The isolated development check is:

```sh
python3 typography/audit.py --output /tmp/aven-font-audit.json
```

This appends the candidate to the host's config without installing it and checks fontconfig's Latin/CJK/mono resolution, SC/TC/HK/JP/KR routing, regular/medium/bold matches, CJK punctuation, and color emoji support. It catches missing families and wrong matching, but does not reproduce the guest's exact config order. `--active` in the guest is the authoritative fontconfig check. Neither mode proves the actual face instance selected by Qt; the [native weight investigation](typography-bold-investigation.md) demonstrates why separate shaping and outline checks matter. Neither audit validates widget clipping, perceived sharpness, or emoji sequence appearance; those require screenshots.

## Native screenshot matrix

Set scaling through the Plasma Wayland output configuration. Keep browser page zoom at 100%. Do not set `QT_FONT_DPI`, `QT_SCALE_FACTOR`, `GDK_SCALE`, or an Xft DPI override as a session-wide substitute for compositor scaling. Qt 6 uses device-independent geometry and accepts fractional scaling; `QT_SCALE_FACTOR` is a debugging/testing override. [Qt High DPI](https://doc.qt.io/qt-6/highdpi.html).

| Scale | Required comparisons |
|---:|---|
| 100% | Latin and SC/TC UI at 11 pt; dense strokes; filename truncation; real paragraphs |
| 125% | Same logical size; glyph edge consistency, baseline jitter, menu clipping |
| 150% | Same set; browser/Qt apparent weight and size balance |
| 200% | Same set; paragraph comfort, fine punctuation, image metadata, emoji |

For **each** scale, capture stock and Aven with the same VM output, application version, language, content, window size, and scroll position:

1. Dolphin in Chinese (`zh_CN`, then `zh_TW`): sidebar, breadcrumbs, mixed filename list, rename field, copy progress.
2. `fixtures/typography/specimen.html` in the selected browser: all SC, TC, and HK paragraphs; the language-form row; weight ladder; inverse text; emoji. Preserve original PNG pixels for inspection, with full-page capture or multiple scroll positions.
3. Text preview: the two supplied `.txt` fixtures. Check wrapping, fallback, and metadata clipping.
4. Mail: real Chinese reading and composition fixtures; toolbar and body in one image.
5. Photos: Chinese filenames and metadata over light and dark image surroundings.

Use native screenshots for judgment. Resized contact sheets help navigation, but they blur the evidence needed to score typography. Record compositor scale and screenshot pixel size with each capture; the specimen exposes `devicePixelRatio` and viewport size for supporting browser diagnostics. This does not prove the compositor scale by itself because browser zoom also changes it.

Score Chinese only after inspecting full SC/TC paragraphs, dense UI labels, and regional probes. A pass requires Chinese ≥8.5 and the overall product score ≥8; this document awards neither. If the first candidate looks weak at 100%, compare one change at a time (UI 11→11.5 pt, reading 17→18 px, or hintslight→hintnone at HiDPI) using fresh native screenshots. Avoid tuning an English-only contact sheet.
