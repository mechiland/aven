# Browser integration — Firefox

Native Firefox 155 is installed and booted in both guests. Round 4 browser
coherence scored **8.4** from inspected paired SC/TC reading and real HTTPS
browsing. Native download/reveal and portal selection pass; the final review is in
[critic-round-04.md](critic-round-04.md).

Local verification completed: isolated-profile creation, private permissions,
idempotent install preserving changed preferences, explicit refresh preserving
unrelated preferences, refusal of an unmarked profile, and refusal while Firefox's
profile lock is held. These checks validate installer behavior, not appearance.

## Choice

Keep **the native Firefox shipped in Fedora Kinoite 44**. This gives Aven a mature
browser while retaining Fedora's packaging and update path. Record the actual
installed RPM version in the stock/Aven evidence; both comparison guests must
use the same build. Firefox's system theme, document-font controls and independent
profiles provide the integration points needed here. [Mozilla theme help](https://support.mozilla.org/en-US/kb/use-themes-change-look-of-firefox),
[font preferences](https://support.mozilla.org/en-US/kb/change-fonts-and-colors-websites-use),
[profiles](https://support.mozilla.org/en-US/kb/profile-management).

| Candidate | Practical fit | Decision |
| --- | --- | --- |
| Native Firefox | Existing base browser; independent profile; GTK system colors and KDE portal dialogs | Select for the first prototype |
| Chromium | Mature alternative with documented GTK theme integration | Keep as a future compatibility option; a second browser adds packaging and QA work without improving this focused prototype |
| Falkon | KDE-native Qt application with tabs, bookmarks and history | Prefer Firefox for this prototype's browser baseline; Qt uniformity alone is insufficient reason to change browsers |

Chromium's supported GTK mode reads colors from GTK widgets. Falkon's project
documents its native browser features. The selection above is Aven's engineering
judgment, not a claim that either alternative failed a measured compatibility
test. [Chromium GTK integration](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/linux/gtk_theme_integration.md),
[Falkon](https://apps.kde.org/falkon/).

## Implemented defaults

`browser/install.py` reads `typography/roles.json` and records the
`visual/tokens.json` palette dependency. It creates only an Aven-owned profile and
launcher in the explicitly supplied guest home:

- `~/.local/share/aven/firefox/`: isolated profile, private directory permissions.
- `~/.local/bin/aven-browser`: invokes `/usr/bin/firefox --profile …`.
- `~/.local/share/applications/org.mozilla.firefox.desktop`: native Firefox identity
  and icon, bound to the actual Wayland application ID. The older Aven entry is
  hidden compatibility for saved associations.

The browser uses the upstream **System theme**, normal density, the shared native
window titlebar, and the KDE portal for Open/Save dialogs. Generic sans-serif
defaults resolve to Noto Sans for Latin, Noto Sans CJK SC for Simplified Chinese,
TC for Taiwan Traditional Chinese, and HK for Hong Kong Traditional Chinese.
Latin monospace defaults to Noto Sans Mono. Fontconfig owns the remaining fallback
and emoji behavior. CSS-authored fonts, line heights, font sizes, page zoom, serif
faces and minimum sizes remain available to each site. The quiet new tab page
keeps search and shortcuts and removes sponsored cards and story recommendations.

These defaults are seeded into `prefs.js`, **not enforced on every launch**.
People can change them normally in Firefox. Re-running without `--refresh`
preserves their choices. `--refresh` explicitly reapplies only the listed Aven
defaults and requires the profile to be closed. The installer takes Firefox's
profile lock and refuses to adopt an existing unmarked directory. It never reads
or imports other browser profiles and does not register this as the default
browser by itself.

A small `userChrome.css` supplies palette variables for normal light windows.
It does not change browser layout or website styles. This unsupported Mozilla
customization requires review on browser upgrades. Normal Firefox protection,
extension signing, search and update preferences are retained.

## Integrator dependencies

Root owns and must supply:

1. Noto packages/fontconfig from `typography/`; refresh font cache before launch.
2. Shared GTK Breeze configuration with `gtk-font-name=Noto Sans 11`, Aven's
   palette, and Plasma's normal GTK settings bridge. Firefox UI fonts inherit GTK.
3. Working `xdg-desktop-portal` and `xdg-desktop-portal-kde` in the user session.
4. Shared KWin window decoration/motion; no browser-specific animation hack.
5. Panel pin `applications:org.mozilla.firefox.desktop`. The shared integration
   sets this desktop entry as the HTTP/HTTPS and HTML handler through native GIO,
   then reads back each association. Fedora's `xdg-settings` KDE path currently
   invokes an unavailable unversioned `qtpaths`, so it is not used here.

Firefox's system theme alone retained a cool-colored toolbox. The small palette
stylesheet corrected that visible mismatch in round 3. Private, dark and high
contrast windows retain their native styling.

## Activate after the stock baseline

Run as `aven` in the Aven comparison guest, with the repository copied there:

```sh
python3 browser/install.py --home "$HOME"
update-desktop-database "$HOME/.local/share/applications"
"$HOME/.local/bin/aven-browser" http://127.0.0.1:8765/index.html
```

For a later preference revision, close Firefox, then run the installer with
`--refresh`. A regular repeat without that flag only repairs the launcher and
retains existing browser preferences. Exit Firefox before rolling an Atomic
deployment back; do not use `--allow-downgrade` on the profile. Profiles are mutable
user data and do not roll back with OSTree deployments.

To stop using Aven's profile, choose the stock Firefox launcher/default handler.
Retain the Aven profile if it contains user data. Its files can be archived after
closing Firefox; removing the two Aven launcher files leaves Fedora's native app
intact. Do not delete another browser's profile.

## Reproducible browsing fixture

The two original Chinese reading pages in `fixtures/browser/` are ordinary HTML
documents, not replacement browser UI. They have long SC/TC paragraphs, a real
title reflected in the browser tab/window, numbers, Latin text, Chinese
punctuation, navigation, a download link and a native image file input. Their
author CSS uses generic `sans-serif` so browser/fontconfig fallbacks are visible.
The small CSS landscape is explicitly a route diagram, not a photograph or OS
screenshot. It is identical in both comparison guests.

Serve the **same bytes** inside each guest:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory fixtures/browser
```

Use stock Firefox before any Aven installation for the stock baseline. Capture
both `/index.html` and `/traditional.html` at the same window size and scale.
Also visit real public Chinese and English websites in both browsers; a controlled
fixture alone cannot establish everyday web compatibility. The fixture has no
JavaScript and never uploads selected images; its external Mozilla links are
ordinary web navigation.

## Native acceptance coverage

The following is the broader review checklist, not a claim that every optional
browser feature has been tested. Paired screenshots, actual completed operations,
and remaining limitations are recorded by round in the critic manifests.

| Area | Required evidence |
| --- | --- |
| Versions | `rpm -q firefox firefox-langpacks`; `firefox --version`; Wayland/session backend in `about:support` |
| SC and TC | Top and paragraph screenshots; inspect regional glyphs, punctuation, 400/500 weight and mixed `English / 1.2 km / ¥28.50 / NT$120` |
| Scale | 100%, 125%, 150%, 200%; normal 100% browser zoom; no per-browser DPI override |
| Chrome | Several tabs, focused address bar, history suggestions, context menu, menu panel, active/inactive titlebar |
| Normal browsing | Public SC/TC and English pages, back/forward, new tab, search, zoom, password/autofill controls where testable without a personal account |
| Files boundary | Download `周末路线.txt`, open the completed download in the native text viewer, choose an image through the KDE portal |
| External links | Invoke `xdg-open` from a closed and an already open browser; both must land in the Aven profile without a profile-lock error |
| Media | Public or local WebM/audio playback; record any proprietary-codec limitation separately |
| Motion | Observe window opening, tab switching and menus; screenshot quality does not prove animation quality |

### Version limits and sources

This integration targets **native Linux GTK Firefox in the captured Kinoite 44
image**. It does not configure a Firefox Flatpak or Chromium. The exact installed
Firefox version is 155 in the pinned comparison deployment. Check these preferences
against that build before accepting the screenshots; Firefox's internal preference
names are not a long-term compatibility guarantee.

Upstream source inspected on 2026-09-15 defines `browser.tabs.inTitlebar=0` as
native titlebar mode and portal file-picker mode `1` as always use portal.
The same source defines native GTK theme support. [Firefox StaticPrefList](https://github.com/mozilla-firefox/firefox/blob/main/modules/libpref/init/StaticPrefList.yaml).
Per-script font preferences are in [Firefox all.js](https://github.com/mozilla-firefox/firefox/blob/main/modules/libpref/init/all.js).
New-tab preferences and normal density are in [Firefox profile defaults](https://github.com/mozilla-firefox/firefox/blob/main/browser/app/profile/firefox.js).
The explicit profile command is documented by [Mozilla command-line options](https://wiki.mozilla.org/Firefox/CommandLineOptions).

## Round3 chrome and launcher correction

Firefox155 retained a cool-colored toolbox despite System theme and correct Breeze GTK colors. A small opt-in `browser/chrome/userChrome.css` now supplies palette variables only for normal light windows. Layout, controls, websites, dark/high-contrast and private-window styling remain native. This Mozilla chrome customization requires review on browser upgrades. The managed user entry is now `org.mozilla.firefox.desktop`, matching its real Wayland application ID; `aven-browser.desktop` is hidden compatibility for saved associations. The original brand and isolated profile wrapper remain. Actual screenshot validation is recorded by round, not inferred from installation.
