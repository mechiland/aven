# Union 0.3.1 · Medium emphasis and translucent dock

This follow-up applies the user's requested 500 emphasis and macOS-like dock to
the existing Union VM. It extends the [0.3.0 appearance revision](UNION-SEQUOIA.md).
Fedora Atomic deployments and the pinned stock fallback remain unchanged.

## Typography

Shared section/emphasis roles now request 500, as do the managed Thunderbird
sender, folder and subject styles that previously requested 600. Window titles
were already 500. Regular UI and reading text stay 400 at their existing sizes.
The active guest passes all 68 font-resolution checks, including actual named
Medium faces for Latin, Simplified Chinese, Traditional Chinese and Hong Kong.

This is not a global rewrite of all bold text. Native KIO current-location
breadcrumbs still explicitly request Bold, and arbitrary web/document headings
retain their own styles. The [typography investigation](../typography/round06-medium-emphasis.md)
explains why a broad font alias was rejected rather than weakening regular text.

## Dock

The user-local `aven-dock` Plasma style overrides only panel and task frames.
The existing native task manager still supplies running state, activation,
minimization, grouping and context menus. Other shell assets inherit Breeze.

- Centered, floating, 58 logical px tall, with width fitted to contents.
- A 54% translucent pale background, 16 px corners and a fine light edge.
- Small dark running dots in normal, active and minimized states; closed pinned
  applications have no dot. The previous blue active tile is removed.
- Compact icon spacing and a 10 pt regular clock. Existing launcher, system
  tray, clock and desktop controls are preserved.

The reference inspected again for this change is
`/home/michael/Downloads/macOS15Screens/15-Sequoia-Desktop.png`. The dock follows
its translucent rounded container and quiet black indicator treatment. Application
icons and the retained Plasma system tray differ from macOS.

Desktop matching now uses the actual Firefox/Thunderbird application IDs, and
hidden legacy launchers no longer compete for their window classes. A user-local
Gwenview importer metadata override removes only its incorrect `StartupWMClass`
hint; its native command and hidden status are retained. This prevents Photos
windows being assigned to the importer and creating a duplicate dock icon.
The matching order was checked against the
[installed Plasma version's implementation](https://github.com/KDE/plasma-workspace/blob/v6.7.90/libtaskmanager/tasktools.cpp#L217).

## Native evidence and verification

All images are original 1920×1200 native framebuffer captures at 1×, with SHA-256
and RFB metadata in their JSON sidecars.

| State | Evidence |
| --- | --- |
| Before this follow-up | [Before](../evidence/aven/round-07/before.png) |
| Chinese mail with 500 emphasis, four running dots | [Final](../evidence/aven/round-07/mail-final.png) |
| Photos minimized, running dot retained | [Minimized](../evidence/aven/round-07/photos-minimized-dot.png) |
| Photos restored from the dock | [Restored](../evidence/aven/round-07/photos-restored-dot.png) |
| Photos closed, pinned icon without a dot | [Closed](../evidence/aven/round-07/photos-quit-no-dot.png) |
| Native task context menu | [Menu](../evidence/aven/round-07/native-task-menu.png) |

The final panel measures 558×58 logical px with the original seven widgets.
Native app launch, minimize/restore, close, menu and show-desktop behavior were
exercised; all four apps group into their own fixed icon. Shell restart preserved
the theme and panel settings. The 88 existing verification tests pass; 68 active
font checks pass. See the [review record](../evidence/verification/union-dock-medium/review.json).
This follow-up did not repeat guest reboot, fractional-scale, motion or rollback
execution checks; the preceding 0.3.0 reboot evidence is recorded separately.

## Apply and recover

The running test session is VNC `127.0.0.1:5922`. The source bundle is
[Aven-Union-0.3.1-profile.tar.gz](../output/Aven-Union-0.3.1-profile.tar.gz).
Unpack into `~/aven` on the already prepared Union Atomic guest, close the focused
applications, and run:

```sh
bash ~/aven/scripts/guest-session.sh python3 ~/aven/integration/apply-profile.py \
  --style union --decoration aven --refresh
```

Log out/in before comparing. The exported 0.2.0 VM disk remains unchanged.
The later [Union 0.3.1 installer release](UNION-ISO-0.3.1.md) packages this profile
for fresh installations and records its own boot and installation evidence.

The lab's pre-change focused snapshot is
`~/.local/state/aven/focused-before-20260917T061127.091575Z`.
The mail chrome backups are in `~/.local/state/aven/dock-medium-before/`.
Shared rollback includes the new Plasma style's files. Restore only appearance
files, keeping later browser/mail data. Live rollback was not exercised.
The importer metadata addition has its own pre-install snapshot at
`~/.local/state/aven/focused-before-20260917T062245.327653Z`; its original state was
absent. The current snapshot manifest covers 93 paths, including this override.

Formal visual scores, the three-second differentiation judgment and overall
acceptance remain pending; earlier prototype scores do not assess this revision.
