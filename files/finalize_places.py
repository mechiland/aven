"""Finish native Places defaults after Plasma has initialized its bookmarks."""

import argparse
import json
import math
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

from places import PLACES_TARGET, configure_places
from system_places import discover_system_devices


def finalize_places(home, *, timeout=30, interval=0.5, discover=discover_system_devices,
                    monotonic=time.monotonic, sleep=time.sleep):
    """Wait for native XBEL and two complete, stable device inventories.

    Never initialize XBEL ourselves: KFilePlacesModel owns native bookmark
    creation. Existing explicit visibility flags remain configure_places' domain.
    The caller must not publish its completion marker if complete is false.
    """
    if not math.isfinite(timeout) or timeout <= 0 or not math.isfinite(interval) or interval <= 0:
        raise ValueError("timeout and interval must be positive finite seconds")
    home = Path(home)
    target = home / PLACES_TARGET
    deadline = monotonic() + timeout
    previous = None
    attempts = 0
    pending = "Waiting for native Places initialization"
    while monotonic() < deadline:
        attempts += 1
        if target.is_symlink():
            raise ValueError("Refusing to replace a symlinked Places file")
        if not target.exists():
            previous = None
            pending = "Waiting for native Places initialization"
        else:
            try:
                native = ET.parse(target).getroot()
                if native.tag != "xbel" or not native.findall("bookmark"):
                    raise ET.ParseError("Waiting for a native XBEL bookmark list")
                remaining = deadline - monotonic()
                if remaining <= 0:
                    break
                devices = discover(require_ready=True, timeout=min(10, remaining))
                signature = json.dumps(sorted(devices, key=lambda item: item["udi"]), sort_keys=True)
            except (FileNotFoundError, ET.ParseError, OSError, ValueError, RuntimeError,
                    subprocess.SubprocessError) as error:
                previous = None
                pending = str(error)
            else:
                if signature == previous and monotonic() < deadline:
                    # configure_places rereads current native bytes and refuses
                    # concurrent writes; it never replaces explicit IsHidden.
                    try:
                        result = configure_places(home, system_devices=devices)
                    except (FileNotFoundError, ET.ParseError):
                        previous = None
                        pending = "Native Places changed during initialization"
                    else:
                        if "reason" not in result:
                            return {"complete": True, "device_inventory_ready": True,
                                    "attempts": attempts, "system_devices": devices, **result}
                        previous = None
                        pending = result["reason"]
                else:
                    previous = signature
                    pending = "Waiting for a second stable device inventory"
        remaining = deadline - monotonic()
        if remaining > 0:
            sleep(min(interval, remaining))
    return {"complete": False, "device_inventory_ready": False,
            "attempts": attempts, "reason": pending}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--timeout", type=float, default=30, help="Maximum readiness wait in seconds (default: 30)")
    args = parser.parse_args(argv)
    try:
        result = finalize_places(args.home, timeout=args.timeout)
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"complete": False, "reason": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["complete"] else 75


if __name__ == "__main__":
    raise SystemExit(main())
