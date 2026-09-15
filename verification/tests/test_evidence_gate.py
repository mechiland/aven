"""Adversarial completeness/integrity tests; synthetic PNGs stay in temp dirs."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence_gate import CATEGORIES, MOTION, OPERATIONS, SCALES, template, validate
from file_operations import prepare, verify
from rfb_capture import METHOD as RFB_METHOD


def write_json(path, data):
    path.write_text(json.dumps(data))


def fake_png():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\x00\x12\x34\x56")) + chunk(b"IEND", b"")


class GateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aven-gate-test-not-evidence-")
        self.root = Path(self.temp.name)
        self.manifest = template()
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        self.manifest["critic"] = {"name": "unit-test-only", "independent": True, "inspected_at": now}
        tags = sorted(set().union(*CATEGORIES.values()))
        for index, scale in enumerate(sorted(SCALES)):
            pair = {"id": f"pair-{index}", "content_id": "test-only", "tags": tags,
                    "inspection": {"by": "unit-test-only", "notes": "Synthetic unit-test fixture, never a visual assessment"}}
            for guest in ["stock", "aven"]:
                png = self.root / f"{guest}-{index}.png"
                png.write_bytes(fake_png())
                sha = hashlib.sha256(png.read_bytes()).hexdigest()
                pair["inspection"][guest + "_sha256"] = sha
                pair[guest] = f"{guest}-{index}.json"
                write_json(self.root / pair[guest], {
                    "guest": guest, "round": 0 if guest == "stock" else 1, "method": "QEMU QMP screendump; unmodified guest framebuffer", "guest_probe_exit_code": 0,
                    "captured_at": now, "image": png.name, "sha256": sha, "declared_scale": scale,
                    "runtime_probe": {"guest": guest, "ostree_booted": True, "captured_at": now, "commands": {
                        "qt": {"exit_code": 0, "focus": {"before": "fixture-window", "after": "fixture-window", "restored": True, "activation_requests_sent": 0}, "json": {"platform": "wayland", "screens": [{"scale": 1 if scale == 1 else 2}],
                            "window": {"scale": scale, "visible": True, "exposed_once": True, "frames_submitted": 1, "active": False, "screen": "Virtual-1"}}},
                        "display_json": {"exit_code": 0, "json": {"outputs": [{"enabled": True, "connected": True, "name": "Virtual-1", "scale": scale}]}},
                        "display": {"exit_code": 0, "stdout": f"Output: 1 Virtual-1\n\tenabled\n\tconnected\n\tScale: {scale}\n"},
                        "packages": {"exit_code": 0, "stdout": "test-native-package-v1\n"},
                        "font_packages": {"exit_code": 0, "stdout": "test-noto-v1\n"},
                        "atomic": {"exit_code": 0, "json": {"deployments": [{"booted": True, "checksum": "base"}]}}}}})
            self.manifest["pairs"].append(pair)
        for record in self.manifest["scores"].values():
            record.update(score=8.5, pairs=[p["id"] for p in self.manifest["pairs"]], rationale="Fixture covers gate branches only")
        self.manifest["three_second"] = {"answer": True, "pairs": ["pair-0"], "rationale": "Synthetic test assertion"}
        for name in OPERATIONS:
            item = {"id": name, "passed": True, "method": "native-ui", "observation": "test only", "pairs": ["pair-0"]}
            if name in ["copy", "move", "rename", "trash", "restore"]:
                stage = {"copy": "copied", "move": "moved", "rename": "renamed", "trash": "trashed", "restore": "restored"}[name]
                for guest in ["stock", "aven"]:
                    item[guest + "_check"] = f"{name}-{guest}.json"
                    write_json(self.root / item[guest + "_check"], {"stage": stage, "passed": True, "checks": [{"passed": True}]})
            self.manifest["operations"].append(item)
        self.manifest["motion"] = [{"id": name, "passed": True, "method": "live-observation", "observer": "unit-test-only", "observation": "test only", "pairs": ["pair-0"]} for name in MOTION]

    def tearDown(self):
        self.temp.cleanup()

    def result(self):
        return validate(copy.deepcopy(self.manifest), self.root)

    def change_sidecar(self, name, callback):
        path = self.root / name
        data = json.loads(path.read_text())
        callback(data)
        write_json(path, data)

    def test_complete_gate_contract(self):
        result = self.result()
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["overall"], 8.5)

    def test_missing_or_boolean_score_never_passes(self):
        for value in [None, True, float("nan"), float("inf"), -1, 11]:
            self.manifest["scores"]["files_experience"]["score"] = value
            self.assertFalse(self.result()["pass"])

    def test_chinese_threshold_is_independent_of_overall(self):
        self.manifest["scores"]["chinese_typography"]["score"] = 8
        self.assertGreater(self.result()["overall"], 8)
        self.assertFalse(self.result()["pass"])

    def test_false_three_second_judgment_never_passes(self):
        self.manifest["three_second"]["answer"] = False
        self.assertFalse(self.result()["pass"])

    def test_image_tampering_rejected(self):
        (self.root / "aven-0.png").write_bytes(b"invalid")
        self.assertFalse(self.result()["pass"])

    def test_uninspected_exact_hash_rejected(self):
        del self.manifest["pairs"][0]["inspection"]["aven_sha256"]
        self.assertFalse(self.result()["pass"])

    def test_actual_scale_mismatch_rejected(self):
        self.change_sidecar("aven-0.json", lambda s: s["runtime_probe"]["commands"]["qt"]["json"]["window"].update(scale=2))
        self.assertFalse(self.result()["pass"])

    def test_fractional_surface_accepts_rounded_qscreen(self):
        result = self.result()  # 1.25 and 1.5 windows both have QScreen DPR 2
        self.assertTrue(result["pass"], result["errors"])

    def test_fractional_qscreen_alone_rejected(self):
        self.change_sidecar("aven-1.json", lambda s: s["runtime_probe"]["commands"]["qt"]["json"].pop("window"))
        self.assertFalse(self.result()["pass"])

    def test_compositor_disagreement_rejected(self):
        self.change_sidecar("aven-1.json", lambda s: s["runtime_probe"]["commands"]["display_json"]["json"]["outputs"][0].update(scale=1.5))
        self.assertFalse(self.result()["pass"])

    def test_unmapped_surface_rejected(self):
        for invalid in [{"frames_submitted": 0}, {"exposed_once": False}, {"visible": False}]:
            self.change_sidecar("aven-1.json", lambda s: s["runtime_probe"]["commands"]["qt"]["json"]["window"].update(invalid))
            self.assertFalse(self.result()["pass"])

    def test_focus_must_return_without_activation_request(self):
        self.change_sidecar("aven-1.json", lambda s: s["runtime_probe"]["commands"]["qt"]["focus"].update(after="wrong-window"))
        self.assertFalse(self.result()["pass"])

    def test_legacy_integer_capture_requires_recorded_compositor(self):
        def legacy(s):
            commands = s["runtime_probe"]["commands"]
            commands["qt"]["json"].pop("window")
            commands.pop("display_json")
        self.change_sidecar("stock-0.json", legacy)
        result = self.result()
        self.assertTrue(result["pass"], result["errors"])
        self.assertTrue(any("legacy integer" in w for w in result["warnings"]))
        self.change_sidecar("stock-0.json", lambda s: s["runtime_probe"]["commands"].pop("display"))
        self.assertFalse(self.result()["pass"])

    def test_explicit_integer_measurement_needs_no_window_or_focus_probe(self):
        def integer(s):
            qt = s["runtime_probe"]["commands"]["qt"]
            qt.pop("focus")
            qt["json"]["window"] = None
            qt["json"]["scale_measurement"] = {"method": "integer QScreen DPR with KScreen agreement", "scale": 1, "surface_mapped": False}
        self.change_sidecar("aven-0.json", integer)
        result = self.result()
        self.assertTrue(result["pass"], result["errors"])
        self.assertFalse(result["warnings"])

    def test_integer_no_window_claim_cannot_substitute_for_fractional_surface(self):
        def false_integer(s):
            qt = s["runtime_probe"]["commands"]["qt"]["json"]
            qt["window"] = None
            qt["scale_measurement"] = {"method": "integer QScreen DPR with KScreen agreement", "scale": 1.25, "surface_mapped": False}
        self.change_sidecar("aven-1.json", false_integer)
        self.assertFalse(self.result()["pass"])

    def test_missing_chinese_qt_coverage_rejected(self):
        self.manifest["pairs"][0]["tags"].remove("qt_tc")
        self.assertFalse(self.result()["pass"])

    def test_snapshot_provenance_missing_rejected(self):
        self.change_sidecar("stock-0.json", lambda s: s.update(method="offscreen fixture render"))
        self.assertFalse(self.result()["pass"])

    def test_base_commit_mismatch_rejected(self):
        self.change_sidecar("aven-0.json", lambda s: s["runtime_probe"]["commands"]["atomic"]["json"]["deployments"][0].update(checksum="different"))
        self.assertFalse(self.result()["pass"])

    def test_app_version_mismatch_rejected(self):
        self.change_sidecar("aven-0.json", lambda s: s["runtime_probe"]["commands"]["packages"].update(stdout="different-build\n"))
        self.assertFalse(self.result()["pass"])

    def test_missing_font_package_rejected(self):
        self.change_sidecar("aven-0.json", lambda s: s["runtime_probe"]["commands"]["font_packages"].update(stdout=""))
        self.assertFalse(self.result()["pass"])

    def test_wrong_aven_round_rejected(self):
        self.change_sidecar("aven-0.json", lambda s: s.update(round=2))
        self.assertFalse(self.result()["pass"])

    def test_rfb_framebuffer_transport_accepted(self):
        self.change_sidecar("aven-0.json", lambda s: s.update(method=RFB_METHOD, framebuffer_transport={"rfb_version": "RFB 003.008", "input_events_sent": 0, "endpoint": "127.0.0.1:5921", "width": 1, "height": 1}))
        result = self.result()
        self.assertTrue(result["pass"], result["errors"])

    def test_rfb_missing_transport_rejected(self):
        self.change_sidecar("aven-0.json", lambda s: s.update(method=RFB_METHOD))
        self.assertFalse(self.result()["pass"])

    def test_stale_runtime_probe_rejected(self):
        self.change_sidecar("aven-0.json", lambda s: s["runtime_probe"].update(captured_at="2020-01-01T00:00:00Z"))
        self.assertFalse(self.result()["pass"])

    def test_evidence_path_escape_rejected(self):
        self.manifest["pairs"][0]["stock"] = "../elsewhere.json"
        self.assertFalse(self.result()["pass"])

    def test_missing_motion_rejected(self):
        self.manifest["motion"] = []
        self.assertFalse(self.result()["pass"])

    def test_shell_operations_do_not_prove_dolphin(self):
        self.manifest["operations"][0]["method"] = "shell"
        self.assertFalse(self.result()["pass"])

    def test_mean_cannot_be_selectively_weighted(self):
        self.manifest["declared_overall"] = 9
        self.assertFalse(self.result()["pass"])


class ByteCheckTest(unittest.TestCase):
    def test_preservation_and_correct_stage(self):
        with tempfile.TemporaryDirectory(prefix="aven-ops-test-") as temporary:
            root = Path(temporary)
            source = root / "source.txt"
            source.write_text("简体中文 / 繁體中文\n")
            work = root / "fixture"
            result = prepare(work, source)
            name = result["fixture"]["name"]
            copied = work / "02 复制" / name
            self.assertFalse(verify(work, "copied")["passed"])
            copied.write_bytes(source.read_bytes())
            report = verify(work, "copied")
            self.assertTrue(report["passed"])
            self.assertFalse(report["ui_verified"])
            (work / "01 原件" / name).write_text("damaged")
            self.assertFalse(verify(work, "copied")["passed"])

    def test_existing_directory_is_not_adopted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.txt"
            source.write_text("test")
            with self.assertRaises(ValueError):
                prepare(root, source)


if __name__ == "__main__":
    unittest.main()
