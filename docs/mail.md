# Mail — Thunderbird integration

**Choice: Thunderbird.** Reading, replying, composing, searching and attachments
stay in the mature upstream application. This is a profile and a small CSS layer,
not a mail-client fork. The guest must use the same Thunderbird package/version
for stock and Aven. Native Thunderbird 153.0.2 is booted in both guests; round 4
mail coherence scored **8.1** after the compose fix and native offline draft
save/reopen verification. See [the final review](critic-round-04.md).

## Practical choice review

| Application | Relevant strengths | Aven decision |
| --- | --- | --- |
| Thunderbird | Documented Gmail OAuth setup; local folders and account/identity model; supported release channels | Selected. One self-contained mail profile gives reproducible reading/writing fixtures, and shares Gecko/font integration knowledge with Firefox. |
| KMail | Native KDE integration; IMAP, POP3, EWS; offline mail, encryption, multiple identities | Strong alternative. Its Qt chrome would need less integration. We are prioritizing the selected application's account workflow and isolated reproducibility for this first prototype. No claim that KMail is unmaintained or inferior was established. |
| Evolution | IMAP/POP and local mbox/Maildir; documented Exchange account types | Mature alternative, particularly for organizations needing its Exchange workflow. Its additional PIM integration is outside this narrow prototype. |

