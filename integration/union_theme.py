"""Install Aven's Union style against the packaged Plasma 6.8 style engine."""
import json
from pathlib import Path
import shutil
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
STYLE_ID = 'aven-mist'


def install(home):
    base = Path('/usr/share/union/styles/breeze/contents/css/style.css')
    if not base.is_file():
        raise RuntimeError('Install the Plasma 6.8 plasma-union package and reboot before selecting Aven Union')
    from PySide6.QtWidgets import QStyleFactory
    if 'union' not in [name.lower() for name in QStyleFactory.keys()]:
        raise RuntimeError('The QtWidgets Union style plugin is unavailable')
    tokens = json.loads((ROOT/'visual/tokens.json').read_text())
    target = Path(home)/'.local/share/union/styles'/STYLE_ID
    shutil.copytree(ROOT/'visual/union'/STYLE_ID, target, dirs_exist_ok=True)
    values = {
        'control-radius': f"{tokens['radius']['control']}px",
        'surface-radius': f"{tokens['radius']['surface']}px",
        'control-height': f"{tokens['control']['comfortableHeight']}px",
        'border': tokens['border']['color'],
        'hover': tokens['surface']['hover'],
        'selection-soft': tokens['accent']['soft'],
        'text': tokens['foreground']['primary'],
        'chrome': tokens['surface']['chrome'],
        'sidebar': tokens['surface']['sidebar'],
    }
    css = '/* Generated from visual/tokens.json by integration/union_theme.py. */\n:root {\n'
    css += ''.join(f'    --aven-{key}: {value};\n' for key, value in values.items())
    (target/'contents/css/tokens.css').write_text(css+'}\n')
    install_files_compatibility(Path(home), tokens)
    install_photos_compatibility(Path(home), tokens)
    return target


def install_files_compatibility(home, tokens):
    """Keep KUrlNavigator readable on the 6.7.90 QtWidgets technology preview.

    This is a deliberately narrow Qt stylesheet, not a second application theme.
    The native Union adapter remains responsible for every other Dolphin control.
    Desktop, FileManager1 activation and the dedicated CLI use the same launcher.
    """
    directory = home/'.local/libexec/aven-union'
    directory.mkdir(parents=True, exist_ok=True)
    stylesheet = directory/'dolphin-location.qss'
    stylesheet.write_text(
        '/* Aven Union 6.7.90 compatibility: KUrlNavigator background/contrast. */\n'
        'KUrlNavigator {\n'
        f"    background-color: {tokens['surface']['chrome']};\n"
        f"    color: {tokens['foreground']['primary']};\n"
        '    border: none;\n'
        f"    border-radius: {tokens['radius']['control']}px;\n"
        '}\n'
        'KFilePlacesView {\n'
        f"    background-color: {tokens['surface']['sidebar']};\n"
        '    border: none;\n'
        '}\n'
        'QDockWidget { border: none; }\n')
    launcher = directory/'aven-files'
    launcher.write_text(
        '#!/bin/sh\n'
        'case "$(kreadconfig6 --file kdeglobals --group KDE --key widgetStyle)" in\n'
        '  Union|union) exec /usr/bin/dolphin -stylesheet '
        + shlex.quote(str(stylesheet)) + ' "$@" ;;\n'
        '  *) exec /usr/bin/dolphin "$@" ;;\n'
        'esac\n')
    launcher.chmod(0o755)
    # Dolphin's own New Window and FileManager1 paths launch the bare command
    # "dolphin --new-window" through KIO, bypassing the desktop entry.
    cli = home/'.local/bin/dolphin'
    cli.parent.mkdir(parents=True, exist_ok=True)
    if cli.exists() or cli.is_symlink():
        if cli.resolve() != launcher.resolve():
            raise RuntimeError(f'Refusing to replace an unrelated Files launcher: {cli}')
    else:
        cli.symlink_to('../libexec/aven-union/aven-files')
    # Desktop and D-Bus Exec fields use their own quoting, not shell syntax.
    quoted = '"' + str(launcher).replace('\\', '\\\\\\\\').replace('"', '\\\\"').replace('`', '\\\\`').replace('$', '\\\\$').replace('%', '%%') + '"'
    desktop = home/'.local/share/applications/org.kde.dolphin.desktop'
    desktop.parent.mkdir(parents=True, exist_ok=True)
    vendor = Path('/usr/share/applications/org.kde.dolphin.desktop').read_text()
    desktop.write_text('\n'.join('Exec='+quoted+line[len('Exec=dolphin'):] if line.startswith('Exec=dolphin') else line for line in vendor.splitlines())+'\n')
    service = home/'.local/share/dbus-1/services/org.kde.dolphin.FileManager1.service'
    service.parent.mkdir(parents=True, exist_ok=True)
    service.write_text('[D-BUS Service]\nName=org.freedesktop.FileManager1\nExec='+quoted+' --daemon\nSystemdService=plasma-dolphin.service\n')
    dropin = home/'.config/systemd/user/plasma-dolphin.service.d/aven-union.conf'
    dropin.parent.mkdir(parents=True, exist_ok=True)
    systemd_path = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%')
    dropin.write_text('[Service]\nExecStart=\nExecStart="'+systemd_path+'" --daemon\n')
    subprocess.run(['update-desktop-database', str(desktop.parent)], check=True)
    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)


