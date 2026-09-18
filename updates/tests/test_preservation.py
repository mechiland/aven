"""Run real component installers in disposable homes; exercise recovery merges."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'updates'))
spec = importlib.util.spec_from_file_location('up_profile', ROOT/'updates/profile.py')
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)


class Preservation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)/'home'
        self.home.mkdir()

    def install(self, component, *options):
        subprocess.run([sys.executable, str(ROOT/component/'install.py'), '--home', str(self.home), *options],
                       check=True, capture_output=True)

    def test_browser_update_preserves_prefs_and_user_files(self):
        self.install('browser')
        directory = self.home/'.local/share/aven/firefox'
        prefs = directory/'prefs.js'
        custom = prefs.read_text().replace('"browser.uidensity", 1', '"browser.uidensity", 2')
        custom += 'user_pref("user.test", "中文偏好");\n'
        prefs.write_text(custom)
        personal = directory/'user-data'
        personal.write_bytes(b'private browser data')
        chrome = directory/'chrome/userChrome.css'
        chrome.write_text('old chrome')
        self.install('browser', '--update')
        self.assertEqual(prefs.read_text(), custom)
        self.assertEqual(personal.read_bytes(), b'private browser data')
        self.assertEqual(chrome.read_bytes(), (ROOT/'browser/chrome/userChrome.css').read_bytes())

    def test_mail_update_preserves_accounts_preferences_and_toolbar(self):
        self.install('mail')
        directory = self.home/'.local/share/aven/mail/default'
        prefs = directory/'prefs.js'
        custom = prefs.read_text()+'user_pref("mail.accountmanager.accounts", "account42");\n'
        prefs.write_text(custom)
        layout = directory/'xulstore.json'
        layout.write_text('{"user-custom-toolbar":"中文"}')
        message = directory/'Mail/Local Folders/Inbox'
        message.parent.mkdir(parents=True)
        message.write_bytes(b'personal mail')
        self.install('mail', '--update')
        self.assertEqual(prefs.read_text(), custom)
        self.assertEqual(layout.read_text(), '{"user-custom-toolbar":"中文"}')
        self.assertEqual(message.read_bytes(), b'personal mail')

    def test_files_assets_update_does_not_touch_layout_or_shortcuts(self):
        config = self.home/'.config/dolphinrc'
        config.parent.mkdir()
        config.write_text('[General]\nViewMode=2\n')
        self.install('files', '--xmlgui-version', '49', '--assets-only')
        self.assertEqual(config.read_text(), '[General]\nViewMode=2\n')
        self.assertFalse((self.home/'.local/share/kxmlgui5/dolphin/dolphinui.rc').exists())
        self.assertTrue((self.home/'.local/libexec/aven-preview/aven-preview').is_file())

    def test_rollback_restores_changed_assets_but_keeps_later_preference_edits(self):
        asset = self.home/'.local/share/union/styles/aven-mist/contents/css/style.css'
        asset.parent.mkdir(parents=True)
        asset.write_text('old asset')
        prefs = self.home/'.config/dolphinrc'
        prefs.parent.mkdir()
        prefs.write_text('original preferences')
        before, after = Path(self.temp.name)/'before', Path(self.temp.name)/'after'
        profile.snapshot(self.home, before)
        asset.write_text('new asset')
        profile.snapshot(self.home, after)
        prefs.write_text('user changed preferences after updating')
        with patch.object(profile.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)), patch.object(profile, 'run'):
            profile.restore_snapshot(self.home, before, after)
        self.assertEqual(asset.read_text(), 'old asset')
        self.assertEqual(prefs.read_text(), 'user changed preferences after updating')

    def test_rollback_conflicts_are_detected_before_any_asset_is_changed(self):
        asset = self.home/'.local/share/union/styles/aven-mist/contents/css/style.css'
        asset.parent.mkdir(parents=True)
        asset.write_text('old')
        before, after = Path(self.temp.name)/'before', Path(self.temp.name)/'after'
        profile.snapshot(self.home, before)
        asset.write_text('new')
        profile.snapshot(self.home, after)
        asset.write_text('user edit after update')
        with patch.object(profile.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaisesRegex(ValueError, 'changed since'):
                profile.restore_snapshot(self.home, before, after)
        self.assertEqual(asset.read_text(), 'user edit after update')

    def test_asset_symlink_is_rejected_before_installation(self):
        directory = self.home/'.local/share/aven/firefox/chrome'
        directory.mkdir(parents=True)
        victim = self.home/'personal'
        victim.write_text('keep me')
        (directory/'userChrome.css').symlink_to(victim)
        with self.assertRaisesRegex(ValueError, 'symlinked'):
            profile.snapshot(self.home, Path(self.temp.name)/'snapshot')
        self.assertEqual(victim.read_text(), 'keep me')

    def test_obsolete_assets_are_removed_only_if_unchanged_by_user(self):
        previous = Path(self.temp.name)/'previous'
        old = previous/'browser/chrome'
        old.mkdir(parents=True)
        target = self.home/'.local/share/aven/firefox/chrome'
        target.mkdir(parents=True)
        for name in ('deleted.css', 'customized.css'):
            (old/name).write_text('previous shipped content')
            (target/name).write_text('previous shipped content')
        (target/'customized.css').write_text('user override')
        profile.prune_obsolete(self.home, previous)
        self.assertFalse((target/'deleted.css').exists())
        self.assertEqual((target/'customized.css').read_text(), 'user override')

    def test_rollback_can_restore_a_file_deleted_by_the_new_release(self):
        target = self.home/'.local/share/aven/firefox/chrome/obsolete.css'
        target.parent.mkdir(parents=True)
        target.write_text('previous asset')
        before, after = Path(self.temp.name)/'before', Path(self.temp.name)/'after'
        profile.snapshot(self.home, before)
        target.unlink()
        profile.snapshot(self.home, after)
        with patch.object(profile.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)), patch.object(profile, 'run'):
            profile.restore_snapshot(self.home, before, after)
        self.assertEqual(target.read_text(), 'previous asset')


if __name__ == '__main__':
    unittest.main()
