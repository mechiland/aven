# Full-width translucent panel

This unreleased follow-up changes the Union panel to the user's Windows 11
layout reference. The existing Aven background, blur, 58 px height, icons and
running indicators remain. The panel fills the screen width and touches its
bottom edge. The Breeze profile retains its previous layout.

The native desktop pager sits at the left. Two expanding Plasma spacers center
the launcher and application group independently of the unequal edge groups.
The system tray, single-line date/time and show-desktop control sit at the right.
The seven existing widgets retain their identities; only two spacers are added.
One additional virtual desktop is created if there is only one. Existing
desktops, names and window assignments are retained on subsequent applications.

Both profile application and ISO first-login use `integration/panel_layout.py`.
To apply only this layout to an existing Aven Union session:

```sh
bash ~/aven/scripts/guest-session.sh python3 ~/aven/integration/panel_layout.py
```

The command records a full user-profile snapshot before applying the layout.
The tested pre-change snapshot is
`~/.local/state/aven/focused-before-20260918T014441.345228Z` in the lab guest.
Use the existing [restore guide](restore.md) to restore a selected snapshot.
Fedora Atomic deployment checksums are unchanged. This change does not rebuild
the published 0.3.1 ISO.

Native evidence is in [the review record](../evidence/verification/union-full-width-panel/review.json):

- [Previous dock](../evidence/aven/round-08/before-awake.png)
- [Full-width desktop](../evidence/aven/round-08/desktop-final.png)
- [Real Chinese filenames after shell restart](../evidence/aven/round-08/chinese-files-final.png)
- [Second space selected](../evidence/aven/round-08/space-two-final.png)
- [Calendar](../evidence/aven/round-08/calendar-open.png) and
  [volume tray popup](../evidence/aven/round-08/tray-volume-final.png)
- [1280 px layout check](../evidence/aven/round-08/narrow-1280.png)

At 1920×1200 and 1280×720, the panel fills the width, date/time stays on one
line, and the launcher/application group's geometric center is within one pixel
of the screen center. The smaller mode is only a panel layout check: existing
windows extend beyond that temporary viewport, and Plasma's fixed-point clock
font follows the virtual display's changed physical DPI. No fractional-scale
typography acceptance is claimed.

Native pager switching, Files launch, show desktop, calendar and volume popup
were exercised. Reapplication preserves all nine widget IDs/order and the two
desktops. Configuration persisted across a shell restart. The beta shell hung
while stopping and required killing that shell process to finish the restart;
graceful restart is therefore not marked passed. The recovered shell is active.
All 116 existing verification tests pass. Guest reboot, rollback execution,
motion, independent visual scores and the three-second judgment remain pending
for this follow-up.

The layout uses KDE's [public scripting API](https://develop.kde.org/docs/plasma/scripting/api/)
and the installed 6.7.90 implementations of the
[panel spacer](https://github.com/KDE/plasma-workspace/blob/v6.7.90/applets/panelspacer/main.qml)
and [clock settings](https://github.com/KDE/plasma-workspace/blob/v6.7.90/applets/digital-clock/main.xml).