These are documented-capability comparisons, not fabricated usability scores.
References accessed 2026-09-15:
[Thunderbird Gmail/OAuth](https://support.mozilla.org/en-US/kb/thunderbird-and-gmail),
[Thunderbird account architecture](https://source-docs.thunderbird.net/en/latest/backend/accounts.html),
[Thunderbird release channels](https://updates.thunderbird.net/en-US/thunderbird/128.0/monthly/),
[KMail features and current releases](https://apps.kde.org/kmail2/),
[Evolution account types](https://help.gnome.org/evolution/mail-account-management.html).

## Integration boundary

- Noto Sans 11 pt chrome; Noto Sans CJK SC/TC/HK regional reading preferences.
- Latin reading 16 px / 1.65; tagged Chinese reading 17 px / 1.75 in plain,
  flowed and owned fixture content. Chinese punctuation and mixed text use real
  Noto metrics. No added character spacing or synthetic weight tricks.
- Warm content/chrome surfaces and jade accents follow `visual/tokens.json`.
- A separate native titlebar joins the integrator's KWin decoration.
- Thunderbird's own normal density and virtual row layout stay authoritative.
  Changing message-row height in CSS independently of its JS calculator can
  clip or overlap rows, so no such override is included.
- Small variable-based transition changes retain keyboard focus feedback;
  reduced-motion and contrast preferences remain usable. Native GTK, KWin,
  fontconfig and DPI settings are owned by root/typography.
- Default authored HTML mail formatting stays enabled. Sender-styled tables,
  receipts and newsletters keep their structure. The reading CSS is limited to
  Thunderbird plain/flowed content and our fixture's `.aven-letter` wrapper.
- No application updates, attachment checks, encryption or remote-content
  protections are disabled. The offline mode belongs only to the local fixture
  harness. Normal empty Aven profiles use upstream account setup.

`mail/chrome/userChrome.css` is an unsupported upstream customization surface.
It is deliberately small and token-oriented. Selectors/preferences were initially
checked against host Thunderbird 155.0.1 and then the guest's 153.0.2 `omni.ja`:
`shared/variables.css`, `shared/threadPane.css`, `UIFontSize.sys.mjs`,
`mailTabs.js`, `SessionStoreManager.sys.mjs`, `MsgComposeCommands.js` and defaults.
Paired native screenshots establish the observed guest appearance separately.
For each Thunderbird update, verify read/compose screenshots, contrast mode,
keyboard focus, message-row clipping and native titlebar before accepting it.

## Reproducible stock and Aven mail

If the official Kinoite image contains no mail app, root installs the same
Thunderbird package in the lab guest and records the addition. Capture all
otherwise-stock desktop scenarios first as required by the baseline procedure.
Keep any real user profile separate.

From the copied repository **inside each guest**:

```sh
# Stock guest, before Aven settings. This seeds local sample mail only.
python3 mail/profile.py create --variant stock --profile "$HOME/.local/share/aven/mail/stock" --demo
python3 mail/profile.py launch --profile "$HOME/.local/share/aven/mail/stock"

# Aven comparison guest, after shared typography and visual integration.
python3 mail/profile.py create --variant aven --profile "$HOME/.local/share/aven/mail/aven" --demo
python3 mail/profile.py launch --profile "$HOME/.local/share/aven/mail/aven"
```

`create` refuses **any existing directory**. It never locates, edits or registers
an existing Thunderbird profile. Preferences are seeded once in `prefs.js`, not
reapplied from `user.js` at every startup, so ordinary changes remain editable.
For another critic round, choose `aven-round-2` etc. Keep the prior profile with
its evidence. All fixture paths are relative to the chosen Thunderbird profile.
The script accepts `--executable` for an explicit native executable path.

Four original fictional messages cover Simplified Chinese, Traditional Chinese,
English and mixed Chinese/Latin. The date, message IDs, MIME boundaries and mbox
From-lines are fixed, so both guests get identical mailbox bytes. `Drafts`
contains an editable reply. `fixture-export` also contains individual `.eml`
files and the compose HTML/text. All addresses end in `example.invalid`; the
profile contains no IMAP, POP or SMTP service. The launch command starts offline.
No mail is sent by any script.

To open the writing fixture, close the reading instance first:

```sh
python3 mail/profile.py launch --profile "$HOME/.local/share/aven/mail/aven" --scene compose
```

This opens Thunderbird's real compose window, prefilled with the local draft
text. Do not invoke Send; use Ctrl+S to test local draft storage, then close/reopen
the draft. No real email account is needed. Replace the profile path with the
stock profile for the same stock writing scene. For a normal new profile without
fixtures or offline harness, omit `--demo` on `create`.

## Current native evidence

Round 4 captures contain the same fictional Inbox, Simplified and Traditional
Chinese messages, normal compose frame and a matched 720px-wide compose frame.
The native operation run saved a new Chinese sentence and reopened the draft
with that exact text intact. See the [comparison index](COMPARISON.md),
[native operation report](../evidence/interaction/aven-round04-native-verification.json)
and [compose rhythm review](compose-rhythm-review.md).

The fixture check confirms identical initial stock/Aven Inbox bytes, four parsed
multipart messages with SC/TC/English metadata, one draft and no SMTP service.
Profile creation refuses to overwrite an existing directory. Native Chinese
text entry used the clipboard and editor; an input method engine was not tested.
No live account delivery, attachment round trip or network mail sending was
performed. The four-scale matrix covers Dolphin and Firefox UI/prose; mail's
read/compose comparisons are at 1×, including genuinely wrapped Chinese lines.

For a later account-integration or platform round, repeat read/compose at the
other scales, test native keyboard traversal and search, and use an explicitly
authorized account for delivery and attachment checks. Preserve sender HTML and
native row geometry when maintaining the small stylesheet.

## Normal product launcher

Root activates the normal mail integration inside the Aven guest with:

```sh
python3 mail/install.py --home "$HOME"
```

Panel activation: **`applications:net.thunderbird.Thunderbird.desktop`**. The desktop entry keeps
Thunderbird's name and icon. Root can associate `x-scheme-handler/mailto` and
`message/rfc822` with `net.thunderbird.Thunderbird.desktop` as part of shared desktop integration.
The installer itself only owns the profile, launcher and desktop entry.

The command seeds `~/.local/share/aven/mail/default` once, **without fixtures,
accounts or offline preferences**. Thunderbird presents its ordinary account
setup; real user accounts remain fully supported. The generated
`~/.local/bin/aven-mail` launches that profile online and forwards external
`mailto:` and file arguments unchanged. Remote requests stay enabled for an
already-running instance. This is separate from the stock/Aven demo profiles
and their explicitly offline evidence launcher.

Re-running the installer preserves all existing profile files, preferences,
accounts, saved mail and edited CSS. It only rewrites its marked generated
launcher/desktop entry. An existing unmarked profile, a demo profile in the
normal-profile location, symlink target, or unmarked launcher/desktop file causes
an explicit refusal. Normal-profile installation can safely run while its
Thunderbird instance is open because no existing profile file is written.

## Round3 refinement

The chrome palette includes native toolbox colors, and the compose editor
viewport has a 16 px top / 24 px side inset. The native desktop identity binds
the actual Wayland window to its pinned launcher; the old Aven entry is hidden
compatibility.

## Round 4 compose rhythm

Thunderbird's `messageQuotes.css` forces `body` line height to `initial` at
user-agent-important priority. A body rule in `userContent.css` therefore loaded
successfully but had no visible effect. The final rule targets normal editable
block containers in `about:blank?compose`: paragraphs, divs, main content and
lists. Native computed leading is **29.75 px at 17 px**, confirmed against a real
compose screenshot. Explicit author formatting remains available; incoming HTML
is outside this scope. These user styles do not become outgoing HTML attributes
or message CSS. Plain-text bodies without block containers retain native leading.

The diagnostic used a temporary loopback-only Marionette session to read styles.
It was closed before the round 4 boot; remote debugging is not a product default.
