#!/usr/bin/python3
"""Install the preview and Dolphin defaults into a prototype user's home.

Run with Dolphin closed. No Fedora package, system theme or Plasma files change.
Existing config keys not owned by this layer are preserved; original config
files are backed up once beside themselves as *.pre-aven.
"""

import argparse
import configparser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from places import configure_places

SOURCE = Path(__file__).resolve().parent
ACTION = "servicemenu_aven-preview.desktop::aven-preview"


def backup(path):
    saved = path.with_name(path.name + ".pre-aven")
    if path.exists() and not saved.exists():
        shutil.copy2(path, saved)


def merge_ini(path, sections):
    path.parent.mkdir(parents=True, exist_ok=True)
    backup(path)
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    if path.exists():
        config.read(path, encoding="utf-8")
    for section, values in sections.items():
        if not config.has_section(section):
            config.add_section(section)
        for key, value in values.items():
            config.set(section, key, str(value))
    with path.open("w", encoding="utf-8") as stream:
        config.write(stream, space_around_delimiters=False)


def install_shortcut(home, xml_version=None):
    # KDE Frameworks 6 still uses kxmlgui5 as the data directory name.
    target = home / ".local/share/kxmlgui5/dolphin/dolphinui.rc"
    target.parent.mkdir(parents=True, exist_ok=True)
    backup(target)
    gui = ET.parse(target).getroot() if target.exists() else ET.Element("gui", name="dolphin", version="0")
    if gui.find("MenuBar") is None and gui.find("ToolBar") is None:
        # This file is only a shortcut seed, not a complete replacement UI.
        # KXmlGuiVersionHandler chooses the highest-version document. Giving a
        # fragment the native version makes it replace Dolphin's entire UI.
        # Version 0 instead invokes KDE's native upgrade path, which copies the
        # current embedded UI and merges these ActionProperties into it.
        # Also repairs the version 48/49 fragment written by the first prototype.
        gui.set("version", "0")
    properties = gui.find("ActionProperties")
    if properties is None:
        properties = ET.SubElement(gui, "ActionProperties", scheme="Default")
    action = next((item for item in properties.findall("Action") if item.get("name") == ACTION), None)
    if action is None:
        action = ET.SubElement(properties, "Action", name=ACTION)
    action.set("shortcut", "Ctrl+Alt+P")
    ET.indent(gui)
    ET.ElementTree(gui).write(target, encoding="utf-8", xml_declaration=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--xmlgui-version", type=int, help="48 for Dolphin 26.04, 49 for 26.08; detected from installed dolphin by default")
    parser.add_argument("--skip-layout", action="store_true", help="For staging without Qt; seed native layout later with files/layout.py")
    parser.add_argument("--shortcut-only", action="store_true", help="Repair or update only the native Preview shortcut configuration")
    args = parser.parse_args()
    home = args.home.resolve()
    version = args.xmlgui_version
    if version is None:
        installed = subprocess.check_output(["dolphin", "--version"], text=True).strip()
        if "26.04" in installed:
            version = 48
        elif "26.08" in installed:
            version = 49
        else:
            parser.error("This integration requires Dolphin 26.04 or 26.08. Verify its XMLGUI version before using --xmlgui-version.")
    if args.shortcut_only:
        shortcut = install_shortcut(home)
        print(json.dumps({"shortcut": "Ctrl+Alt+P", "shortcut_file": str(shortcut), "merge": "KDE native XMLGUI upgrade", "restart_dolphin_required": True}, indent=2))
        return
    destination = home / ".local/libexec/aven-preview"
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE.parent / "preview/aven_preview", destination / "aven_preview", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(SOURCE.parent / "preview/aven-preview", destination / "aven-preview")
    (destination / "aven-preview").chmod(0o755)
    binary = home / ".local/bin/aven-preview"
    binary.parent.mkdir(parents=True, exist_ok=True)
    if binary.exists() or binary.is_symlink():
        if not binary.is_symlink():
            backup(binary)
        binary.unlink()
    binary.symlink_to("../libexec/aven-preview/aven-preview")
    for name, relative in (("aven-preview.desktop", ".local/share/kio/servicemenus/aven-preview.desktop"), ("org.aven.Preview.desktop", ".local/share/applications/org.aven.Preview.desktop")):
        target = home / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / name, target)
        # Desktop Exec grammar has its own quoted-string escaping.
        # Absolute path keeps the action working before next login updates PATH.
        executable = str(binary).replace("\\", "\\\\\\\\").replace('"', '\\\\"').replace("`", "\\\\`").replace("$", "\\\\$").replace("%", "%%")
        target.write_text(target.read_text().replace("Exec=aven-preview -- %U", f'Exec="{executable}" -- %U'), encoding="utf-8")
        target.chmod(0o755)
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    config.read(SOURCE / "dolphinrc", encoding="utf-8")
    values = {section: dict(config[section]) for section in config.sections()}
    values["General"]["HomeUrl"] = str(home)
    merge_ini(home / ".config/dolphinrc", values)
    # Home/Documents/Downloads start in a concise details view; Pictures is a grid.
    for path, mode in ((home / ".local/share/dolphin/view_properties/global/.directory", "1"), (home / "Documents/.directory", "1"), (home / "Downloads/.directory", "1"), (home / "Pictures/.directory", "0")):
        merge_ini(path, {"Dolphin": {"Version": "4", "ViewMode": mode, "PreviewsShown": "true", "SortFoldersFirst": "true", "GroupedSorting": "false", "VisibleRoles": "Details_text,Details_size,Details_modificationtime"}})
    shortcut = install_shortcut(home, version)
    places = configure_places(home)
    layout = {"changed": False, "reason": "staging without Qt"}
    if not args.skip_layout:
        layout = json.loads(subprocess.check_output([sys.executable, str(SOURCE / "layout.py"), "--home", str(home)], text=True, env=os.environ | {"QT_QPA_PLATFORM": "offscreen"}))
    print(json.dumps({"preview": str(binary), "shortcut": "Ctrl+Alt+P", "shortcut_file": str(shortcut), "xmlgui_version": version, "places": places, "layout": layout, "packages_required": ["python3-pyside6", "kf6-kimageformats", "kio-extras", "kdegraphics-thumbnailers", "ghostscript", "ffmpegthumbs"]}, indent=2))


if __name__ == "__main__":
    main()
