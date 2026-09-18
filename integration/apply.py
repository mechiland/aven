#!/usr/bin/env python3
"""Apply the focused Aven profile to the current user in a Kinoite guest."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def command(*args):
    print('+', ' '.join(str(x) for x in args), flush=True)
    return subprocess.run([str(x) for x in args], check=True, capture_output=True, text=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decoration', choices=['breeze', 'aven'], default='breeze', help='Aven decoration is a candidate until boot-tested')
    p.add_argument('--without-shell-reload', action='store_true')
    p.add_argument('--style', choices=['breeze', 'union'], default='breeze')
    a = p.parse_args()
    release = Path('/etc/os-release').read_text()
    if 'ID=fedora' not in release or not Path('/run/ostree-booted').exists():
        p.error('Apply only inside the intended Fedora Atomic guest')
    if os.getuid() == 0:
        p.error('Run as the desktop user; system font configuration is installed separately')
    if a.style == 'union':
        from union_theme import install
        install(Path.home())
        command('kbuildsycoca6','--noincremental')
    config = Path.home()/'.config'
    share = Path.home()/'.local/share'
    backup = Path.home()/'.local/state/aven'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True)
    configs = ['kdeglobals', 'kwinrc', 'plasmarc', 'plasmashellrc', 'plasma-org.kde.plasma.desktop-appletsrc', 'kcminputrc', 'breezerc', 'gtk-3.0/settings.ini', 'gtk-4.0/settings.ini']
    saved, absent, hashes = [], [], {}
    for name in configs:
        src = config/name
        if src.exists():
            dst = backup/name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src,dst)
            saved.append(name)
            hashes[name] = hashlib.sha256(dst.read_bytes()).hexdigest()
        else:
            absent.append(name)
    (backup/'manifest.json').write_text(json.dumps({'backed_up': saved, 'absent': absent, 'sha256': hashes, 'scope': 'shared-config', 'profile': 'Aven Mist v1'}, indent=2))
    # Assets are user-local and replace only the Aven namespace.
    for source, dest in [(ROOT/'visual/color-schemes',share/'color-schemes'),
                         (ROOT/'visual/wallpapers',share/'wallpapers'),
                         (ROOT/'visual/icons',share/'icons'),
                         (ROOT/'visual/aurorae',share/'aurorae/themes'),
                         (ROOT/'visual/plasma',share/'plasma/desktoptheme')]:
        if source.exists(): shutil.copytree(source,dest,dirs_exist_ok=True)
    def write(file,group,key,value):
        args = ['kwriteconfig6','--file',config/file]
        for part in group.split('/'):
            args += ['--group',part]
        command(*args,'--key',key,str(value))
    # The native tool skips a scheme whose name is already selected, even when
    # its file changed. Switch through the packaged light scheme to invalidate
    # the palette before applying an updated Aven package.
    command('plasma-apply-colorscheme','BreezeLight')
    command('plasma-apply-colorscheme','AvenMist')
    # Union overrides only panel/task frames; the remaining shell assets
    # inherit the default Plasma style and follow the application palette.
    shell_theme = 'aven-dock' if a.style == 'union' else 'default'
    command('plasma-apply-desktoptheme',shell_theme)
    # An explicit user value prevents Fedora's kdedefaults/breeze-dark from
    # returning when the default-theme command removes its redundant key.
    write('plasmarc','Theme','name',shell_theme)
    from PySide6.QtGui import QFont
    roles = json.loads((ROOT/'typography/roles.json').read_text())
    tokens = json.loads((ROOT/'visual/tokens.json').read_text())
    def font_value(role):
        font = QFont(role['family'])
        font.setPointSizeF(role['point_size'])
        font.setWeight(QFont.Weight(role['weight']))
        # Short legacy font strings interpret weights on the Qt5 0..99 scale.
        # Let this installed Qt serialize its full current format.
        return font.toString()
    fonts = {
        'font':font_value(roles['ui']),
        'menuFont':font_value(roles['ui']),
        'toolBarFont':font_value(roles['ui']),
        'smallestReadableFont':font_value(roles['secondary']),
        'fixed':font_value(roles['monospace'])}
    for key,value in fonts.items(): write('kdeglobals','General',key,value)
    write('kdeglobals','WM','activeFont',font_value(roles['window_title']))
    native_style = 'Union' if a.style == 'union' else 'Breeze'
    for key,value in {'widgetStyle':native_style,'AnimationDurationFactor':'0.65','SingleClick':'false'}.items():
        write('kdeglobals','KDE',key,value)
    if a.style == 'union':
        write('kdeglobals','KDE','unionStyle','aven-mist')
    write('kdeglobals','Icons','Theme','Aven')
    write('kdeglobals','Toolbar style','ToolButtonStyle','IconOnly')
    write('kdeglobals','MainToolbarIcons','Size',tokens['icon']['toolbar'])
    write('kdeglobals','ToolbarIcons','Size',tokens['icon']['toolbar'])
    for key,value in {'XftAntialias':'true','XftHintStyle':'hintslight','XftSubPixel':'none'}.items():
        write('kdeglobals','General',key,value)
    for effect in ['wobblywindows','magiclamp','fallapart','glide','slide','cubeslide','windowaperture','sheet','squash','translucency','diminactive','scale']:
        write('kwinrc','Plugins',effect+'Enabled','false')
    for effect in ['fade','fadingpopups','overview']:
        write('kwinrc','Plugins',effect+'Enabled','true')
    write('kwinrc','TabBox','LayoutName','thumbnail_grid')
    write('kwinrc','TabBox','HighlightWindows','false')
    write('kwinrc','org.kde.kdecoration2','ButtonsOnLeft','XIA' if a.decoration == 'aven' else '')
    write('kwinrc','org.kde.kdecoration2','ButtonsOnRight','' if a.decoration == 'aven' else 'IAX')
    write('kwinrc','org.kde.kdecoration2','BorderSize','Normal' if a.decoration == 'aven' else 'None')
    write('kwinrc','org.kde.kdecoration2','BorderSizeAuto','false')
    if a.decoration == 'aven':
        write('kwinrc','org.kde.kdecoration2','library','org.kde.kwin.aurorae')
        write('kwinrc','org.kde.kdecoration2','theme','__aurorae__svg__Aven')
    else:
        write('kwinrc','org.kde.kdecoration2','library','org.kde.breeze')
        write('kwinrc','org.kde.kdecoration2','theme','Breeze')
        write('breezerc','Windeco','TitleAlignment','AlignLeft')
        write('breezerc','Windeco','DrawTitleBarSeparator','false')
        write('breezerc','Windeco','DrawBackgroundGradient','false')
        write('breezerc','Windeco','OutlineIntensity',0)
        write('breezerc','Windeco','ShadowStrength',110)
    for file in ['gtk-3.0/settings.ini','gtk-4.0/settings.ini']:
        write(file,'Settings','gtk-font-name',f"{roles['ui']['family']} {roles['ui']['point_size']}")
        write(file,'Settings','gtk-theme-name','Breeze')
        write(file,'Settings','gtk-icon-theme-name','Aven')
        write(file,'Settings','gtk-application-prefer-dark-theme','false')
        write(file,'Settings','gtk-xft-antialias',1)
        write(file,'Settings','gtk-xft-hinting',1)
        write(file,'Settings','gtk-xft-hintstyle','hintslight')
        write(file,'Settings','gtk-xft-rgba','none')
    if not a.without_shell_reload:
        env = os.environ
        env['XDG_RUNTIME_DIR'] = f'/run/user/{os.getuid()}'
        env['DBUS_SESSION_BUS_ADDRESS'] = f'unix:path={env["XDG_RUNTIME_DIR"]}/bus'
        wallpaper = share/'wallpapers/AvenEstuary/contents/images/3840x2160.svg'
        dbus=shutil.which('qdbus6') or shutil.which('qdbus-qt6') or shutil.which('qdbus')
        if not dbus: raise RuntimeError('qdbus6 is required for the running Plasma session')
        from panel_layout import apply_layout
        apply_layout(dbus, a.style, wallpaper)
        # KWin reads QFontDatabase::TitleFont through the platform-theme cache.
        # Reconfigure alone does not refresh an already cached WM activeFont.
        command('dbus-send','--session','--type=signal','/KDEPlatformTheme',
                'org.kde.KDEPlatformTheme.refreshFonts')
        command(dbus,'org.kde.KWin','/KWin','reconfigure')
    print(f'Aven candidate installed. Config backup: {backup}. Log out/in before typography comparisons.')

if __name__ == '__main__': main()
