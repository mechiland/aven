#!/usr/bin/env python3
"""Create an isolated Thunderbird profile; existing profiles are never changed."""
from __future__ import annotations
import argparse
import fcntl
from email import policy
from email.message import EmailMessage
from email.utils import formataddr
import hashlib
import html
import json
import mailbox
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'fixtures/mail/messages.json'
MARKER = 'aven-mail-profile.json'


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def prefs_text(prefs):
    return '// Aven isolated prototype profile; all ordinary prefs remain editable.\n' + ''.join(
        f'user_pref({json.dumps(k)}, {json.dumps(v, ensure_ascii=False)});\n' for k, v in sorted(prefs.items()))


def candidate_preferences():
    roles = json.loads((ROOT / 'typography/roles.json').read_text(encoding='utf-8'))
    reading = roles['reading']
    ui_size = roles['ui'].get('pixel_size', roles['ui']['point_size'] * 96 / 72)
    prefs = {
        'toolkit.legacyUserProfileCustomizations.stylesheets': True,
        'mail.tabs.drawInTitlebar': True,
        'mail.uidensity': 1,
        # Keep native virtual-row measurements aligned with the actual UI size.
        # The user's later font-size/density changes still work normally.
        'mail.uifontsize': round(ui_size),
        'mail.pane_config.dynamic': 2,
        'mail.threadpane.listview': 0,
        'toolbar.unifiedtoolbar.buttonstyle': 2,
        'mail.biff.play_sound': False,
        'mail.biff.use_system_alert': True,
        'mailnews.start_page.enabled': False,
        'mailnews.display.prefer_plaintext': False,
        'mail.fixed_width_messages': False,
        'msgcompose.font_face': reading['family'],
        'msgcompose.font_size': 'medium',
    }
    for group, family in [('x-western', reading['family']), ('x-unicode', reading['family']),
                          *((language, roles['cjk'][language]) for language in ('zh-CN', 'zh-TW', 'zh-HK'))]:
        prefs.update({
            f'font.default.{group}': 'sans-serif',
            f'font.name.sans-serif.{group}': family,
            f'font.name.monospace.{group}': 'Noto Sans Mono',
            f'font.name-list.sans-serif.{group}': f'Noto Sans, {family}, sans-serif',
            f'font.name-list.monospace.{group}': f'Noto Sans Mono, {family}, monospace',
            f'font.size.variable.{group}': reading['cjk_pixel_size'] if group.startswith('zh') else reading['pixel_size'],
            f'font.size.monospace.{group}': 14,
        })
    return prefs


def install_chrome(profile):
    roles = json.loads((ROOT / 'typography/roles.json').read_text(encoding='utf-8'))
    family = json.dumps(roles['ui']['family'], ensure_ascii=False)
    size = roles['ui'].get('pixel_size', roles['ui']['point_size'] * 96 / 72)
    shutil.copytree(ROOT / 'mail/chrome', profile / 'chrome', dirs_exist_ok=True)
    (profile / 'chrome/union-typography.css').write_text(
        '/* Generated from typography/roles.json by mail/profile.py. */\n'
        f':root {{ --union-ui-family: {family}; --union-ui-size: {size:g}px; }}\n', encoding='utf-8')


def install_layout(profile):
    """Use Thunderbird's persisted customization, retaining every other view."""
    path = profile / 'xulstore.json'
    if path.is_symlink():
        raise SystemExit('Refusing to replace a symlinked toolbar state.')
    state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    main = state.setdefault('chrome://messenger/content/messenger.xhtml', {})
    toolbar = main.setdefault('unifiedToolbar', {})
    spaces = json.loads(toolbar.get('state', '{}'))
    spaces['mail'] = [
        'get-messages', 'write-message', 'spacer', 'archive', 'delete',
        'junk', 'reply', 'reply-all', 'forward-inline', 'spacer', 'search-bar',
    ]
    toolbar['state'] = json.dumps(spaces, separators=(',', ':'))
    # Native collapse keeps the Spaces popover/reveal control available.
    main.setdefault('spacesToolbar', {})['hidden'] = 'true'
    header = main.setdefault('messageHeader', {})
    header_layout = json.loads(header.get('layout', '{}'))
    if not header_layout:
        header_layout = {
            'showAvatar': True, 'showBigAvatar': False, 'showFullAddress': True,
            'hideLabels': True, 'subjectLarge': True,
        }
    # Use Thunderbird's own header customization so labels/tooltips and the
    # user's ability to restore text remain intact; commands are never hidden.
    header_layout['buttonStyle'] = 'only-icons'
    header['layout'] = json.dumps(header_layout, separators=(',', ':'))
    save_json(path, state)


