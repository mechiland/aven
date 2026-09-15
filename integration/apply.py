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
    a = p.parse_args()
    release = Path('/etc/os-release').read_text()
    if 'ID=fedora' not in release or not Path('/run/ostree-booted').exists():
        p.error('Apply only inside the intended Fedora Atomic guest')
    if os.getuid() == 0:
        p.error('Run as the desktop user; system font configuration is installed separately')
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
                         (ROOT/'visual/aurorae',share/'aurorae/themes')]:
        if source.exists(): shutil.copytree(source,dest,dirs_exist_ok=True)
    def write(file,group,key,value):
        args = ['kwriteconfig6','--file',config/file]
        for part in group.split('/'):
            args += ['--group',part]
        command(*args,'--key',key,str(value))
    command('plasma-apply-colorscheme','AvenMist')
    # Fedora's Twilight shell defaults to breeze-dark independently of the
    # application color scheme. The adaptive default shell follows Aven Mist.
    command('plasma-apply-desktoptheme','default')
    # An explicit user value prevents Fedora's kdedefaults/breeze-dark from
    # returning when the default-theme command removes its redundant key.
    write('plasmarc','Theme','name','default')
    from PySide6.QtGui import QFont
    def font_value(family, size, weight=QFont.Weight.Normal):
        font = QFont(family, size, weight)
        # Short legacy font strings interpret weights on the Qt5 0..99 scale.
        # Let this installed Qt serialize its full current format.
        return font.toString()
    fonts = {
        'font':font_value('Noto Sans',11),
        'menuFont':font_value('Noto Sans',11),
        'toolBarFont':font_value('Noto Sans',11),
        'smallestReadableFont':font_value('Noto Sans',10),
        'fixed':font_value('Noto Sans Mono',10)}
    for key,value in fonts.items(): write('kdeglobals','General',key,value)
    write('kdeglobals','WM','activeFont',font_value('Noto Sans',11,QFont.Weight.Medium))
    for key,value in {'widgetStyle':'Breeze','AnimationDurationFactor':'0.65','SingleClick':'false'}.items():
        write('kdeglobals','KDE',key,value)
    write('kdeglobals','Icons','Theme','Aven')
    write('kdeglobals','Toolbar style','ToolButtonStyle','TextBesideIcon')
    write('kdeglobals','MainToolbarIcons','Size',22)
    write('kdeglobals','ToolbarIcons','Size',22)
    for key,value in {'XftAntialias':'true','XftHintStyle':'hintslight','XftSubPixel':'none'}.items():
        write('kdeglobals','General',key,value)
    for effect in ['wobblywindows','magiclamp','fallapart','glide','slide','cubeslide','windowaperture','sheet','squash','translucency','diminactive','scale']:
        write('kwinrc','Plugins',effect+'Enabled','false')
    for effect in ['fade','fadingpopups','overview']:
        write('kwinrc','Plugins',effect+'Enabled','true')
    write('kwinrc','TabBox','LayoutName','thumbnail_grid')
    write('kwinrc','TabBox','HighlightWindows','false')
    write('kwinrc','org.kde.kdecoration2','ButtonsOnLeft','')
    write('kwinrc','org.kde.kdecoration2','ButtonsOnRight','IAX')
    write('kwinrc','org.kde.kdecoration2','BorderSize','None')
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
        write(file,'Settings','gtk-font-name','Noto Sans 11')
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
        script=(ROOT/'integration/plasma-layout.js.in').read_text().replace('@WALLPAPER@',wallpaper.as_uri())
        dbus=shutil.which('qdbus6') or shutil.which('qdbus-qt6') or shutil.which('qdbus')
        if not dbus: raise RuntimeError('qdbus6 is required for the running Plasma session')
        command(dbus,'org.kde.plasmashell','/PlasmaShell','org.kde.PlasmaShell.evaluateScript',script)
        command(dbus,'org.kde.KWin','/KWin','reconfigure')
    print(f'Aven candidate installed. Config backup: {backup}. Log out/in before typography comparisons.')

if __name__ == '__main__': main()
