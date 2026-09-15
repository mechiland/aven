# Native bold emphasis investigation

## Result

The dark Dolphin breadcrumb is **real Bold 700, not another legacy 900 serialization error**. In offscreen Qt 6.11.2 on both guests, in both SC and TC locales, copying the application font and calling `setBold(true)` requests 700 and shapes Latin plus regional CJK as Bold 700. Explicit 700 behaves the same. The explicit 900 control shapes as Black 900. Additional outline hashes distinguish 700 from 900 for Latin, SC, and TC.

The inspected [round 03 Files screenshot](../evidence/aven/round-03/files-list-1x.png) still shows strong current-folder emphasis. This report identifies the weight mechanism; it does not assign a visual score.

## Evidence

- [Aven SC](../evidence/verification/aven-bold-shaping-zh_CN.json), [Aven TC](../evidence/verification/aven-bold-shaping-zh_TW.json)
- [Stock SC](../evidence/verification/stock-bold-shaping-zh_CN.json), [Stock TC](../evidence/verification/stock-bold-shaping-zh_TW.json)
- [Isolated pattern-remap and outline test, SC](../evidence/verification/aven-emphasis-pattern-zh_CN.json), [TC](../evidence/verification/aven-emphasis-pattern-zh_TW.json)

All probes used `QT_QPA_PLATFORM=offscreen`, created no window, and changed no guest preferences. The remap test used temporary `FONTCONFIG_FILE` wrappers including the active system configuration; they were deleted after each subprocess exited.

The independent fontconfig query matches CJK Bold to `NotoSansCJK-VF.ttc` indices 393218 (SC) and 393219 (TC), versus Black indices 458754 and 458755. The query uses the shaped physical family/style/weight; it is not a direct file pointer from Qt's font engine. Aven's matched fontconfig pattern reports `embolden=false`.

OS/2 `usWeightClass` is **not an instance-weight proof** here. The raw variable CJK table retains its default value 100 at Regular, Bold, and Black; the Latin variable Bold table retains 400. The diagnostic preserves these values instead of describing them as the applied weight. Qt documents QRawFont as a physical instance, but raw font tables can still describe a variable font's defaults. [Qt QRawFont](https://doc.qt.io/qt-6/qrawfont.html).

## Why the breadcrumb is bold

The installed KIO package is 6.30.0. Its URL navigator paint code copies the widget font and calls `setBold(m_subDir.isEmpty())` before drawing the current segment. This explicitly selects Bold for the current folder. The same code path exists in stock. [KIO 6.30.0 source](https://raw.githubusercontent.com/KDE/kio/v6.30.0/src/filewidgets/kurlnavigatorbutton.cpp).

Qt's `setBold(true)` selects its Bold enum; finer emphasis requires `setWeight()`. Changing the ordinary widget font to Medium alone would not defeat the navigator's subsequent `setBold(true)` call. [Qt QFont](https://doc.qt.io/qt-6/qfont.html#setBold).

## Scoped fontconfig candidate: ineffective

A test pattern matched the actual probe executable name `python3.14` and exact Bold weight, then assigned fontconfig `demibold`. Fontconfig debug output confirms that `prgname` is present. Changing Qt's application name or invoking Python with `exec -a dolphin` did not change this field in this environment. It follows the executable basename; direct Dolphin/Gwenview patterns were not instrumented, so their names remain an inference from their normal ELF paths.

The rule changes `fc-match` from Bold/200 to SemiBold/180. **It does not change the actual Qt glyphs**: requested 700 still reports Bold 700 and has identical outline hashes with and without the candidate, in both SC and TC. Qt's font database selects the face separately from some later fontconfig substitution calls. A passing `fc-match` check would therefore be a false implementation success for this candidate. [Qt 6.11.2 fontconfig database source](https://raw.githubusercontent.com/qt/qtbase/v6.11.2/src/gui/text/unix/qfontconfigdatabase.cpp).

An additional caution: requested SC 600 reports raw weight 600 but its tested outlines equal the 500 outlines. TC 600 differs from TC 500 in the same test. An implementation must validate physical outlines or controlled rendering before promising a real regional 600 instance.

## Smallest maintainable choice

Do not install the ineffective remap or relabel existing outlines. No supported breadcrumb-weight preference was found: Dolphin's documented custom font setting concerns the file view, while KIO's current-segment drawing explicitly sets bold. Keeping the native 700 emphasis is the smallest maintainable choice in the current prototype. A narrowly configurable upstream navigator emphasis role would address it directly, but requires a source change and is outside this configuration-only investigation. [Dolphin configuration documentation](https://docs.kde.org/stable_kf6/en/dolphin/dolphin/configuring-dolphin.html).
