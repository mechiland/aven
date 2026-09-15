import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("iso_deployment_probe", Path(__file__).parents[1] / "iso_deployment_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class IsoDeploymentIdentityTests(unittest.TestCase):
    def setUp(self):
        self.status = {"deployments": [{"booted": True, "checksum": probe.LAYER,
            "base-checksum": probe.BASE, "origin": probe.ORIGIN, "unlocked": "none", "gpg-enabled": True,
            "layered-commit-meta": {"rpmostree.clientlayer": True}, "requested-packages": sorted(probe.PACKAGES)}]}
        self.origin = "[origin]\nbaserefspec=" + probe.ORIGIN + "\n[packages]\nrequested=" + ";".join(sorted(probe.PACKAGES)) + ";\n"

    def test_exact_layer_and_persistent_origin(self):
        self.assertEqual(probe.assess(self.status, self.origin), [])

    def test_layer_without_imported_base_is_rejected(self):
        del self.status["deployments"][0]["base-checksum"]
        self.assertTrue(any("base" in e for e in probe.assess(self.status, self.origin)))

    def test_installer_ref_is_not_future_update_origin(self):
        self.status["deployments"][0]["origin"] = "aven-installer:aven/44/x86_64/prototype"
        self.assertTrue(any("origin" in e for e in probe.assess(self.status, self.origin)))

    def test_lost_layering_request_is_rejected(self):
        self.assertTrue(any("package persistence" in e for e in probe.assess(self.status, "[origin]\nbaserefspec=" + probe.ORIGIN)))

    def test_ambiguous_booted_deployment_is_rejected(self):
        self.status["deployments"].append(copy.deepcopy(self.status["deployments"][0]))
        self.assertTrue(probe.assess(self.status, self.origin))

    def test_plain_origin_refspec_is_rejected(self):
        self.assertTrue(any("baserefspec" in e for e in probe.assess(self.status, self.origin.replace("baserefspec", "refspec"))))

    def test_disabled_future_signature_verification_is_rejected(self):
        self.status["deployments"][0]["gpg-enabled"] = False
        self.assertTrue(any("GPG" in e for e in probe.assess(self.status, self.origin)))


if __name__ == "__main__":
    unittest.main()
