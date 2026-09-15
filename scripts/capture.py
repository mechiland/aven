#!/usr/bin/env python3
"""Capture a real guest framebuffer with immutable provenance beside it."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vm import qmp, ROOT, VM

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene')
    p.add_argument('--guest', choices=['stock', 'aven'], required=True)
    p.add_argument('--round', type=int, default=0)
    p.add_argument('--scale', type=float, default=1)
    p.add_argument('--locale', choices=['en_US.UTF-8','zh_CN.UTF-8','zh_TW.UTF-8','zh_HK.UTF-8'], default='en_US.UTF-8')
    p.add_argument('--note', default='')
    p.add_argument('--backend', choices=['auto','qmp','rfb'], default='auto')
    a = p.parse_args()
    if not a.scene.replace('-', '').replace('_', '').isalnum():
        p.error('Use a simple scene name')
    dest = ROOT / 'evidence' / a.guest / f'round-{a.round:02}'
    dest.mkdir(parents=True, exist_ok=True)
    stem = f'{a.scene}-{a.scale:g}x'
    png = dest / f'{stem}.png'
    if png.exists():
        p.error(f'Capture exists; choose a new scene or round: {png}')
    transport=None
    method='QEMU QMP screendump; unmodified guest framebuffer'
    try:
        if a.backend=='rfb':raise RuntimeError('no surface: explicitly requested RFB')
        qmp(a.guest, 'screendump', {'filename': str(png), 'format': 'png'})
        captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    except RuntimeError as error:
        if a.backend=='qmp' or 'no surface' not in str(error):raise
        sys.path.insert(0,str(ROOT/'verification'))
        from rfb_capture import capture, png_bytes, METHOD
        rgb,transport=capture(5920 if a.guest=='stock' else 5921)
        png.write_bytes(png_bytes(transport['width'],transport['height'],rgb))
        method=METHOD
        captured_at=transport['captured_at']
    port = '2222' if a.guest == 'stock' else '2223'
    result = subprocess.run(['ssh', '-i', str(VM/'id_ed25519'), '-p', port,
        '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=accept-new',
        '-o', f'UserKnownHostsFile={VM/"known_hosts"}', 'aven@127.0.0.1',
        'rpm-ostree status --json; rpm -q plasma-desktop kwin dolphin firefox thunderbird gwenview fontconfig freetype; '
        'cat /etc/os-release; bash ~/aven/scripts/guest-session.sh kscreen-doctor -o'],
        capture_output=True, text=True)
    probe = subprocess.run(['ssh', '-i', str(VM/'id_ed25519'), '-p', port,
        '-o', 'BatchMode=yes', '-o', f'UserKnownHostsFile={VM/"known_hosts"}', 'aven@127.0.0.1',
        f'env LC_ALL={a.locale} LANG={a.locale} LANGUAGE={a.locale.split(".")[0]} bash ~/aven/scripts/guest-session.sh python3 ~/aven/verification/guest_probe.py --guest {a.guest}'],
        capture_output=True, text=True)
    try:
        runtime_probe=json.loads(probe.stdout) if probe.returncode == 0 else None
    except json.JSONDecodeError:
        runtime_probe=None
    metadata = {'captured_at': captured_at,
        'guest': a.guest, 'round': a.round, 'scene': a.scene, 'declared_scale': a.scale,
        'declared_locale': a.locale, 'note': a.note,
        'method': method, 'framebuffer_transport':transport,
        'image': str(png.relative_to(ROOT)), 'sha256': hashlib.sha256(png.read_bytes()).hexdigest(),
        'guest_probe_stdout': result.stdout, 'guest_probe_stderr': result.stderr,
        'guest_probe_exit_code': result.returncode, 'runtime_probe':runtime_probe,
        'runtime_probe_stderr':probe.stderr, 'visually_inspected': False}
    (dest/f'{stem}.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+'\n')
    print(png)

if __name__ == '__main__': main()
