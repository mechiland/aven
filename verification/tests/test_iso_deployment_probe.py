import copy
import importlib.util
import json
from pathlib import Path
import tempfile
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


class IsoDesktopStartupTests(unittest.TestCase):
    def setUp(self):
        self.probes = {
            "system_flatpak_apps": {"exit_code": 0, "stdout": "org.example.Unrelated\n"},
            "display_manager": {"exit_code": 0, "stdout": "Id=plasmalogin.service\nLoadState=loaded\nActiveState=active\nUnitFileState=enabled\n"},
            "default_target": {"exit_code": 0, "stdout": "graphical.target\n"},
        }

    def test_native_login_and_unrelated_flatpak_are_allowed(self):
        self.assertEqual(probe.assess_desktop(self.probes), [])

    def test_each_bundled_duplicate_is_rejected(self):
        for app in probe.DUPLICATE_FLATPAKS:
            with self.subTest(app=app):
                self.probes["system_flatpak_apps"]["stdout"] = app + "\n"
                self.assertTrue(any(app in e for e in probe.assess_desktop(self.probes)))

    def test_failed_flatpak_query_is_not_empty_application_success(self):
        self.probes["system_flatpak_apps"] = {"exit_code": 1, "stdout": ""}
        self.assertTrue(any("command failed" in e for e in probe.assess_desktop(self.probes)))

    def test_disabled_but_currently_running_login_service_is_rejected(self):
        self.probes["display_manager"]["stdout"] = self.probes["display_manager"]["stdout"].replace("UnitFileState=enabled", "UnitFileState=disabled")
        self.assertTrue(probe.assess_desktop(self.probes))

    def test_old_display_manager_is_rejected(self):
        self.probes["display_manager"]["stdout"] = self.probes["display_manager"]["stdout"].replace("plasmalogin", "sddm")
        self.assertTrue(probe.assess_desktop(self.probes))

    def test_text_default_target_is_rejected(self):
        self.probes["default_target"]["stdout"] = "multi-user.target\n"
        self.assertTrue(any("graphical.target" in e for e in probe.assess_desktop(self.probes)))


class UnionReleaseContractTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads((Path(__file__).parents[2] / "iso/platform.json").read_text())
        self.expected = probe.expectation(self.document)
        tree = self.expected["ostree"]
        self.status = {"deployments": [{"booted": True, "checksum": tree["layered_commit"],
            "base-checksum": tree["base_commit"], "origin": tree["origin"], "unlocked": "none", "gpg-enabled": True,
            "layered-commit-meta": {"rpmostree.clientlayer": True}, "requested-packages": tree["requested_packages"],
            "requested-local-packages": [v.split(":", 1)[1] for v in tree["requested_local_packages"]],
            "requested-base-local-replacements": [v.split(":", 1)[1] for v in tree["local_replacements"]]}]}
        self.origin = ("[origin]\nbaserefspec=" + tree["origin"] + "\n[packages]\nrequested="
            + ";".join(tree["requested_packages"]) + ";\nrequested-local=" + ";".join(tree["requested_local_packages"])
            + ";\n[overrides]\nreplace-local=" + ";".join(tree["local_replacements"]) + ";\n")

    def test_explicit_union_contract_preserves_two_local_eighty_four_overrides_and_cache(self):
        tree = self.expected["ostree"]
        self.assertEqual([len(tree[k]) for k in ["requested_local_packages", "local_replacements", "package_cache_refs"]], [2, 84, 103])
        self.assertEqual(probe.assess(self.status, self.origin, expected=self.expected), [])
        self.assertNotEqual(probe.assess(self.status, self.origin), [])

    def test_each_local_origin_entry_and_checksum_is_required(self):
        for field in ["requested_local_packages", "local_replacements"]:
            for entry in self.expected["ostree"][field]:
                with self.subTest(entry=entry):
                    changed = self.origin.replace(entry, "0" * 64 + ":" + entry.split(":", 1)[1])
                    self.assertTrue(any("checksum:NEVRA" in error for error in probe.assess(self.status, changed, expected=self.expected)))

    def test_lost_runtime_local_requests_are_rejected(self):
        for key in ["requested-local-packages", "requested-base-local-replacements"]:
            status = copy.deepcopy(self.status)
            status["deployments"][0][key].pop()
            self.assertTrue(probe.assess(status, self.origin, expected=self.expected))

    def test_epoch_in_nevra_is_not_lost(self):
        values = self.status["deployments"][0]["requested-base-local-replacements"]
        self.assertTrue(any("-1:" in value for value in values))
        self.assertEqual(probe.assess(self.status, self.origin, expected=self.expected), [])

    def test_incomplete_release_cache_contract_is_rejected(self):
        tree = self.document["ostree"]
        tree["package_cache_refs"] = []
        with self.assertRaisesRegex(ValueError, "cache ref"):
            probe.expectation(self.document)

    def test_checksumless_local_origin_contract_is_rejected(self):
        self.document["ostree"]["requested_local_packages"][0] = "plasma-union-6.7.90-1.fc44.x86_64"
        with self.assertRaisesRegex(ValueError, "checksum:NEVRA"):
            probe.expectation(self.document)

    def test_conflicting_explicit_commit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "differs"):
            probe.expectation(self.document, layer=probe.LAYER)

    def test_platform_and_manifest_must_agree(self):
        with tempfile.TemporaryDirectory() as temporary:
            platform = Path(temporary) / "platform.json"
            manifest = Path(temporary) / "release.json"
            platform.write_text(json.dumps(self.document))
            manifest.write_text(json.dumps(self.document | {"iso": {"file": "release.iso"}}))
            self.assertEqual(probe.load_expectation(manifest, platform), self.expected)
            changed = copy.deepcopy(self.document)
            changed["profile"]["style"] = "breeze"
            manifest.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "contracts differ"):
                probe.load_expectation(manifest, platform)

    def test_cache_rejects_missing_unresolved_or_corrupt_commit(self):
        refs = self.expected["ostree"]["package_cache_refs"]
        records = {ref: {"checksum": "a" * 64, "object_sha256": "a" * 64} for ref in refs}
        self.assertEqual(probe.assess_cache_refs(refs, records), [])
        records.pop(refs[0])
        records[refs[1]]["object_sha256"] = "b" * 64
        records[refs[2]]["checksum"] = "not-a-checksum"
        self.assertEqual(len(probe.assess_cache_refs(refs, records)), 3)


