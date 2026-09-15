#!/usr/bin/env python3
"""Validate a critic's evidence manifest. Never invent or calculate visual scores.

Overall is the mean of nine explicitly assigned scores. Hashes check integrity,
not authenticity: the critic must actually inspect the referenced framebuffers.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path
import struct
import sys
import zlib

from rfb_capture import METHOD as RFB_METHOD

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {
    "chinese_typography": {"typography_sc", "typography_tc", "qt_sc", "qt_tc"},
    "latin_typography": {"typography_latin", "files_home", "browser_web"},
    "files_experience": {"files_home", "files_list", "files_grid", "files_mixed"},
    "file_preview": {"preview_image", "preview_pdf", "preview_text", "preview_media"},
    "browser_coherence": {"browser_web", "browser_sc", "browser_tc"},
    "mail_coherence": {"mail_list", "mail_sc", "mail_tc", "mail_compose"},
    "photo_experience": {"photos_grid", "photo_landscape", "photo_exif", "photo_alpha"},
    "visual_coherence": {"desktop", "files_home", "browser_web", "mail_list", "photos_grid"},
    "perceived_polish": {"desktop", "files_mixed", "preview_image", "mail_compose"},
}
SCALES = {1, 1.25, 1.5, 2}
OPERATIONS = {"folders", "breadcrumbs", "sidebar", "grid_list", "selection", "copy", "move", "rename", "trash", "restore", "default_open", "preview_toggle", "preview_escape_focus", "browser_download", "browser_file_picker", "mail_draft_save", "photo_next_previous"}
MOTION = {"window_open_close", "window_switch", "menus_popovers", "preview", "photo_transition", "overview"}


def template():
    return {"schema_version": 1, "round": 1, "critic": {"name": None, "independent": True, "inspected_at": None},
            "pairs": [], "scores": {name: {"score": None, "pairs": [], "rationale": None, "limitations": []} for name in CATEGORIES},
            "three_second": {"answer": None, "pairs": [], "rationale": None}, "operations": [], "motion": [],
            "declared_overall": None, "pass": False}


def date(value):
    if not isinstance(value, str):
        raise ValueError("missing timestamp")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp needs timezone")
    return parsed


def png_size(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG framebuffer")
    offset, size, image_data, ended = 8, None, [], False
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        chunk = data[offset + 8:offset + 8 + length]
        crc = data[offset + 8 + length:offset + 12 + length]
        if len(crc) != 4 or (zlib.crc32(kind + chunk) & 0xffffffff) != struct.unpack(">I", crc)[0]:
            raise ValueError("PNG chunk checksum mismatch")
        if kind == b"IHDR":
            size = struct.unpack(">II", chunk[:8])
        if kind == b"IDAT":
            image_data.append(chunk)
        if kind == b"IEND":
            ended = True
            break
        offset += length + 12
    if not ended or not size or not all(size) or not image_data:
        raise ValueError("incomplete PNG framebuffer")
    if not zlib.decompress(b"".join(image_data)):
        raise ValueError("empty PNG image data")
    return size


def observed_scale(commands, declared):
    """Use surface DPR on Wayland; never accept rounded QScreen DPR as fractional."""
    qt = commands.get("qt", {})
    data = qt.get("json", {})
    screens = data.get("screens", [])
    if qt.get("exit_code") != 0 or data.get("platform") != "wayland" or len(screens) != 1:
        raise ValueError("successful one-screen native Wayland Qt probe required")
    display = commands.get("display_json")
    if display is not None:
        if display.get("exit_code") != 0:
            raise ValueError("KScreen JSON probe failed")
        outputs = [o for o in display.get("json", {}).get("outputs", [])
                   if o.get("enabled") is True and o.get("connected") is True]
        if len(outputs) != 1:
            raise ValueError("one enabled connected KScreen output required")
        compositor = outputs[0].get("scale")
        output_name = outputs[0].get("name")
    else:
        # Preserve original capture-time evidence at integer scales. Do not
        # invent a new runtime probe or rewrite existing sidecar metadata.
        old = commands.get("display", {})
        clean = re.sub(r"\x1b\[[0-9;]*m", "", old.get("stdout", ""))
        scales = re.findall(r"^\s*Scale:\s*([0-9.]+)\s*$", clean, re.M)
        outputs = re.findall(r"^Output:\s*\d+\s+(\S+)", clean, re.M)
        if old.get("exit_code") != 0 or len(scales) != 1 or len(outputs) != 1 or not re.search(r"^\s*enabled\s*$", clean, re.M) or not re.search(r"^\s*connected\s*$", clean, re.M):
            raise ValueError("missing capture-time KScreen scale evidence")
        compositor, output_name = float(scales[0]), outputs[0]
    if type(declared) not in [int, float] or not math.isfinite(declared) or declared not in SCALES:
        raise ValueError("invalid declared scale")
    if type(compositor) not in [int, float] or compositor != declared:
        raise ValueError("KScreen scale differs from declared scale")
    window = data.get("window")
    measurement = data.get("scale_measurement")
    if window is not None:
        if display is None:
            raise ValueError("mapped window probe requires structured compositor agreement")
        submitted = window.get("frames_submitted")
        if window.get("visible") is not True or window.get("exposed_once") is not True or type(submitted) is not int or submitted < 1:
            raise ValueError("Qt scale probe did not map and submit a real surface")
        focus = qt.get("focus", {})
        if focus.get("restored") is not True or "before" not in focus or "after" not in focus or focus["before"] != focus["after"] or focus.get("activation_requests_sent") != 0:
            raise ValueError("original KWin focus was not verified after Qt probe exit")
        if window.get("screen") != output_name:
            raise ValueError("Qt surface and KScreen output differ")
        scale = window.get("scale")
        source = "mapped QWindow DPR with KScreen agreement"
        if measurement is not None and (measurement.get("method") != source or measurement.get("scale") != scale or measurement.get("surface_mapped") is not True):
            raise ValueError("mapped surface measurement metadata is inconsistent")
    else:
        scale = screens[0].get("scale")
        if declared not in [1, 2]:
            raise ValueError("fractional scale requires mapped QWindow DPR; QScreen alone is rounded")
        if measurement is not None:
            source = "integer QScreen DPR with KScreen agreement"
            if display is None or measurement.get("method") != source or measurement.get("scale") != scale or measurement.get("surface_mapped") is not False:
                raise ValueError("integer no-window measurement metadata is inconsistent")
        else:
            source = "legacy integer QScreen DPR with capture-time KScreen agreement"
    if type(scale) not in [int, float] or scale != declared:
        raise ValueError("actual Qt surface scale differs from declared scale")
    return scale, source


def validate(manifest, root=ROOT):
    errors, warnings, pairs, scores = [], [], {}, []
    root = root.resolve()

    def require(condition, message):
        if not condition:
            errors.append(message)
        return condition

    def path(value):
        if not isinstance(value, str) or not value:
            raise ValueError("missing repository-relative evidence path")
        candidate = (root / value).resolve()
        if Path(value).is_absolute() or not candidate.is_relative_to(root):
            raise ValueError("evidence path must remain within repository")
        if not candidate.is_file():
            raise ValueError(f"missing evidence: {value}")
        return candidate

    def refs(record, label):
        result = record.get("pairs", [])
        require(bool(result) and isinstance(result, list), f"{label}: cite inspected pairs")
        for ref in result:
            require(ref in pairs, f"{label}: unknown pair {ref}")
        return [pairs[ref] for ref in result if ref in pairs]

    require(manifest.get("schema_version") == 1, "schema_version must be 1")
    require(type(manifest.get("round")) is int and manifest["round"] > 0, "round must be a positive integer")
    critic = manifest.get("critic", {})
    require(bool(critic.get("name")), "critic identity missing")
    require(critic.get("independent") is True, "critic must be independent of integration")
    try:
        inspected_at = date(critic.get("inspected_at"))
    except ValueError as error:
        inspected_at = None
        errors.append(f"critic: {error}")
    all_captures = set()
    for pair in manifest.get("pairs", []):
        identifier = pair.get("id")
        require(bool(identifier) and identifier not in pairs, f"pair id missing or duplicated: {identifier}")
        if not identifier or identifier in pairs:
            continue
        pairs[identifier] = pair
        require(bool(pair.get("content_id")), f"{identifier}: matched content_id required")
        require(bool(pair.get("tags")), f"{identifier}: scene tags required")
        inspection = pair.get("inspection", {})
        require(inspection.get("by") == critic.get("name") and bool(inspection.get("notes")), f"{identifier}: explicit critic inspection and notes required")
        dimensions, scales, versions, package_sets, font_sets = [], [], [], [], []
        for guest in ["stock", "aven"]:
            label = f"{identifier}/{guest}"
            try:
                sidecar_path = path(pair.get(guest))
                sidecar = json.loads(sidecar_path.read_text())
                require(sidecar.get("guest") == guest, f"{label}: wrong guest provenance")
                if guest == "aven":
                    require(sidecar.get("round") == manifest.get("round"), f"{label}: capture belongs to another Aven round")
                require(sidecar.get("method") in ["QEMU QMP screendump; unmodified guest framebuffer", RFB_METHOD], f"{label}: requires unmodified QEMU framebuffer capture")
                if sidecar.get("method") == RFB_METHOD:
                    transport = sidecar.get("framebuffer_transport", {})
                    require(transport.get("rfb_version") == "RFB 003.008" and transport.get("input_events_sent") == 0, f"{label}: missing read-only raw RFB provenance")
                    require(transport.get("endpoint") == f"127.0.0.1:{5920 if guest == 'stock' else 5921}", f"{label}: wrong QEMU VNC endpoint")
                require(sidecar.get("guest_probe_exit_code") == 0, f"{label}: failed capture-time guest probe")
                captured_at = date(sidecar.get("captured_at"))
                if inspected_at:
                    require(inspected_at >= captured_at, f"{label}: inspection predates capture")
                png = path(sidecar.get("image"))
                require(png not in all_captures, f"{label}: screenshot reused across pairs; combine tags on one pair")
                all_captures.add(png)
                sha = hashlib.sha256(png.read_bytes()).hexdigest()
                require(sha == sidecar.get("sha256"), f"{label}: screenshot hash mismatch")
                require(sha == inspection.get(guest + "_sha256"), f"{label}: critic did not attest this exact screenshot hash")
                dimensions.append(png_size(png))
                if sidecar.get("method") == RFB_METHOD:
                    require(dimensions[-1] == (transport.get("width"), transport.get("height")), f"{label}: RFB and PNG dimensions differ")
                runtime = sidecar.get("runtime_probe")
                if not isinstance(runtime, dict):
                    runtime = json.loads(path(pair.get(guest + "_probe")).read_text())
                require(runtime.get("guest") == guest and runtime.get("ostree_booted") is True, f"{label}: runtime must be actual Atomic guest")
                require(abs((date(runtime.get("captured_at")) - captured_at).total_seconds()) <= 120, f"{label}: runtime probe more than 120 seconds from capture")
                commands = runtime.get("commands", {})
                packages = commands.get("packages", {})
                fonts = commands.get("font_packages", {})
                require(packages.get("exit_code") == 0, f"{label}: missing native app/runtime package")
                require(fonts.get("exit_code") == 0, f"{label}: font package query failed")
                package_sets.append(sorted(packages.get("stdout", "").splitlines()))
                font_sets.append(sorted(fonts.get("stdout", "").splitlines()))
                scale, scale_source = observed_scale(commands, sidecar.get("declared_scale"))
                if scale_source.startswith("legacy"):
                    warnings.append(f"{label}: {scale_source}; no mapped surface in original probe")
                scales.append(scale)
                atomic = commands.get("atomic", {})
                deployments = atomic.get("json", {}).get("deployments", [])
                booted = [d for d in deployments if d.get("booted") is True]
                require(atomic.get("exit_code") == 0 and len(booted) == 1, f"{label}: missing booted OSTree deployment")
                if booted:
                    versions.append(booted[0].get("base-checksum", booted[0].get("checksum")))
            except (OSError, ValueError, TypeError, KeyError, struct.error, zlib.error) as error:
                errors.append(f"{label}: {error}")
        require(len(dimensions) == 2 and dimensions[0] == dimensions[1], f"{identifier}: paired framebuffer dimensions must match")
        require(len(scales) == 2 and scales[0] == scales[1], f"{identifier}: paired display scales must match")
        require(len(versions) == 2 and versions[0] and versions[0] == versions[1], f"{identifier}: stock/Aven booted base OSTree commits differ or missing")
        require(len(package_sets) == 2 and package_sets[0] and package_sets[0] == package_sets[1], f"{identifier}: paired native app/runtime packages differ or missing")
        require(len(font_sets) == 2 and font_sets[0] and font_sets[0] == font_sets[1], f"{identifier}: fonts must be available equally in stock and Aven")
        pair["_verified_scale"] = scales[0] if len(scales) == 2 and scales[0] == scales[1] else None

    for category, needed in CATEGORIES.items():
        record = manifest.get("scores", {}).get(category, {})
        value = record.get("score")
        numeric = type(value) in [int, float] and math.isfinite(value) and 0 <= value <= 10
        require(numeric, f"{category}: score pending or invalid (0–10)")
        if numeric:
            scores.append(value)
        require(bool(record.get("rationale")), f"{category}: critic rationale required")
        cited = refs(record, category)
        tags = set().union(*(set(p.get("tags", [])) for p in cited)) if cited else set()
        require(needed <= tags, f"{category}: missing paired coverage {sorted(needed - tags)}")
        if category == "chinese_typography":
            for tag in needed:
                covered = {p.get("_verified_scale") for p in cited if tag in p.get("tags", [])}
                require(SCALES <= covered, f"Chinese {tag}: missing actual paired scales {sorted(SCALES - covered)}")
    three = manifest.get("three_second", {})
    require(three.get("answer") is True, "three-second differentiation judgment must be affirmative")
    require(bool(three.get("rationale")), "three-second judgment needs an explanation")
    require(any("desktop" in p.get("tags", []) for p in refs(three, "three_second")), "three-second judgment must cite paired desktops")

    observed_operations = set()
    for operation in manifest.get("operations", []):
        name = operation.get("id")
        observed_operations.add(name)
        require(operation.get("passed") is True and bool(operation.get("observation")), f"operation {name}: missing passing witnessed observation")
        require(operation.get("method") == "native-ui", f"operation {name}: requires native application UI, not shell simulation")
        refs(operation, f"operation {name}")
        if name in {"copy", "move", "rename", "trash", "restore"}:
            for guest in ["stock", "aven"]:
                try:
                    result = json.loads(path(operation.get(guest + "_check")).read_text())
                    expected_stage = {"copy": "copied", "move": "moved", "rename": "renamed", "trash": "trashed", "restore": "restored"}[name]
                    require(result.get("passed") is True and result.get("stage") == expected_stage and bool(result.get("checks")) and all(c.get("passed") is True for c in result["checks"]), f"{name}/{guest}: byte verification did not pass")
                except (OSError, ValueError, TypeError, KeyError) as error:
                    errors.append(f"operation {name}/{guest}: {error}")
    require(OPERATIONS <= observed_operations, f"missing witnessed operations: {sorted(OPERATIONS - observed_operations)}")
    observed_motion = set()
    for motion in manifest.get("motion", []):
        name = motion.get("id")
        observed_motion.add(name)
        require(motion.get("passed") is True and bool(motion.get("observation")), f"motion {name}: pending or failed")
        require(motion.get("method") in ["live-observation", "recording"], f"motion {name}: static screenshots cannot prove motion")
        require(motion.get("observer") == critic.get("name"), f"motion {name}: critic observation required")
        refs(motion, f"motion {name}")
        if motion.get("method") == "recording":
            for guest in ["stock", "aven"]:
                try:
                    recording = path(motion.get(guest + "_recording"))
                    require(hashlib.sha256(recording.read_bytes()).hexdigest() == motion.get(guest + "_sha256"), f"motion {name}/{guest}: recording hash mismatch")
                except (OSError, ValueError) as error:
                    errors.append(f"motion {name}/{guest}: {error}")
    require(MOTION <= observed_motion, f"missing observed motion: {sorted(MOTION - observed_motion)}")
    overall = sum(scores) / len(CATEGORIES) if len(scores) == len(CATEGORIES) else None
    require(overall is not None and overall >= 8, "overall must be the mean of all nine scores and >=8")
    chinese = manifest.get("scores", {}).get("chinese_typography", {}).get("score")
    require(type(chinese) in [int, float] and math.isfinite(chinese) and chinese >= 8.5, "Chinese typography must be >=8.5")
    if manifest.get("declared_overall") is not None:
        require(overall is not None and type(manifest["declared_overall"]) in [int, float] and math.isclose(manifest["declared_overall"], overall, abs_tol=.00001), "declared_overall differs from nine-score mean")
    return {"schema_version": 1, "round": manifest.get("round"), "pass": not errors, "overall": overall, "errors": errors, "warnings": warnings,
            "limitations": ["Integrity and completeness checks do not authenticate a screenshot or substitute for honest visual inspection."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path)
    parser.add_argument("--template", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.template:
        print(json.dumps(template(), indent=2))
        return 0
    if not args.manifest:
        parser.error("provide a critic manifest or --template")
    try:
        result = validate(json.loads(args.manifest.read_text()), args.root)
    except (OSError, ValueError, TypeError, AttributeError) as error:
        result = {"pass": False, "overall": None, "errors": [f"invalid manifest: {error}"]}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
