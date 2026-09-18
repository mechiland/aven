#!/usr/bin/env python3
"""Seed an isolated Aven Firefox profile, never the user's normal profiles.

Run as the guest's aven user after the stock screenshots have been captured.
Only --refresh reapplies preferences to an already seeded profile.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MARKER = "aven-browser-profile-v1"


def atomic_write(path: Path, text: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as out:
        tmp = Path(out.name)
        out.write(text)
    tmp.chmod(mode)
    tmp.replace(path)


def preferences(roles: dict) -> dict:
    prefs = {
        # Keep upstream System theme, co-locating the native window controls
        # with Firefox's navigation toolbar using its supported CSD mode.
        "browser.theme.native-theme": True,
        "browser.tabs.inTitlebar": 1,
        "browser.uidensity": 1,
        "toolkit.legacyUserProfileCustomizations.stylesheets": True,
        # KDE's portal owns the Open / Save dialogs; no GTK file chooser fork.
        "widget.use-xdg-desktop-portal.file-picker": 1,
        # A quiet ordinary new tab page, retaining search and shortcuts.
        "browser.newtabpage.activity-stream.showSponsored": False,
        "browser.newtabpage.activity-stream.showSponsoredTopSites": False,
        "browser.newtabpage.activity-stream.feeds.section.topstories": False,
        "font.name.sans-serif.x-western": roles["ui"]["family"],
        "font.name.monospace.x-western": roles["monospace"]["family"],
    }
    for language in ("zh-CN", "zh-TW", "zh-HK"):
        prefs[f"font.name.sans-serif.{language}"] = roles["cjk"][language]
    # Deliberately retain document fonts, serif/monospace CJK fallbacks, browser
    # zoom, minimum font size, site line-height, UI locale and every protection.
    return prefs


def typography_css(roles: dict) -> str:
    family = json.dumps(roles["ui"]["family"], ensure_ascii=False)
    size = roles["ui"].get("pixel_size", roles["ui"]["point_size"] * 96 / 72)
    return ("/* Generated from typography/roles.json by browser/install.py. */\n"
            f":root {{ --union-ui-family: {family}; --union-ui-size: {size:g}px; }}\n")


def toolbar_preferences(original: str) -> dict:
    """Move real tab commands to navigation before a single tab row can hide."""
    key = "browser.uiCustomization.state"
    prefix = f"user_pref({json.dumps(key)}, "
    state = None
    for line in original.splitlines():
        if line.startswith(prefix):
            try:
                state = json.loads(json.loads(line[len(prefix):-2]))
            except (ValueError, TypeError):
                raise SystemExit("Cannot safely merge Firefox toolbar customization state")
    if state is None:
        # Firefox 155's native serialized toolbar schema, inspected in guest.
        state = {
            "placements": {
                "widget-overflow-fixed-list": [], "unified-extensions-area": [],
                "nav-bar": ["sidebar-button", "back-button", "forward-button", "stop-reload-button",
                            "customizableui-special-spring1", "urlbar-container", "customizableui-special-spring2",
                            "downloads-button", "fxa-toolbar-menu-button", "unified-extensions-button"],
                "toolbar-menubar": ["menubar-items"],
                "TabsToolbar": ["tabbrowser-tabs", "customizableui-special-spring3"],
                "vertical-tabs": [], "PersonalToolbar": ["personal-bookmarks"],
            },
            "seen": [], "dirtyAreaCache": [], "currentVersion": 26, "newElementCount": 3,
        }
    if not isinstance(state, dict) or not isinstance(state.get("placements"), dict):
        raise SystemExit("Unexpected Firefox toolbar customization schema")
    placements = state["placements"]
    for area, items in placements.items():
        if not isinstance(items, list):
            raise SystemExit("Unexpected Firefox toolbar placement schema")
        placements[area] = [item for item in items if item not in ("new-tab-button", "alltabs-button")]
    placements.setdefault("nav-bar", []).extend(["new-tab-button", "alltabs-button"])
    state["dirtyAreaCache"] = list(dict.fromkeys(state.get("dirtyAreaCache", []) + ["nav-bar", "TabsToolbar"]))
    return {key: json.dumps(state, separators=(",", ":"), ensure_ascii=False)}


def desktop_quote(value: str) -> str:
    # Desktop Entry Exec has different escaping rules from a POSIX shell.
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$").replace("%", "%%") + '"'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", required=True, type=Path, help="Explicit isolated guest user home")
    parser.add_argument("--refresh", action="store_true", help="Reapply Aven defaults; Firefox must be closed")
    parser.add_argument("--update", action="store_true", help="Update chrome assets while retaining all existing preferences")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    if not home.is_dir():
        parser.error("--home must be an existing directory")
    if home.stat().st_uid != os.getuid():
        parser.error("Run as the owner of --home so the browser can write its profile")
    profile = home / ".local/share/aven/firefox"
    marker = profile / ".aven-profile"
    if profile.exists() and not marker.exists() and any(profile.iterdir()):
        parser.error(f"Refusing to adopt an existing unmarked profile: {profile}")
    if marker.exists() and marker.read_text().strip() != MARKER:
        parser.error("Unexpected profile marker")
    profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    profile.chmod(0o700)
    roles_path = ROOT / "typography/roles.json"
    tokens_path = ROOT / "visual/tokens.json"
    roles = json.loads(roles_path.read_text())
    tokens = json.loads(tokens_path.read_text())
    prefs = preferences(roles)
    pref_path = profile / "prefs.js"
    seed = not pref_path.exists() or args.refresh
    with (profile / ".parentlock").open("a+") as lock:
        try:
            fcntl.lockf(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("Close the Aven Firefox profile before installing preferences")
        if seed or args.update:
            # Chrome layout and typography only; website CSS is untouched.
            shutil.copytree(ROOT / "browser/chrome", profile / "chrome", dirs_exist_ok=True)
            atomic_write(profile / "chrome/union-typography.css", typography_css(roles))
        if seed:
            original = pref_path.read_text() if pref_path.exists() else ""
            prefs.update(toolbar_preferences(original))
            keys = "|".join(re.escape(json.dumps(key)) for key in prefs)
            managed_line = re.compile(r"^user_pref\((?:" + keys + r"),")
            retained = [line for line in original.splitlines() if not managed_line.match(line)]
            generated = [f"user_pref({json.dumps(key)}, {json.dumps(value, ensure_ascii=False)});" for key, value in prefs.items()]
            atomic_write(pref_path, "\n".join(retained + generated) + "\n")
        atomic_write(marker, MARKER + "\n")
        if seed:
            manifest = {
                "schema_version": 1,
                "profile": str(profile),
                "target": "Fedora Kinoite 44 native Firefox",
                "theme": "Union neutral Safari-reference chrome; native Firefox CSD controls in 52px navigation row",
                "palette_dependency": tokens["name"],
                "roles_sha256": hashlib.sha256(roles_path.read_bytes()).hexdigest(),
                "tokens_sha256": hashlib.sha256(tokens_path.read_bytes()).hexdigest(),
                "preferences": prefs,
                "native_verified_version": None,
                "visual_verified": False,
            }
            atomic_write(profile / "aven-profile.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    launcher = home / ".local/bin/aven-browser"
    # Remote requests remain enabled so mail and Dolphin links can open tabs.
    # The explicit profile avoids importing or editing ~/.mozilla profiles.
    atomic_write(launcher, "#!/bin/sh\nexec /usr/bin/firefox --profile " + shlex.quote(str(profile)) + ' "$@"\n', 0o755)
    desktop = "\n".join([
        "[Desktop Entry]", "Type=Application", "Name=Firefox Browser",
        "Name[zh_CN]=Firefox 浏览器", "Name[zh_TW]=Firefox 瀏覽器",
        "Comment=Browse the Web", "Exec=" + desktop_quote(str(launcher)) + " %u",
        "Icon=firefox", "Terminal=false", "Categories=Network;WebBrowser;",
        "MimeType=text/html;x-scheme-handler/http;x-scheme-handler/https;",
        # Match the native Wayland app ID / KWin resource_class, not the
        # lowercase resource_name. Plasma pins this same desktop-file ID.
        "StartupNotify=true", "StartupWMClass=org.mozilla.firefox", "",
    ])
    native = home / ".local/share/applications/org.mozilla.firefox.desktop"
    if native.exists() and "X-Aven-Managed=browser-v1" not in native.read_text():
        parser.error(f"Refusing to replace an existing custom desktop entry: {native}")
    atomic_write(native, desktop.replace("Type=Application", "Type=Application\nX-Aven-Managed=browser-v1"), 0o644)
    # Compatibility for saved associations, without a competing WMClass claim
    # that can make Plasma attach a running window to the hidden legacy ID.
    compatibility = desktop.replace("StartupWMClass=org.mozilla.firefox\n", "")
    atomic_write(home / ".local/share/applications/aven-browser.desktop", compatibility + "NoDisplay=true\n", 0o644)
    print(json.dumps({"profile": str(profile), "preferences_seeded": seed, "launcher": str(launcher), "desktop": native.name}, indent=2))


if __name__ == "__main__":
    main()
