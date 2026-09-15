# Aven round 04 native verification handoff

Status: **native operations completed; Aven UI returned to root at 14:46 UTC+08:00**.
Root now owns Aven native input. Verification captures used
`op-` prefixes so canonical appearance scenes remain available to the integrator.

## Preconditions

- Root names the completed build/round and releases the Aven guest explicitly.
- Observe current KScreen scale, native app inventory, and framebuffer. Use the
  same 1920×1200 at 1× lab output as the stock interaction run.
- Sync verification source if necessary. At 1× the runtime probe must report
  integer QScreen/KScreen agreement with no mapped measurement window.
- Record actual app locale and geometry. Keep stock/Aven content and selection
  matched; styling and defaults remain root's responsibility.

## Files workflow

Prepare a fresh `Documents/Aven operation check 20260915-round04` fixture using
`file_operations.py prepare` and the existing `旅行清单.txt` source. Stop rather
than adopting an existing directory. Perform operations through Dolphin's native
UI, recording input and inspecting new round-04 captures:

1. Open the fixture, enter `01 原件`, select the long Chinese/Latin filename.
2. Copy with Ctrl+C; navigate through parent and destination folders; Ctrl+V in
   `02 复制`. Save the `copied` byte check.
3. Cut and paste into `03 移动`; save the `moved` check.
4. F2 rename to `已整理 · Weekend.txt`; save the `renamed` check.
5. Delete to Trash; inspect the native Trash item and original path; save the
   `trashed` check. Do not empty Trash.
6. Restore from the native context menu; save the `restored` check and inspect
   the returned file. Keep original and restored fixture files as evidence.
7. Exercise breadcrumbs, Documents/Downloads/Pictures sidebar entries, grid and
   list views, multi-selection, and default JPEG opening in Gwenview.

## Preview behavior

Use the installed **Ctrl+Alt+P** action from Dolphin; direct renderer launch does
not verify integration. Space remains Dolphin selection mode by design.

- Select image/PDF/text/media fixtures, invoke the native preview action, inspect
  the actual content and localized controls.
- Escape must close preview and leave Dolphin usable with the intended file
  selection. Verify active UUID and visible selection, not UUID alone.
- For a multi-selection, Alt+Right/Left must traverse only the selection.
- Repeated invocation must close/reopen predictably without accumulating orphan
  preview windows. Return must open the file in its mature default application.
- Round-04 video preview should show its poster while paused; Space should start
  playback and Escape should stop/close. Record what actually happens.

Stock evidence retains its limitations: F11 information panel stays open after
Escape and the selection is cleared; Space opens selection mode. Those stock
failures are not overwritten by Aven results.

## Browser, mail, photos

- Use the same local HTTP browser fixture. Download the route through Firefox,
  inspect its native completed-download popup, use Show in Folder, and compare
  downloaded bytes to the fixture. Never overwrite an existing user download.
- Open the native KDE chooser and select `06-山间河流.jpg`; the page's plain file
  input only displays the local name and performs no upload.
- Save and reopen an offline Thunderbird draft through the UI. Do not send mail.
  Capture the canonical 1000×840 composer and an additional 720-pixel outer-width
  composer to inspect wrapped Chinese prose and signature spacing.
- In Gwenview, use Right then Left on the same landscape/portrait pair; inspect
  title/index and image content. Test fullscreen and Escape return.

## Six motion recordings

Use `record_frames.py` at requested 10 fps for 6–8 seconds per sequence, with
normal public input recorded in `evidence/interaction/aven.jsonl`:

| Sequence | Native action |
| --- | --- |
| Window opening/closing | Dolphin Ctrl+N, then Alt+F4 on the new window |
| Switching | Alt+Tab to Firefox, then back to Dolphin |
| Menus/popovers | Open Dolphin menu, then Escape |
| File preview | Ctrl+Alt+P, selected-file navigation where applicable, Escape |
| Photo transition | Gwenview Right, then Left |
| Overview | The configured native Overview shortcut, then Escape |

Save untouched frames, transport metadata, hashes, actual sampling rate and gaps.
Inspect representative original frames and scene endpoints. The sampled VM
recordings do not establish physical frame pacing; visual motion assessment
belongs to the paired critic review.

## Deliverables

Create an Aven-specific interaction report with native operator attribution,
inspected screenshot/sidecar hashes, byte checks, motion manifests and observed
failures. Preserve `stock-native-verification.json` as the source baseline. Root
owns `docs/STATUS.json`, acceptance, fixes, and further rounds.

Completed source report: `evidence/interaction/aven-round04-native-verification.json`.
All 17 required native operations passed. The associated integrity report at
`evidence/verification/aven-round04-native-evidence-validation.json` verifies 35
accepted screenshots and all 359 frames across six motion recordings. Nine
startup or operator-miss captures are explicitly excluded. This does not assign
visual quality scores or establish physical frame pacing.

## Required operation IDs

`folders`, `breadcrumbs`, `sidebar`, `grid_list`, `selection`, `copy`, `move`,
`rename`, `trash`, `restore`, `default_open`, `preview_toggle`,
`preview_escape_focus`, `browser_download`, `browser_file_picker`,
`mail_draft_save`, `photo_next_previous`. Byte checks alone do not satisfy native
operation observations. Record failed observations without converting them to passes.