class FirstLoginUnionTests(unittest.TestCase):
    def setUp(self):
        self.profile = {"style": "union", "decoration": "aven"}
        self.record = {"home": "/home/reader", "markers": {phase: {
            "schema_version": 1, "phase": phase, "home": "/home/reader", "completed_at": "2026-09-17T00:00:00Z"}
            for phase in ["seed", "layout"]},
            "settings": {"widgetStyle": "Union", "unionStyle": "aven-mist", "shellTheme": "aven-dock"},
            "union_assets_present": True, "live_panels": {"exit_code": 0, "json": [{"id": 2,
                "location": "bottom", "alignment": "center", "height": 58, "lengthMode": "fit",
                "opacity": "translucent", "floating": True}]}}

    def test_complete_markers_selected_theme_and_running_dock(self):
        self.assertEqual(probe.assess_first_login(self.record, self.profile), [])

    def test_breeze_left_active_after_markers_is_rejected(self):
        self.record["settings"]["widgetStyle"] = "Breeze"
        self.assertTrue(probe.assess_first_login(self.record, self.profile))

    def test_completed_seed_without_layout_is_rejected(self):
        del self.record["markers"]["layout"]
        self.assertTrue(probe.assess_first_login(self.record, self.profile))

    def test_markers_from_another_home_are_rejected(self):
        self.record["markers"]["seed"]["home"] = "/home/aven"
        self.assertTrue(probe.assess_first_login(self.record, self.profile))

    def test_inactive_session_or_empty_panels_cannot_pass_from_config_alone(self):
        for live in [{"exit_code": 1}, {"exit_code": 0, "json": []}, {"exit_code": 0, "json": {}}]:
            self.record["live_panels"] = live
            self.assertTrue(probe.assess_first_login(self.record, self.profile))

    def test_previous_wide_panel_is_rejected(self):
        self.record["live_panels"]["json"][0].update(height=48, lengthMode="custom", opacity="adaptive")
        self.assertTrue(probe.assess_first_login(self.record, self.profile))

    def test_no_implicit_user_selection(self):
        record = probe.collect_first_login(None)
        self.assertTrue(any("--profile-user" in error for error in record["errors"]))
        self.assertTrue(probe.assess_first_login(record, self.profile))


if __name__ == "__main__":
    unittest.main()