def install_photos_compatibility(home, tokens):
    """The same Union KUrlNavigator workaround for native Gwenview entrypoints."""
    directory = home/'.local/libexec/aven-union'
    directory.mkdir(parents=True, exist_ok=True)
    stylesheet = directory/'gwenview-surfaces.qss'
    stylesheet.write_text(
        '/* Scoped native Gwenview surfaces; Union still draws other controls. */\n'
        'QWidget#mUrlNavigatorContainer, KUrlNavigator {\n'
        f"    background-color: {tokens['surface']['chrome']};\n"
        f"    color: {tokens['foreground']['primary']};\n"
        '    border: none;\n'
        '    border-radius: 0;\n'
        '}\n'
        'QWidget#mUrlNavigatorContainer { max-height: 34px; }\n'
        'QWidget#folders, QWidget#folders QTreeView {\n'
        f"    background-color: {tokens['surface']['sidebar']};\n"
        '    border: none;\n'
        '}\n'
        'QWidget#folders QScrollBar:horizontal {\n'
        f"    background-color: {tokens['surface']['sidebar']};\n"
        '    height: 8px; border: none;\n'
        '}\n'
        'QWidget#folders QScrollBar::handle:horizontal {\n'
        '    background: #B0B0B0; border-radius: 4px; min-width: 24px;\n'
        '}\n'
        'QWidget#folders QScrollBar::add-line:horizontal,\n'
        'QWidget#folders QScrollBar::sub-line:horizontal { width: 0; }\n')
    launcher = directory/'aven-photos'
    launcher.write_text('#!/bin/sh\n'
        'case "$(kreadconfig6 --file kdeglobals --group KDE --key widgetStyle)" in\n'
        '  Union|union) exec /usr/bin/gwenview -stylesheet '+shlex.quote(str(stylesheet))+' "$@" ;;\n'
        '  *) exec /usr/bin/gwenview "$@" ;;\n'
        'esac\n')
    launcher.chmod(0o755)
    cli = home/'.local/bin/gwenview'
    cli.parent.mkdir(parents=True, exist_ok=True)
    if cli.exists() or cli.is_symlink():
        if cli.resolve() != launcher.resolve():
            raise RuntimeError(f'Refusing to replace an unrelated Photos launcher: {cli}')
    else:
        cli.symlink_to('../libexec/aven-union/aven-photos')
    desktop = home/'.local/share/applications/org.kde.gwenview.desktop'
    desktop.parent.mkdir(parents=True, exist_ok=True)
    if desktop.exists() and 'X-Aven-Managed=union-photos' not in desktop.read_text():
        raise RuntimeError(f'Refusing to replace an unrelated Photos desktop entry: {desktop}')
    quoted = '"' + str(launcher).replace('\\', '\\\\\\\\').replace('"', '\\\\"').replace('`', '\\\\`').replace('$', '\\\\$').replace('%', '%%') + '"'
    vendor = Path('/usr/share/applications/org.kde.gwenview.desktop').read_text()
    desktop.write_text('\n'.join('Exec='+quoted+line[len('Exec=gwenview'):] if line.startswith('Exec=gwenview') else line for line in vendor.splitlines() if not line.startswith('StartupWMClass=')).replace('[Desktop Entry]', '[Desktop Entry]\nX-Aven-Managed=union-photos\nStartupWMClass=org.kde.gwenview')+'\n')
    # Fedora's hidden importer claims StartupWMClass=gwenview. Plasma 6.7.90
    # checks that resource name before the viewer's correct desktop app ID,
    # so it assigns viewer windows to the importer and duplicates the dock icon.
    # Override only that incorrect hint, retaining the vendor import command.
    importer_vendor = Path('/usr/share/applications/org.kde.gwenview_importer.desktop')
    importer = desktop.with_name(importer_vendor.name)
    marker = 'X-Aven-Managed=union-photos-importer-metadata'
    if importer_vendor.exists():
        if importer.is_symlink() or (importer.exists() and marker not in importer.read_text()):
            raise RuntimeError(f'Refusing to replace an unrelated Photos importer entry: {importer}')
        lines = importer_vendor.read_text().splitlines()
        importer.write_text('\n'.join(line for line in lines if line != 'StartupWMClass=gwenview').replace('[Desktop Entry]', '[Desktop Entry]\n'+marker)+'\n')
    subprocess.run(['update-desktop-database', str(desktop.parent)], check=True)