def refresh(profile):
    """Refresh only appearance in a closed, explicitly marked Aven profile."""
    marker_path = profile / MARKER
    if profile.is_symlink() or marker_path.is_symlink() or not marker_path.is_file():
        raise SystemExit('Refresh requires an existing, non-symlink Aven profile.')
    marker = json.loads(marker_path.read_text(encoding='utf-8'))
    if marker.get('schema_version') != 1 or marker.get('variant') != 'aven':
        raise SystemExit('Refresh only accepts an Aven variant profile.')
    prefs_path = profile / 'prefs.js'
    if prefs_path.is_symlink() or (profile / 'chrome').is_symlink() or (profile / 'xulstore.json').is_symlink():
        raise SystemExit('Refusing to refresh symlinked profile files.')
    with (profile / '.parentlock').open('a+') as lock:
        try:
            fcntl.lockf(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Close this Thunderbird profile before refreshing its theme.')
        # Accounts, identities, servers, passwords, messages and all unrelated
        # preferences remain untouched. Do not reseed content or fixture state.
        allowed = {
            'toolkit.legacyUserProfileCustomizations.stylesheets',
            'mail.tabs.drawInTitlebar', 'mail.uidensity', 'mail.uifontsize',
            'mail.pane_config.dynamic', 'mail.threadpane.listview',
            'toolbar.unifiedtoolbar.buttonstyle',
        }
        prefs = {key: value for key, value in candidate_preferences().items() if key in allowed}
        original = prefs_path.read_text(encoding='utf-8') if prefs_path.exists() else ''
        keys = '|'.join(re.escape(json.dumps(key)) for key in prefs)
        managed_line = re.compile(r'^user_pref\((?:' + keys + r'),')
        retained = [line for line in original.splitlines() if not managed_line.match(line)]
        generated = [f'user_pref({json.dumps(key)}, {json.dumps(value)});' for key, value in prefs.items()]
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=profile, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write('\n'.join(retained + generated) + '\n')
        temporary.chmod(0o600)
        temporary.replace(prefs_path)
        install_chrome(profile)
        install_layout(profile)
        marker['visual_validation'] = 'pending-native-guest-screenshots'
        marker['theme_revision'] = 'union-sequoia-frame-v1'
        save_json(marker_path, marker)
    print(json.dumps({'refreshed': str(profile), 'account_data_modified': False, 'theme_revision': marker['theme_revision']}))


def letter_html(item):
    paras = ''.join('<p>' + html.escape(p).replace('\n', '<br>') + '</p>' for p in item['paragraphs'])
    return f'<!doctype html><html lang="{item["lang"]}"><head><meta charset="utf-8"></head><body><main class="aven-letter" lang="{item["lang"]}">{paras}</main></body></html>'


def make_message(item, draft=False):
    msg = EmailMessage(policy=policy.SMTP)
    msg['Message-ID'] = f'<aven-{item["id"]}@example.invalid>'
    msg['Date'] = item.get('date', 'Tue, 15 Sep 2026 09:25:00 +0800')
    msg['Subject'] = item['subject']
    msg['From'] = formataddr(('安宁', 'anning@example.invalid')) if draft else formataddr((item['from_name'], item['from_address']))
    msg['To'] = formataddr((item['to_name'], item['to_address'])) if draft else formataddr(('安宁', 'anning@example.invalid'))
    msg['X-Mozilla-Status'] = '0001'
    msg['X-Mozilla-Status2'] = '00000000'
    if draft:
        msg['X-Mozilla-Draft-Info'] = 'internal/draft; vcard=0; receipt=0; DSN=0; uuencode=0; attachmentreminder=0; deliveryformat=4'
        msg['X-Identity-Key'] = 'id1'
        msg['X-Account-Key'] = 'account1'
    msg.set_content('\n\n'.join(item['paragraphs']), charset='utf-8')
    msg.add_alternative(letter_html(item), subtype='html', charset='utf-8')
    msg.set_boundary(f'aven-fixture-{item["id"]}-v1')
    msg['Content-Language'] = item['lang']
    return msg


def fixture_preferences():
    return {
        'mail.accountmanager.accounts': 'account1',
        'mail.accountmanager.defaultaccount': 'account1',
        'mail.accountmanager.localfoldersserver': 'server1',
        'mail.account.account1.server': 'server1',
        'mail.account.account1.identities': 'id1',
        'mail.server.server1.type': 'none',
        'mail.server.server1.hostname': 'Local Folders',
        'mail.server.server1.name': 'Local Folders',
        'mail.server.server1.userName': 'nobody',
        'mail.server.server1.directory-rel': '[ProfD]Mail/Local Folders',
        'mail.server.server1.storeContractID': '@mozilla.org/msgstore/berkeleystore;1',
        'mail.server.server1.login_at_startup': False,
        'mail.server.server1.check_new_mail': False,
        'mail.identity.id1.fullName': '安宁',
        'mail.identity.id1.useremail': 'anning@example.invalid',
        'mail.identity.id1.valid': True,
        'mail.identity.id1.compose_html': True,
        'mail.identity.id1.draft_folder': 'mailbox://nobody@Local%20Folders/Drafts',
        'mail.identity.id1.stationery_folder': 'mailbox://nobody@Local%20Folders/Templates',
        'mail.identity.id1.fcc_folder': 'mailbox://nobody@Local%20Folders/Sent',
        # No SMTP account exists. This is a local fixture, never a mail service.
        'mail.smtpservers': '',
        'mail.shell.checkDefaultClient': False,
        'mailnews.start_page.enabled': False,
        'mail.provider.suppress_dialog_on_startup': True,
        'mail.winsearch.firstRunDone': True,
        'offline.startup_state': 2,
        'offline.autoDetect': False,
    }


def populate_fixtures(profile):
    data = json.loads(FIXTURES.read_text(encoding='utf-8'))
    local = profile / 'Mail/Local Folders'
    local.mkdir(parents=True)
    exports = profile / 'fixture-export'
    exports.mkdir()
    for folder, items, draft in [('Inbox', data['messages'], False), ('Drafts', [data['draft']], True)]:
        mbox = mailbox.mbox(local / folder, create=True)
        try:
            for item in items:
                msg = make_message(item, draft)
                mbox.add(b'From nobody Tue Sep 15 01:00:00 2026\n' + msg.as_bytes())
                (exports / f'{item["id"]}.eml').write_bytes(msg.as_bytes())
        finally:
            mbox.close()
    for folder in ['Sent', 'Trash', 'Templates', 'Unsent Messages']:
        (local / folder).touch()
    (exports / 'compose.html').write_text(letter_html(data['draft']), encoding='utf-8')
    (exports / 'compose.txt').write_text('\n\n'.join(data['draft']['paragraphs']), encoding='utf-8')
    save_json(profile / 'session.json', {
        'rev': 0, 'windows': [{'type': '3pane', 'tabs': {'rev': 0, 'selectedIndex': 0, 'tabs': [
            {'mode': 'mail3PaneTab', 'state': {'firstTab': True, 'folderPaneVisible': True,
             'folderURI': 'mailbox://nobody@Local%20Folders/Inbox', 'messagePaneVisible': True}, 'ext': {}}
        ]}}]
    })


def create(profile, variant, demo):
    if profile.exists():
        raise SystemExit(f'Refusing to overwrite existing directory: {profile}. Choose a new profile path.')
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.mkdir(mode=0o700)
    prefs = candidate_preferences() if variant == 'aven' else {}
    if demo:
        prefs.update(fixture_preferences())
        populate_fixtures(profile)
    if variant == 'aven':
        install_chrome(profile)
        install_layout(profile)
    # Seed prefs.js once rather than user.js, so application UI changes persist.
    (profile / 'prefs.js').write_text(prefs_text(prefs), encoding='utf-8')
    save_json(profile / MARKER, {
        'schema_version': 1, 'variant': variant, 'local_fixtures': demo,
        'fixture_sha256': hashlib.sha256(FIXTURES.read_bytes()).hexdigest() if demo else None,
        'visual_validation': 'pending-native-guest-screenshots',
        'prefs_source': 'mail/profile.py', 'base_profile_modified': False,
    })
    print(json.dumps({'created': str(profile), 'variant': variant, 'local_fixtures': demo}))


def launch(profile, executable, scene):
    marker_path = profile / MARKER
    if not marker_path.is_file():
        raise SystemExit('Launch only accepts an isolated Aven-created profile.')
    marker = json.loads(marker_path.read_text())
    argv = [executable, '-no-remote', '-profile', str(profile)]
    if marker['local_fixtures']:
        argv.append('-offline')
    if scene == 'compose':
        if not marker['local_fixtures']:
            raise SystemExit('Compose fixture requires --demo when creating the profile.')
        path = profile / 'fixture-export/compose.html'
        if any(c in str(path) for c in ["'", ',', '\n', '\r']):
            raise SystemExit('Thunderbird compose argument paths cannot contain quotes, commas or newlines.')
        data = json.loads(FIXTURES.read_text(encoding='utf-8'))['draft']
        argv.extend(['-compose', f"preselectid=id1,format=html,to='{data['to_address']}',subject='{data['subject']}',message='{path}'"])
    env = os.environ.copy()
    env.setdefault('MOZ_ENABLE_WAYLAND', '1')
    return subprocess.call(argv, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    c = commands.add_parser('create')
    c.add_argument('--variant', required=True, choices=['stock', 'aven'])
    c.add_argument('--profile', type=Path, required=True)
    c.add_argument('--demo', action='store_true', help='add local mailbox and writing fixture; no mail server')
    r = commands.add_parser('refresh', help='Refresh appearance only; profile must be closed')
    r.add_argument('--profile', type=Path, required=True)
    l = commands.add_parser('launch')
    l.add_argument('--profile', type=Path, required=True)
    l.add_argument('--executable', default='thunderbird')
    l.add_argument('--scene', choices=['read', 'compose'], default='read')
    args = parser.parse_args()
    profile = args.profile.expanduser().resolve()
    if args.command == 'create':
        create(profile, args.variant, args.demo)
        return 0
    if args.command == 'refresh':
        refresh(profile)
        return 0
    return launch(profile, args.executable, args.scene)


if __name__ == '__main__':
    raise SystemExit(main())
