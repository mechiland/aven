#!/usr/bin/env python3
"""Observe the selected Union style and libraries in actual native applications."""
import configparser
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

from PySide6.QtCore import QLibraryInfo
from PySide6.QtWidgets import QApplication, QPushButton, QStyle, QStyleFactory


def main():
    app = QApplication([])
    if app.platformName() != 'wayland':
        raise RuntimeError('Run this probe in the real Wayland desktop session')
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read(Path.home()/'.config/kdeglobals')
    button = QPushButton('打开文件 · Open file')
    style = app.style()
    processes = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            if path.stat().st_uid != os.getuid():
                continue
            command = (path/'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace').strip()
            executable = Path(os.readlink(path/'exe')).name
            if executable not in ['dolphin', 'gwenview', 'firefox', 'thunderbird', 'python3.14', 'python3', 'python3.15']:
                continue
            if executable.startswith('python') and 'aven_preview' not in command and 'aven-preview' not in command:
                continue
            mappings = (path/'maps').read_text()
            libraries = sorted({line.split()[-1] for line in mappings.splitlines()
                                if 'libUnion' in line or 'UnionWidgetsStyle' in line})
            environment = dict(item.split(b'=', 1) for item in (path/'environ').read_bytes().split(b'\0') if b'=' in item)
            processes.append({'pid': int(path.name), 'executable': executable,
                              'command': command, 'union_libraries': libraries,
                              'locale': {key: environment.get(key.encode(), b'').decode(errors='replace')
                                         for key in ['LANG', 'LANGUAGE', 'LC_ALL']}})
        except (OSError, PermissionError):
            continue
    theme = Path.home()/'.local/share/union/styles/aven-mist'
    hashes = {str(p.relative_to(theme)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(theme.rglob('*')) if p.is_file()}
    packages = subprocess.run(['rpm', '-q', 'plasma-desktop', 'kwin', 'plasma-union', 'cxx-rust-cssparser',
                               'dolphin', 'gwenview', 'qt6-qtbase'], capture_output=True, text=True)
    data = {'schema_version': 1, 'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'platform': app.platformName(), 'qt': QLibraryInfo.version().toString(),
            'configured_widget_style': config.get('KDE', 'widgetStyle', fallback=None),
            'configured_union_style': config.get('KDE', 'unionStyle', fallback=None),
            'actual_style_class': style.metaObject().className(), 'actual_style_name': style.objectName(),
            'available_styles': QStyleFactory.keys(),
            'button_size_hint': [button.sizeHint().width(), button.sizeHint().height()],
            'button_margin': style.pixelMetric(QStyle.PixelMetric.PM_ButtonMargin, None, button),
            'theme_sha256': hashes, 'packages': packages.stdout,
            'files_compatibility_sha256': {str(p.relative_to(Path.home())): hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in sorted((Path.home()/'.local/libexec/aven-union').glob('*')) if p.is_file()},
            'native_processes': processes,
            'limitations': ['Library mappings and style metrics do not establish visual quality; inspect real screenshots.']}
    data['style_active'] = (data['actual_style_class'] == 'UnionStyle'
                            and data['configured_union_style'] == 'aven-mist' and bool(hashes))
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
