# Medium emphasis revision

The user's new direction changes `section_label.weight` and `emphasis.weight`
from 600 to 500. `window_title.weight` remains 500. Sizes, ordinary UI 400,
reading 400, regional CJK fallback, and rendering settings are unchanged.
Consumers of these shared roles now request Medium for Latin and Chinese;
independent document styles and native controls' own Bold requests are not
rewritten by this role change.

`audit.py` now checks the three configured emphasis roles against actual named
Medium instances in Latin, SC, TC, and HK. It no longer uses optional variable
CJK 600 interpolation as evidence for configured emphasis. The isolated audit
using the previously copied guest fonts and system configuration passes 68/68
checks; see [the report](round06-medium-role-resolution.json). Root must still
activate the role consumers and inspect the resulting native UI. The earlier
round-06 screenshots predate this section/emphasis revision.

An additional offscreen Qt 6.11.2 experiment tested whether a real CJK Medium
face could be selected for native Bold requests using a scan alias, without
altering Regular or Latin. The diagnostic used a private temporary font
directory containing copies of the existing guest fonts, temporary config
wrappers, and subprocess-only `FONTCONFIG_FILE`; no installed font or desktop
configuration was replaced. The clearly named `Union CJK Medium Probe SC`
alias exists only inside that experiment and is not a shipped font family.

Fontconfig correctly resolved the alias to Noto CJK SC's real Medium face,
weight 100, index 327682. That alone did not solve the native Qt problem:

- Inserting the alias after Adwaita only for emphasis requests preserved
  ordinary 400 and Latin, but Qt's 700 CJK output remained identical to the
  control Bold 700 in both glyph outlines and rendered pixels.
- Explicitly requesting the alias as the CJK family made a 400 request render
  Medium, violating the requirement to preserve regular text. A 700 request
  still did not reproduce the real Medium control's outlines or pixels.

The control confirms that explicit 500 renders an actual Noto CJK Medium
instance, separate from Regular 400 and Bold 700. This probe validates font
selection behavior for the tested SC sample; it is not a screenshot or a visual
quality score. It does not establish all regional/script behavior.

The alias approach is rejected and no experimental rule is installed. A
native control that calls `setBold(true)` still needs a supported widget-level
emphasis setting or a source change that chooses the intended face per script;
global weight or style remapping is not a demonstrated substitute. The unchanged
Latin and ordinary-weight controls prevent treating a broad style override as
a successful fix.

The experiment is deliberately outside the repository and deployment tree.
Its reproducer and full Qt glyph/raster result are retained locally under
`/home/michael/work/aven/.cache/typography-round06-medium-probe/` as
`native_medium_alias_probe.py` and `native-medium-alias-result.json`.

Integration dependency: root must apply the updated roles to shared Qt/GTK
configuration and app chrome generated from those roles. Thus controlled
emphasis changes from 600 to 500; native KIO's hardcoded 700 stays unaffected.
No native-bold override or new visual acceptance claim accompanies this change.
After syncing the updated typography files to the guest, the active audit is:

```sh
python3 /home/aven/aven/typography/audit.py --active --output /home/aven/aven/evidence/verification/round06-medium-font-audit.json
```
