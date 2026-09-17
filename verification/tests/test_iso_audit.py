import importlib.util
import hashlib
import json
from pathlib import Path
import shlex
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

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


class ExplicitReleaseAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.platform = json.loads((Path(__file__).parents[2] / "iso/platform.json").read_text())
        self.platform_file = self.root / "platform.json"
        self.platform_file.write_text(json.dumps(self.platform))

    def installed_args(self):
        return SimpleNamespace(ssh_host="aven@localhost", ssh_port=2226, identity=None, known_hosts=None,
            root_command="sudo -n", python="python3", manifest=None, platform=self.platform_file,
            layer=None, base=None, profile_user="aven")

    def test_installed_streams_contract_without_relying_on_guest_platform_file(self):
        output = {"atomic_identity_passed": True, "desktop_startup_passed": True, "first_login_passed": True}
        completed = SimpleNamespace(returncode=0, stdout=json.dumps(output), stderr="")
        with patch.object(audit.subprocess, "run", return_value=completed) as run:
            result = audit.installed(self.installed_args())
        self.assertTrue(result["installed_checks_passed"])
        ssh = run.call_args.args[0]
        remote = shlex.split(ssh[-1])
        expected = json.loads(remote[remote.index("--expected-json") + 1])
        self.assertEqual(len(expected["ostree"]["local_replacements"]), 84)
        self.assertEqual(remote[-2:], ["--profile-user", "aven"])
        self.assertIn("def assess_first_login", run.call_args.kwargs["input"])

    def test_new_profile_cannot_pass_with_only_atomic_and_login_manager_success(self):
        output = {"atomic_identity_passed": True, "desktop_startup_passed": True}
        completed = SimpleNamespace(returncode=0, stdout=json.dumps(output), stderr="")
        with patch.object(audit.subprocess, "run", return_value=completed):
            self.assertFalse(audit.installed(self.installed_args())["installed_checks_passed"])

    def test_historical_default_does_not_require_new_first_login_proof(self):
        args = self.installed_args()
        args.platform, args.profile_user = None, None
        output = {"atomic_identity_passed": True, "desktop_startup_passed": True}
        with patch.object(audit.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=json.dumps(output), stderr="")):
            self.assertTrue(audit.installed(args)["installed_checks_passed"])

    def media_fixture(self):
        raw_layer, raw_base, raw_cache = b"layer object", b"signed base object", b"cached package commit"
        digest = lambda raw: hashlib.sha256(raw).hexdigest()
        tree = self.platform["ostree"]
        tree.update(layered_commit=digest(raw_layer), base_commit=digest(raw_base))
        self.platform_file.write_text(json.dumps(self.platform))
        image = self.root / "release.iso"
        image.write_bytes(b"\0" * 32768 + b"\x01CD001\x01")
        manifest = self.platform | {"iso": {"file": image.name, "sha256": audit.sha(image)},
            "paths": {"kickstart": "/aven/aven.ks", "repo": "/aven/ostree/repo"}}
        manifest_file = self.root / "release.json"
        manifest_file.write_text(json.dumps(manifest))
        repo = "/aven/ostree/repo"
        self.contents = {
            "/aven/aven.ks": PublicKickstartAuditTests.SAFE.replace("aven/44/x86_64/prototype", tree["installer_ref"]).encode(),
            repo + "/config": b"[core]\nmode=archive-z2\n",
            repo + "/refs/heads/" + tree["installer_ref"]: tree["layered_commit"].encode(),
            "/boot/grub2/grub.cfg": b"inst.ks=cdrom:/aven/aven.ks",
            "/EFI/BOOT/grub.cfg": b"inst.ks=cdrom:/aven/aven.ks",
        }
        for raw in [raw_layer, raw_base, raw_cache]:
            checksum = digest(raw)
            self.contents[repo + "/objects/" + checksum[:2] + "/" + checksum[2:] + ".commit"] = raw
        checksum = digest(raw_base)
        self.contents[repo + "/objects/" + checksum[:2] + "/" + checksum[2:] + ".commitmeta"] = b"signature metadata"
        self.cache = {ref.removeprefix("rpmostree/pkg/"): digest(raw_cache).encode() for ref in tree["package_cache_refs"]}
        return SimpleNamespace(manifest=manifest_file, iso=image, platform=self.platform_file, kickstart_path=None, repo_path=None)

    def fake_xorriso(self, argv, **kwargs):
        if "-report_el_torito" in argv:
            return SimpleNamespace(stdout="El Torito boot img : 1 BIOS y\nEl Torito boot img : 2 UEFI y\nGPT\n", stderr="")
        for index, word in enumerate(argv):
            if word != "-extract":
                continue
            source, target = argv[index + 1], Path(argv[index + 2])
            if source.endswith("/refs/heads/rpmostree/pkg"):
                target.mkdir()
                for relative, raw in self.cache.items():
                    path = target / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(raw)
            else:
                target.write_bytes(self.contents[source])
        return SimpleNamespace(stdout="", stderr="")

    def test_explicit_union_media_contract_and_all_103_cache_refs(self):
        args = self.media_fixture()
        with patch.object(audit, "run", side_effect=self.fake_xorriso):
            result = audit.media(args)
        self.assertTrue(result["static_media_checks_passed"], result["errors"])
        self.assertEqual(result["facts"]["package_cache_refs_checked"], 103)

    def test_media_missing_cache_ref_is_rejected(self):
        args = self.media_fixture()
        self.cache.pop(next(iter(self.cache)))
        with patch.object(audit, "run", side_effect=self.fake_xorriso):
            result = audit.media(args)
        self.assertFalse(result["static_media_checks_passed"])
        self.assertTrue(any("cache ref" in error for error in result["errors"]))

    def test_media_corrupt_cache_commit_is_rejected(self):
        args = self.media_fixture()
        for path, raw in self.contents.items():
            if raw == b"cached package commit":
                self.contents[path] = b"corrupt cache commit"
        with patch.object(audit, "run", side_effect=self.fake_xorriso):
            result = audit.media(args)
        self.assertFalse(result["static_media_checks_passed"])
        self.assertTrue(any("cache commit object" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
