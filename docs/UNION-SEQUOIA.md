# Union · macOS 15 reference revision

The running VM now includes the [0.3.1 Medium/dock follow-up](UNION-DOCK-MEDIUM.md).
This document records the preceding 0.3.0 appearance revision, which changes
Files, browser, mail, photos, preview, and their shared typography/decoration.
The signed Fedora Atomic deployments and pinned stock fallback remain intact.
The desktop, login, Settings, and installer have not been redesigned.

## References and resulting changes

All eight original PNGs in `/home/michael/Downloads/macOS15Screens` were inspected.
Applications, Mail, Safari v18, and Photos supplied the main framework references;
Desktop, Accents, Settings, and Spotlight informed common surfaces and hierarchy.
The references contain no equivalent Chinese interface, and their device scale
is not established by PNG metadata. No exact Chinese rasterization match is claimed.

| Area | Implemented revision |
| --- | --- |
| Typography | Adwaita Sans Latin UI at 9.75 pt / 13 logical px; 12 px secondary text; 14 px Medium titles; region-specific Noto CJK fallback. Reading text retains 16 px Latin / 17 px Chinese. Fractional Qt sizes are serialized with `setPointSizeF`. Synthetic bold is disabled. |
| Windows | Approximately 10 px corners, 12 px left-side traffic-light buttons, compact 28 px native titlebar, neutral shadows and inactive states. Native button commands and resize behavior remain. |
| Shared surfaces | White content, light-gray chrome/sidebar, blue selection, compact icon-only toolbars and blue folder/place assets. |
| Files | 184 px places pane, 18 px sidebar/toolbar icons, compact rows, 64 px file icons and 144 px previews. Scoped native-widget compatibility fixes retain readable location surfaces under Union. |
| Browser | 52 px integrated address/header row, centered address field, tabs below it, native New Tab/All Tabs controls. A sole ordinary tab can collapse; multiple/private/grouped/pinned tabs retain navigation. |
| Mail | Compact three-pane layout, quiet separators, selective sender emphasis, icon toolbar, integrated header and rounded client-side corners. Existing accounts and messages are retained. |
| Photos | 208 px folder pane, five-column 168 px gallery at the tested width, filenames hidden, image aspect ratios preserved, neutral location bar/sidebar and a readable horizontal scrollbar. |
| Preview | Compact footer and buttons; explicit document typography preserves Chinese reading size after shrinking UI fonts. |

