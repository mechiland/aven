#!/usr/bin/env python3
"""Create an isolated Thunderbird profile; existing profiles are never changed."""
from __future__ import annotations
import argparse
from email import policy
from email.message import EmailMessage
from email.utils import formataddr
import hashlib
import html
import json
import mailbox
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'fixtures/mail/messages.json'
MARKER = 'aven-mail-profile.json'


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def prefs_text(prefs):
    return '// Aven isolated prototype profile; all ordinary prefs remain editable.\n' + ''.join(
        f'user_pref({json.dumps(k)}, {json.dumps(v, ensure_ascii=False)});\n' for k, v in sorted(prefs.items()))


def candidate_preferences():
    prefs = {
        'toolkit.legacyUserProfileCustomizations.stylesheets': True,
        'mail.tabs.drawInTitlebar': False,
        'mail.uidensity': 1,
        # 0 follows the OS; Thunderbird's custom font-size preference is in px.
        # The 11pt root CSS keeps its density calculator aligned with native UI.
        'mail.uifontsize': 0,
        'mail.pane_config.dynamic': 2,
        'mail.threadpane.listview': 0,
        'mail.biff.play_sound': False,
        'mail.biff.use_system_alert': True,
        'mailnews.start_page.enabled': False,
        'mailnews.display.prefer_plaintext': False,
        'mail.fixed_width_messages': False,
        'msgcompose.font_face': 'Noto Sans',
        'msgcompose.font_size': 'medium',
    }
    for group, family in [('x-western', 'Noto Sans'), ('x-unicode', 'Noto Sans'),
                          ('zh-CN', 'Noto Sans CJK SC'), ('zh-TW', 'Noto Sans CJK TC'),
                          ('zh-HK', 'Noto Sans CJK HK')]:
        prefs.update({
            f'font.default.{group}': 'sans-serif',
            f'font.name.sans-serif.{group}': family,
            f'font.name.monospace.{group}': 'Noto Sans Mono',
            f'font.name-list.sans-serif.{group}': f'Noto Sans, {family}, sans-serif',
            f'font.name-list.monospace.{group}': f'Noto Sans Mono, {family}, monospace',
            f'font.size.variable.{group}': 17 if group.startswith('zh') else 16,
            f'font.size.monospace.{group}': 14,
        })
    return prefs


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
        shutil.copytree(ROOT / 'mail/chrome', profile / 'chrome')
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
    l = commands.add_parser('launch')
    l.add_argument('--profile', type=Path, required=True)
    l.add_argument('--executable', default='thunderbird')
    l.add_argument('--scene', choices=['read', 'compose'], default='read')
    args = parser.parse_args()
    profile = args.profile.expanduser().resolve()
    if args.command == 'create':
        create(profile, args.variant, args.demo)
        return 0
    return launch(profile, args.executable, args.scene)


if __name__ == '__main__':
    raise SystemExit(main())
