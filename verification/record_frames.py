#!/usr/bin/env python3
"""Record timestamped, lossless QEMU RFB frames without injecting UI input.

This samples the VM display; it cannot measure physical compositor frame pacing.
The integrator operates the real guest while this short read-only capture runs.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import time

from rfb_capture import METHOD, capture, png_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guest", choices=["stock", "aven"], required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=8)
    parser.add_argument("--fps", type=float, default=10)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 20 or not 1 <= args.fps <= 15:
        parser.error("Use 1–20 seconds and 1–15 requested fps")
    if args.output_dir.exists():
        parser.error("Use a fresh output directory; recordings are never overwritten")
    args.output_dir.mkdir(parents=True)
    start = time.monotonic()
    report = {"schema_version": 1, "guest": args.guest, "method": METHOD,
              "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "requested_seconds": args.seconds, "requested_fps": args.fps, "frames": [],
              "limitations": ["RFB readback and PNG encoding can skip compositor frames.", "Timestamps describe capture completion on the host, not display presentation.", "Replay this sequence to assess observed transitions; no physical frame-pacing claim is supported."]}
    try:
        while time.monotonic() - start < args.seconds:
            index = len(report["frames"])
            frame_started = time.monotonic()
            rgb, meta = capture(5920 if args.guest == "stock" else 5921, timeout=10)
            offset = time.monotonic() - start
            encoded = png_bytes(meta["width"], meta["height"], rgb, compression=1)
            frame_path = args.output_dir / f"frame-{index:04}.png"
            frame_path.write_bytes(encoded)
            report["frames"].append({"file": frame_path.name, "offset_seconds": offset,
                "capture_seconds": time.monotonic() - frame_started,
                "sha256": hashlib.sha256(encoded).hexdigest(), "transport": meta})
            # No single blocking wait exceeds one second.
            delay = 1 / args.fps - (time.monotonic() - frame_started)
            if delay > 0:
                time.sleep(delay)
    except (OSError, RuntimeError, ValueError) as error:
        report["error"] = str(error)
    report["elapsed_seconds"] = time.monotonic() - start
    report["observed_fps"] = len(report["frames"]) / report["elapsed_seconds"]
    gaps = [b["offset_seconds"] - a["offset_seconds"] for a, b in zip(report["frames"], report["frames"][1:])]
    report["largest_gap_seconds"] = max(gaps, default=None)
    report["complete"] = "error" not in report
    (args.output_dir / "recording.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    # ffmpeg concat can replay actual host sampling intervals without inventing
    # intermediate frames. Original PNGs remain the authoritative evidence.
    lines = ["ffconcat version 1.0"]
    for index, frame in enumerate(report["frames"]):
        lines.append(f"file {frame['file']}")
        duration = gaps[index] if index < len(gaps) else 1 / args.fps
        lines.append(f"duration {duration:.6f}")
    if report["frames"]:
        lines.append(f"file {report['frames'][-1]['file']}")
    (args.output_dir / "replay.ffconcat").write_text("\n".join(lines) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "frames"}, indent=2))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
