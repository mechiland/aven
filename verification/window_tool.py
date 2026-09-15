#!/usr/bin/env python3
"""Guest-side temporary KWin inventory/arrangement for matched screenshots.

Inventory is read-only. Arrange acts only on one explicitly matched ordinary
window. No KWin settings, window rules, global shortcuts or persistent scripts
are installed. Wayland windows can asynchronously acknowledge size changes;
the tool reports the observed final frame as well as the request.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid

SCRIPT = Path(__file__).with_name("kwin_windows.js")
INTERFACE = """<node><interface name="org.aven.Verification">
<method name="Report"><arg name="json" type="s" direction="in"/></method>
</interface></node>"""


def run_script(request):
    # Fedora's stock python3-gobject provides a private callback endpoint. This
    # avoids parsing journal text or enabling KWin debug logging for inventory.
    from gi.repository import Gio, GLib

    dbus = shutil.which("qdbus-qt6") or shutil.which("qdbus6") or shutil.which("qdbus")
    if not dbus:
        raise RuntimeError("qdbus-qt6 is required")
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    owner = connection.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "GetNameOwner", GLib.Variant("(s)", ("org.kde.KWin",)), GLib.VariantType.new("(s)"), Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
    loop, reply = GLib.MainLoop(), {}
    def receive(conn, sender, object_path, interface_name, method_name, parameters, invocation):
        if sender != owner:
            invocation.return_dbus_error("org.aven.Verification.WrongSender", "Only this session's KWin may report")
            return
        try:
            reply["result"] = json.loads(parameters.unpack()[0])
            invocation.return_value(GLib.Variant("()", ()))
        except (ValueError, TypeError) as error:
            reply["error"] = str(error)
            invocation.return_dbus_error("org.aven.Verification.InvalidJSON", str(error))
        loop.quit()
    registration = connection.register_object("/org/aven/Verification", Gio.DBusNodeInfo.new_for_xml(INTERFACE).interfaces[0], receive, None, None)
    plugin = "aven-verification-" + uuid.uuid4().hex
    process, loaded, timeout_source = None, False, None
    def call(*args):
        return subprocess.run([dbus, "org.kde.KWin", *args], capture_output=True, text=True, check=True, timeout=5).stdout.strip()
    try:
        with tempfile.TemporaryDirectory(prefix="aven-kwin-verification-") as directory:
            file = Path(directory) / "main.js"
            file.write_text("const request = " + json.dumps(request, ensure_ascii=False) + ";\nconst receiver = " + json.dumps(connection.get_unique_name()) + ";\n" + SCRIPT.read_text(), encoding="utf-8")
            identifier = int(call("/Scripting", "org.kde.kwin.Scripting.loadScript", str(file), plugin))
            if identifier < 0:
                raise RuntimeError("KWin refused temporary script")
            loaded = True
            process = subprocess.Popen([dbus, "org.kde.KWin", f"/Scripting/Script{identifier}", "org.kde.kwin.Script.run"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            def timeout():
                reply["error"] = "KWin did not return inventory within 10 seconds"
                loop.quit()
                return GLib.SOURCE_REMOVE
            timeout_source = GLib.timeout_add_seconds(10, timeout)
            loop.run()
            out, err = process.communicate(timeout=3)
            if process.returncode:
                raise RuntimeError(f"KWin script failed: {err.strip() or out.strip()}")
            if "error" in reply:
                raise RuntimeError(reply["error"])
            result = reply.get("result")
            if not isinstance(result, dict):
                raise RuntimeError("KWin returned no JSON result")
            return result
    finally:
        if process and process.poll() is None:
            process.terminate()
            process.communicate(timeout=3)
        if loaded:
            call("/Scripting", "org.kde.kwin.Scripting.unloadScript", plugin)
        if timeout_source and "error" not in reply:
            GLib.source_remove(timeout_source)
        connection.unregister_object(registration)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inventory = sub.add_parser("inventory", help="Read existing windows without changing UI")
    arrange = sub.add_parser("arrange", help="Arrange exactly one existing matched window")
    for command in [inventory, arrange]:
        command.add_argument("--id", help="Exact KWin internal window UUID")
        command.add_argument("--app", help="Exact desktop file name, resource class, or resource name")
        command.add_argument("--caption", help="Literal substring in the current title; combined with other selectors")
    inventory.add_argument("--include-special", action="store_true", help="Also report desktop/panel/other special windows")
    mode = arrange.add_mutually_exclusive_group()
    mode.add_argument("--geometry", nargs=4, type=int, metavar=("X", "Y", "WIDTH", "HEIGHT"), help="Outer frame in logical pixels, including titlebar")
    mode.add_argument("--maximize", action="store_true")
    arrange.add_argument("--activate", action="store_true", help="Unminimize and focus the matched window")
    arrange.add_argument("--settle-ms", type=int, default=600)
    args = parser.parse_args()
    if not Path("/run/ostree-booted").exists() or os.getuid() == 0:
        parser.error("Run as the desktop user inside the intended Atomic guest")
    request = {"command": args.command, "id": args.id, "app": args.app, "caption": args.caption,
               "include_special": getattr(args, "include_special", False)}
    if args.command == "arrange":
        if not any([args.id, args.app, args.caption]):
            parser.error("Arrangement requires an explicit --id, --app or --caption")
        if not any([args.geometry, args.maximize, args.activate]):
            parser.error("Specify --geometry, --maximize or --activate")
        if not 0 <= args.settle_ms <= 3000:
            parser.error("--settle-ms must be between 0 and 3000")
        if args.geometry and (args.geometry[2] < 1 or args.geometry[3] < 1):
            parser.error("Width and height must be positive")
        request.update(geometry=dict(zip(["x", "y", "width", "height"], args.geometry)) if args.geometry else None,
                       maximize=args.maximize, activate=args.activate)
    try:
        result = run_script(request)
        if args.command == "arrange" and result.get("ok"):
            time.sleep(args.settle_ms / 1000)
            final = run_script({"command": "inventory", "id": result["before"]["id"]})
            result["after"] = final.get("windows", [])
            if len(result["after"]) != 1:
                result.update(ok=False, error="Selected window disappeared before final verification")
            else:
                if args.geometry:
                    actual = result["after"][0]["frame"]
                    result["geometry_acknowledged"] = all(abs(actual[key] - value) <= 1 for key, value in request["geometry"].items())
                    if not result["geometry_acknowledged"]:
                        result.update(ok=False, error="Application did not acknowledge the requested frame; inspect reported actual geometry")
                if args.activate:
                    result["activation_acknowledged"] = result["after"][0]["active"] is True
                    if not result["activation_acknowledged"]:
                        result.update(ok=False, error="Requested activation was not acknowledged; inspect current focus")
        result.update(schema_version=1, captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      method="temporary KWin script via public Workspace/Window API", command=args.command,
                      persistent_kwin_changes=False)
    except (OSError, ValueError, RuntimeError, ImportError, subprocess.SubprocessError) as error:
        result = {"ok": False, "error": str(error), "command": args.command}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