Font details and actual observations are in the [reference review](../typography/round06-reference-review.md)
and [native review](../typography/round06-native-review.md). KWin reads its title
font through `QFontDatabase::TitleFont`; the live integration now refreshes the
platform-theme font cache before reconfiguring KWin. A plain reconfigure left
the old title glyphs on screen during this round. See the
[KWin implementation](https://github.com/KDE/kwin/blob/Plasma/6.7/src/decorations/settings.cpp).

## Real screenshots

These are original native framebuffer captures, with SHA-256 and RFB metadata
in same-name JSON sidecars. They are not mockups or composited comparisons.
The VM was inspected at 1920×1200 / 1× and 3840×2160 / 2×, then returned to 1×.

| State | Screenshot |
| --- | --- |
| Starting Union appearance | [Before](../evidence/aven/round-06/before-awake.png) |
| Files, final title after fresh boot, Simplified Chinese | [2×](../evidence/aven/round-06/files-sc-reboot-2x.png) |
| Files, Traditional Chinese UI, earlier title weight | [2×](../evidence/aven/round-06/files-tc-final-2x.png) |
| Browser, final controls | [1×](../evidence/aven/round-06/browser-sc-accepted-1x.png) |
| Browser, two tabs after reboot | [2×](../evidence/aven/round-06/browser-reboot-2x.png) |
| Mail, actual Chinese message | [1×](../evidence/aven/round-06/mail-current-1x.png) |
| Mail, empty native compose window | [1×](../evidence/aven/round-06/mail-compose-accepted-1x.png) |
| Photos gallery after reboot | [2×](../evidence/aven/round-06/photos-reboot-2x.png) |
| Chinese text preview | [1×](../evidence/aven/round-06/preview-text-accepted-1x.png) |
| Image handed from Preview to Gwenview | [1×](../evidence/aven/round-06/photos-view-accepted-1x.png) |

The [evidence index](../evidence/verification/union-sequoia/review.json) identifies
diagnostic captures separately. The word `accepted` in some filenames means a
capture after integration, not formal visual acceptance. In particular,
`preview-sc-final-2x` is an erroneous invocation, `photos-handoff-accepted-1x`
was captured before the target window appeared, and several title/cache captures
were stale or dimmed. They must not be used as final appearance evidence.

## Verification and remaining differences

The active guest passes 59 font-resolution checks. Existing verification tests
pass 88/88, Files tests 26/26, and Preview tests 15/15 in the guest with Qt.
All 27 QtSvg decoration slices pass their geometry check. The real native Union
plugin is loaded by Dolphin and Gwenview. Guest reboot and configuration
persistence were checked; no deployment or package changes were made this round.

Native New Tab, multi-tab display, URL suggestions, maximize/restore/minimize,
mail reading/empty composition, Preview text/Escape and image/Enter handoff were
exercised. The image handoff preserved EXIF orientation 6. Mail inspection uses
the existing fictional local demo profile; no message was sent. A complete
operation/motion review and fractional-scale matrix were not repeated.

The result is closer in density, hierarchy, colors, corners, and Mozilla header
structure. It is not a 1:1 replica. Important remaining differences:

- Dolphin and Gwenview retain native separate title/tool/location rows. The
  current-location breadcrumb forces bold and is still too dark in Chinese.
- Noto CJK and Adwaita have different glyph shapes and rasterization from Apple's
  fonts. Small Chinese text at 1× remains denser than Latin. Supplied references
  cannot establish an equivalent Chinese match.
- Gwenview retains its folder/device tree, clipped long device names, thumbnail
  bevels and filmstrip. Its native model does not offer a photo-only flat sidebar.
- Small sidebar assets can resolve to filled folders at 2×; their weight is not
  yet identical across scales. Native and Mozilla shadows also differ.
- Dynamic 1×→2× changes exposed a decoration rasterization artifact; fresh-boot
  captures are the authoritative 2× title reference.

Overall/Chinese scores, the three-second differentiation judgment, and formal
acceptance remain null. Earlier Breeze/ISO and Union 0.2 results do not score
this revision.

## Apply and recover

The existing running session on VNC `127.0.0.1:5922` has this revision. Its
writable disk is `.cache/vm/union-preview/session.qcow2` in the main checkout.
The exported `Aven-Union-0.2.0-x86_64.qcow2` and public 0.1 installer ISO are
unchanged; starting from a fresh copy of that export requires this profile update.

The [complete profile source bundle](../output/Aven-Union-0.3.0-profile.tar.gz)
contains the integration, native assets, app styles and this guide.
On an already prepared Union Atomic guest, unpack it into `~/aven`, close the
focused applications (including Dolphin's background FileManager1 process), then:

```sh
bash ~/aven/scripts/guest-session.sh python3 ~/aven/integration/apply-profile.py \
  --style union --decoration aven --refresh
```

Log out/in or reboot before comparing fonts. `--refresh` updates managed layouts
and appearance preferences while retaining account/message/browser data. The
[native Union package](../output/Aven-Mist-0.3.0.unionstyle) contains only the
Union CSS theme, not the fonts, window decoration or Mozilla application profiles.

The profile creates timestamped focused snapshots under `~/.local/state/aven`.
Shared rollback now includes native theme assets and compatibility launchers,
so restoring an earlier same-ID theme restores its bytes as well as its name.
For this lab session, the pre-revision archive is
`~/.local/state/aven/sequoia-before/appearance.tar.gz`, with both original
fontconfig files alongside it. Restore only the intended configuration/chrome
and asset files from that archive, not whole mail/browser data directories over
subsequent user data. The existing `verification/restore_profile.py` can plan
and restore its focused snapshots; app-profile recovery remains separate.
Live rollback was not exercised in this appearance task.
