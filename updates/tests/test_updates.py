"""Trust boundary, incremental delivery and transaction failure regressions."""
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aven
import build

ROOT = Path(__file__).resolve().parents[2]


class Updates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory()
        cls.base = Path(cls.workspace.name)
        cls.key = cls.base/'signing.pem'
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048',
                        '-out', str(cls.key)], check=True, capture_output=True)
        cls.feed = cls.base/'feed'
        cls.payload = build.build(ROOT, cls.feed, cls.key, '0.4.0', 1, 'union')
        cls.envelope = json.loads((cls.feed/'channel.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.client = aven.Client(self.home)
        self.client.bootstrap((self.feed/'channel.json').as_uri(), self.feed/'release.pub')

    def test_signature_and_tamper(self):
        self.assertEqual(aven.verify(self.envelope, self.feed/'release.pub'), self.payload)
        changed = copy.deepcopy(self.envelope)
        changed['payload']['style'] = 'breeze'
        with self.assertRaisesRegex(ValueError, 'signature'):
            aven.verify(changed, self.feed/'release.pub')

    def test_wrong_key_rejected(self):
        key = self.home/'wrong.pem'
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:2048',
                        '-out', str(key)], check=True, capture_output=True)
        public = self.home/'wrong.pub'
        subprocess.run(['openssl', 'pkey', '-in', str(key), '-pubout', '-out', str(public)], check=True)
        with self.assertRaises(ValueError):
            aven.verify(self.envelope, public)

    def test_expired_and_incomplete_release(self):
        value = copy.deepcopy(self.payload)
        value['expires'] = '2020-01-01T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError, 'expired'):
            aven.validate_manifest(value)
        value = copy.deepcopy(self.payload)
        del value['components']['browser']
        with self.assertRaises(ValueError):
            aven.validate_manifest(value)

    def test_stage_reuses_verified_archives_and_repairs_corrupt_cache(self):
        source, downloaded = self.client.stage(self.payload, self.envelope, (self.feed/'channel.json').as_uri())
        self.assertEqual(downloaded, sum(p['bytes'] for p in self.payload['components'].values()))
        (source/'updates/aven.py').write_text('corrupt extracted copy')
        source, downloaded = self.client.stage(self.payload, self.envelope, (self.feed/'channel.json').as_uri())
        self.assertEqual(downloaded, 0)
        self.assertEqual((source/'updates/aven.py').read_bytes(), (ROOT/'updates/aven.py').read_bytes())
        item = self.payload['components']['browser']
        (self.client.cache/item['file']).write_bytes(b'corrupt download')
        source, downloaded = self.client.stage(self.payload, self.envelope, (self.feed/'channel.json').as_uri())
        self.assertEqual(downloaded, item['bytes'])

    def test_only_changed_component_is_downloaded(self):
        self.client.stage(self.payload, self.envelope, (self.feed/'channel.json').as_uri())
        aven.save(self.client.receipt, {'release': self.payload})
        changed = copy.deepcopy(self.payload)
        changed['version'] = '0.4.1'
        changed['sequence'] = 2
        changed['components']['visual']['sha256'] = 'a'*64
        changed['components']['visual']['file'] = 'visual-'+'a'*64+'.tar.gz'
        plan = self.client.plan(changed)
        self.assertEqual(plan['changed_components'], ['visual'])
        self.assertEqual(plan['download_bytes'], changed['components']['visual']['bytes'])

    def test_sequence_replay_and_equivocation_rejected(self):
        self.client.release()
        aven.save(self.client.state/'highest.json', {'sequence': 2, 'sha256': 'a'*64})
        with self.assertRaisesRegex(ValueError, 'older release'):
            self.client.release()
        aven.save(self.client.state/'highest.json', {'sequence': 1, 'sha256': 'a'*64})
        with self.assertRaisesRegex(ValueError, 'reused'):
            self.client.release()

    def test_safe_archive_rejects_traversal_links_and_wrong_component(self):
        for name, kind in [('visual/../../escape', tarfile.REGTYPE),
                           ('/visual/escape', tarfile.REGTYPE),
                           ('browser/file', tarfile.REGTYPE),
                           ('visual/link', tarfile.SYMTYPE),
                           ('visual/hardlink', tarfile.LNKTYPE)]:
            archive = self.home/'bad.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                entry = tarfile.TarInfo(name)
                entry.type = kind
                entry.linkname = '/tmp/escape'
                tar.addfile(entry, io.BytesIO())
            with self.assertRaises(ValueError, msg=name):
                aven.unpack(archive, self.home/'extract', 'visual')

    def test_non_https_remote_refused(self):
        for url in ('http://example.com/channel.json', 'file://evil/path', 'https://user:password@example.com/a'):
            with self.assertRaises(ValueError):
                aven.secure_url(url)

    def test_failure_keeps_previous_receipt_and_recovery_journal(self):
        previous = {'release': self.payload}
        aven.save(self.client.receipt, previous)
        def fail(*args, **kwargs):
            if 'apply' in args:
                raise subprocess.CalledProcessError(1, args)
        with patch.object(aven, 'require_closed'), patch.object(aven, 'require_session'), patch.object(aven, 'run', side_effect=fail):
            with self.assertRaises(subprocess.CalledProcessError):
                self.client.apply(self.payload, ROOT, 0)
        self.assertEqual(aven.read_json(self.client.receipt), previous)
        self.assertTrue(self.client.journal.exists())
        with patch.object(aven, 'require_closed'), patch.object(aven, 'run'):
            self.client.recover()
        self.assertFalse(self.client.journal.exists())
        self.assertEqual(aven.read_json(self.client.receipt), previous)

    def test_bootstrap_never_replaces_existing_command(self):
        home = self.home/'another-home'
        command = home/'.local/bin/aven'
        aven.atomic(command, b'#!/bin/sh\necho custom\n')
        other = aven.Client(home)
        with self.assertRaises(ValueError):
            other.bootstrap((self.feed/'channel.json').as_uri(), self.feed/'release.pub')
        self.assertFalse(other.config.exists())
        self.assertIn(b'custom', command.read_bytes())


if __name__ == '__main__':
    unittest.main()
