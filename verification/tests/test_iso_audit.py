import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))
spec = importlib.util.spec_from_file_location("iso_audit", Path(__file__).parents[1] / "iso_audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class PublicKickstartAuditTests(unittest.TestCase):
    SAFE = """graphical
rootpw --lock
ostreesetup --osname=fedora --remote=aven-install --url=file:///run/install/repo/aven/ostree/repo --ref=aven/44/x86_64/prototype --nogpg
%post --nochroot --erroronfail
python3 /run/install/repo/aven/post-install.py
%end
"""

    def test_interactive_public_source_and_locked_root_are_allowed(self):
        errors, setup = audit.check_kickstart(self.SAFE)
        self.assertEqual(errors, [])
        self.assertEqual(audit.option(setup, "--osname"), "fedora")

    def test_existing_lab_kickstart_is_rejected_for_public_media(self):
        lab = Path(__file__).parents[2] / "baseline/stock.ks.in"
        errors, _ = audit.check_kickstart(lab.read_text())
        self.assertTrue(any("clearpart" in e for e in errors))
        self.assertTrue(any("credentials" in e for e in errors))
        self.assertTrue(any("provisioning" in e for e in errors))

    def test_automatic_partitioning_and_disk_selection_are_rejected(self):
        for command in ["autopart", "ignoredisk --only-use=vda", "part / --ondisk=vda", "zerombr"]:
            with self.subTest(command=command):
                self.assertTrue(audit.check_kickstart(command + "\n" + self.SAFE)[0])

    def test_scripted_credentials_are_rejected(self):
        for script in ["useradd aven", "echo 'aven ALL=(ALL) NOPASSWD: ALL'", "cat > /home/aven/.ssh/authorized_keys", "echo '[Autologin]' > display.conf"]:
            with self.subTest(script=script):
                text = self.SAFE.replace("%end", script + "\n%end")
                self.assertTrue(audit.check_kickstart(text)[0])

    def test_comments_do_not_trigger_credential_detection(self):
        errors, _ = audit.check_kickstart("# No NOPASSWD, autologin, or useradd here.\n" + self.SAFE)
        self.assertEqual(errors, [])

    def test_continuation_does_not_hide_root_password(self):
        text = self.SAFE.replace("rootpw --lock", "rootpw \\\n  --iscrypted SHA512PASSWORD")
        self.assertTrue(audit.check_kickstart(text)[0])

    def test_external_include_is_not_silently_accepted(self):
        self.assertTrue(audit.check_kickstart("%include /uninspected.ks\n" + self.SAFE)[0])

    def test_iso_path_cannot_escape(self):
        for path in ["../../foo", "/aven/../etc/passwd", "//host/share"]:
            with self.assertRaises(ValueError):
                audit.iso_path(path)


if __name__ == "__main__":
    unittest.main()
