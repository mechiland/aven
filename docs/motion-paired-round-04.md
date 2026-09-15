# Round 04 paired motion review

Aven’s preview is the clearest improvement: the image becomes useful at a glance and the file list stays in place. Fixed-size window fades also appear calmer than stock’s small scale change. No blocking transition defect appears in the captured states.

This is an independent review of original, unmodified native PNG sequences. All 46 distinct Aven states were opened at 1920×1200 and compared with the 40 stock states already inspected in [the stock review](stock-motion-review.md). All 359 Aven frame hashes were checked. Repeated identical frames, timestamps and return-state mappings are preserved in [the paired manifest](../evidence/critic/motion-paired-round-04.json).

## Paired findings

### Window Open Close

Aven opens and closes the second Dolphin with a fade at fixed bounds. Stock has a modest visible size change as well as fading. Aven looks calmer in the captured states. Both show some asynchronous application content settling.

Frames 0011–0015 show initial translucent window, file drawing, breadcrumb layout and footer settling. Frames 0030–0032 fade out without a visible size change; frame 0033 returns to the initial state.

Comparison limit: Stock opens a five-image Photos folder at 1200×630; Aven opens text Downloads at 1440×900. Startup performance and exact transition speed are not comparable.

Evidence: [stock recording](../evidence/interaction/stock-motion-window-open-close/recording.json) and [Aven recording](../evidence/interaction/aven-round04-motion-window-open-close/recording.json).

### Window Switch

Both switch directly from Dolphin to Firefox and back, without a held switcher popup. Aven matching warm application chrome reduces palette discontinuity; no distinct motion improvement is demonstrated.

Frames 0008–0010 show the Chinese HTTP fixture; frames 0029–0030 restore Dolphin focus decoration, with the original pixels returned by frame 0031.

Comparison limit: Firefox content and window geometry differ. Quick Alt+Tab was tested, not a held switcher or cycling many applications.

Evidence: [stock recording](../evidence/interaction/stock-motion-window-switch/recording.json) and [Aven recording](../evidence/interaction/aven-round04-motion-window-switch/recording.json).

### Menus Popovers

Both use a stationary menu fade. Aven has visibly larger Chinese labels and warm neutral surfaces; the motion itself remains similar, restrained native behavior.

Frames 0009–0010 fade in; 0033–0035 fade out. Frame 0036 returns to the pre-open highlighted hamburger state.

Comparison limit: Menu placement and selected context differ. Aven menu reaches the display right edge but observed labels and submenu chevrons remain visible.

Evidence: [stock recording](../evidence/interaction/stock-motion-menus-popovers/recording.json) and [Aven recording](../evidence/interaction/aven-round04-motion-menus-popovers/recording.json).

### Preview

Aven is a substantial preview improvement: an approximately 832-pixel-wide image occupies a focused overlay, while the underlying file list stays stable. Stock opens a narrow information panel, reflows the list and displays an approximately 160-pixel-wide image amid metadata. Aven retains overlay bounds when changing images and returns with both files selected.

Frames 0011–0012 fade in at fixed geometry. Frame 0024 shows landscape 2/2; frame 0039 returns to Earthrise 1/2. Frames 0052–0054 fade away and frame 0055 shows both original files selected. No intermediate image slide was captured. A standalone preview task icon briefly joins the panel.

Comparison limit: These are different native interactions: stock F11 information panel with one selected file at a time, Aven Ctrl+Alt+P with a two-file selection. The matching Earthrise/landscape assets support a usability comparison, not a timing benchmark.

Evidence: [stock recording](../evidence/interaction/stock-motion-preview/recording.json) and [Aven recording](../evidence/interaction/aven-round04-motion-preview/recording.json).

### Photo Transition

Both show Gwenview crossfades between upright landscape and portrait images, with a brief blend on a light canvas and no added pan or zoom. Aven filmstrip gives navigation context but reduces the fitted photo area. This is a useful integration tradeoff, not evidence of a newly improved transition.

Filmstrip selection moves in frame 0007; 0008–0009 blend to the portrait; 0010 settles. Frames 0027–0028 blend back and frame 0029 is identical to the initial landscape state.

Comparison limit: Same fixture images and outer window size, but different position and Aven filmstrip. Landscape fits at 56% in Aven versus 65% stock; portrait 37% versus 43%. Sparse states do not resolve exact transition duration.

Evidence: [stock recording](../evidence/interaction/stock-motion-photo-transition/recording.json) and [Aven recording](../evidence/interaction/aven-round04-motion-photo-transition/recording.json).

### Overview

Aven enters the native overview with two side-by-side windows and reverses to Dolphin. Sampled entry/exit states are restrained. Stock has three windows arranged across two rows, so Aven simplicity cannot be credited as a layout or motion improvement.

Frames 0010–0011 show two window cards settling; frame 0030 shows exit enlargement and overlap; 0031 approaches original geometry; frame 0032 exactly restores initial pixels.

Comparison limit: Different numbers of applications and window contents; not a matched layout comparison. There is only one sampled intermediate entry state.

Evidence: [stock recording](../evidence/interaction/stock-motion-overview/recording.json) and [Aven recording](../evidence/interaction/aven-round04-motion-overview/recording.json).

## What this establishes

All six scoped transitions have genuine paired capture and independent frame inspection. The current verification report records 17 successful native operations, including preview traversal and Escape focus return. Those operation results belong to the verification agent; this review does not imply the critic repeated those inputs.

Capture achieved 6.98–8.22 fps stock and 8.44–9.75 fps Aven, with maximum gaps of approximately 141–161 ms and 128–134 ms respectively. RFB readback and PNG encoding omit compositor frames. Ordered still inspection establishes transition character and end states; it does not establish continuous real-time perceived smoothness, physical display frame pacing, exact animation duration or input latency. Those criteria remain null.

Historical scores are unchanged. No final pass is issued here: current round 04 primary comparison and the 16-pair typography matrix must be completed separately.
