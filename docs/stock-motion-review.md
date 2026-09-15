# Stock motion: independent supplemental review

All six recordings are reviewed. I inspected **40 distinct original 1920×1200 PNG states** in time order, verified all **307 native frame hashes**, and mapped repeated frames back to inspected identical states. The exact files, hashes, offsets, repeated-state runs, and final-state mappings are in [the review manifest](../evidence/critic/stock-motion-review.json).

This is a stock baseline, with no Aven comparison or new scores. Round 02/03 reports remain unchanged.

## What the native frames show

| Scenario | Inspected distinct states | Observed capture rate | Maximum sample gap |
|---|---:|---:|---:|
| window_open_close | 8 | 8.22fps | 143ms |
| window_switch | 7 | 8.20fps | 147ms |
| menus_popovers | 7 | 8.17fps | 144ms |
| preview | 5 | 8.21fps | 141ms |
| photo_transition | 6 | 7.10fps | 158ms |
| overview | 7 | 6.98fps | 161ms |

### Window Open Close

[Native recording metadata](../evidence/interaction/stock-motion-window-open-close/recording.json). The second Dolphin window appears centered with a modest scale and opacity change. Frame 0010 still has generic image icons; thumbnails arrive by 0011, with remaining footer/storage painting settling through 0013. Closing frames 0023–0024 contract and fade the second window. Frame 0025 is byte-identical to the initial original-window view.

**Character:** Subtle scale/fade; a visible short-lived thumbnail-loading state. **Comparison condition:** Compare the same new-window action and settled content. Do not attribute thumbnail loading time to the compositor animation.

### Window Switch

[Native recording metadata](../evidence/interaction/stock-motion-window-switch/recording.json). The captured sequence changes from Dolphin to Firefox containing real SC/TC prose, then back to Dolphin. Firefox content is already fully drawn in the first switched frame. Subsequent distinct frames chiefly show active chrome/task-state settling. No held Alt+Tab popup or large travel is visible.

**Character:** Direct switch with small focus-color settling in the sampled states. **Comparison condition:** This checks quick Alt+Tab only; it does not establish held-switcher design or animation quality.

### Menus Popovers

[Native recording metadata](../evidence/interaction/stock-motion-menus-popovers/recording.json). The hamburger button highlights, then the menu is partially transparent at 0008 and opaque by 0009. On dismissal, frames 0024–0026 fade the same stationary menu. By 0027 the frame is byte-identical to highlighted-button/no-menu frame 0007. Chinese entries remain clear in the opaque state.

**Character:** Stationary fade with no sampled bounce or large displacement. **Comparison condition:** Compare the same native menu and dismissal; only coarse fade behavior can be inferred.

### Preview

[Native recording metadata](../evidence/interaction/stock-motion-preview/recording.json). F11 exposes the right information panel and reduces the file-list width. Earthrise is a small approximately 160 px-wide image above a dense metadata block. Down changes selection and the panel image to the landscape by 0026; the bottom status label still names Earthrise until 0028. F11 hides the panel by 0032, retaining the landscape selection and restoring list width. No intermediate panel animation was captured.

**Character:** Direct layout change and small image replacement; the list reflows horizontally. **Comparison condition:** Stock information-panel preview and Aven overlay are different native interactions. Compare friction, content usefulness, focus continuity, and transition character; do not claim a matched shortcut or identical surface.

### Photo Transition

[Native recording metadata](../evidence/interaction/stock-motion-photo-transition/recording.json). The landscape is fit at 65%; portrait settles at 43% with white side margins. Frame 0007 blends both images, and 0008 shows the upright portrait. Return frames 0022–0023 again blend portrait and landscape; 0024 is byte-identical to the initial landscape frame. There is no sampled pan or zoom animation, only crossfade and changed fitted image bounds. Window title temporarily reads only Gwenview at 0006 before the new filename.

**Character:** Simple crossfade. Differing aspect ratios produce a visibly light transitional outer area against the white viewer canvas. **Comparison condition:** Use the same landscape and portrait fixture pair. The sampled blend is expected transition content, not a duplicated-image rendering defect.

### Overview

[Native recording metadata](../evidence/interaction/stock-motion-overview/recording.json). The desktop and three windows shrink and rearrange into native Overview. Frame 0007 is still in transit, with Firefox and Dolphin touching/overlapping; frames0008–0009 settle into separated two-above/one-below positions. Search and desktop controls occupy the top. On exit 0023–0024 scale and rearrange back; 0025 is byte-identical to the initial desktop. No cube, wobble, or decorative flourish is visible in the captured states.

**Character:** The largest spatial transition in this set; simple overview scaling and placement. **Comparison condition:** Compare the same three-app arrangement. Transitional small text is resampled by the effect and should not be mistaken for the normal typography baseline.

## Interpretation and limits

Stock KDE already uses fairly restrained menu fades, window scale/fades, and Gwenview crossfades in these recordings. Aven should not receive credit merely for having a fade. The most consequential visible stock weakness here is preview usefulness: opening the information panel reduces the working list width while showing a very small image amid dense metadata.

The capture transport requested 10 fps and achieved 6.98–8.22fps, with 141–161ms maximum gaps. I reviewed ordered original frames, not continuous real-time playback. Host capture-completion timestamps are neither display-presentation nor input-delivery timestamps. These sequences can support coarse transition character, captured intermediate states, and end-state comparisons; they cannot certify 60 Hz smoothness, physical pacing, exact animation duration, or input latency. Absence of an intermediate frame does not prove that an animation was disabled.

**Motion quality scores remain null. Aven comparison is pending. This supplement does not pass the prototype or alter any historical score.**
