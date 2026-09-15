#!/usr/bin/env python3
"""Reproducible, unprivileged QEMU/KVM laboratory. Never touches a physical disk."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache'
VM = CACHE / 'vm'
DOWNLOADS = CACHE / 'downloads'
ISO = DOWNLOADS / 'Fedora-Kinoite-ostree-x86_64-44-1.7.iso'

def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)

def qmp(name, command, arguments=None):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(15)
        sock.connect(str(VM / f'{name}.qmp'))
        f = sock.makefile('rwb', buffering=0)
        json.loads(f.readline())
        def call(cmd, args=None):
            f.write((json.dumps({'execute': cmd, 'arguments': args or {}}) + '\n').encode())
            while True:
                response = json.loads(f.readline())
                if 'error' in response:
                    raise RuntimeError(response['error'])
                if 'return' in response:
                    return response['return']
        call('qmp_capabilities')
        return call(command, arguments)

def prepare():
    VM.mkdir(parents=True, exist_ok=True)
    expected = '4a944312b4e861ab625fd9786957174ef122a8a406bbb54caba7665e0d9f0e92'
    with ISO.open('rb') as f:
        if hashlib.file_digest(f, 'sha256').hexdigest() != expected:
            raise RuntimeError('Download and verify the complete official ISO first')
    run(['gpgv', '--keyring', DOWNLOADS / 'fedora.gpg', DOWNLOADS / 'Fedora-Kinoite-44-1.7-x86_64-CHECKSUM'])
    if not (VM / 'id_ed25519').exists():
        run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', VM / 'id_ed25519', '-C', 'aven-disposable-vm'])
    key = (VM / 'id_ed25519.pub').read_text().strip()
    (VM / 'stock.ks').write_text((ROOT / 'baseline/stock.ks.in').read_text().replace('@SSH_PUBLIC_KEY@', key))
    run(['xorriso', '-osirrox', 'on', '-overwrite', 'on', '-indev', ISO, '-extract', '/images/pxeboot/vmlinuz', VM / 'vmlinuz', '-extract', '/images/pxeboot/initrd.img', VM / 'initrd.img'])
    # Append a newc archive containing only the public-key kickstart to the initrd.
    archive = subprocess.run(['cpio', '-o', '-H', 'newc'], input=b'stock.ks\n', cwd=VM, stdout=subprocess.PIPE, check=True).stdout
    with (VM / 'initrd.img').open('ab') as f:
        f.write(archive)

def start(name, install=False, gpu=False, width=1920, height=1200):
    disk = VM / f'{name}.qcow2'
    if (VM / f'{name}.qmp').exists():
        try:
            qmp(name, 'query-status')
            raise RuntimeError(f'{name} already running')
        except (ConnectionRefusedError, FileNotFoundError):
            (VM / f'{name}.qmp').unlink(missing_ok=True)
    if not disk.exists():
        if not install:
            raise RuntimeError(f'Missing {disk}; install or clone first')
        run(['qemu-img', 'create', '-f', 'qcow2', disk, '48G'])
    elif install:
        raise RuntimeError(f'Refusing to reinstall over existing {disk}; preserve or remove the disposable disk explicitly first')
    port = 2222 if name == 'stock' else 2223
    args = ['qemu-system-x86_64', '-name', f'Aven {name}', '-machine', 'q35,accel=kvm', '-cpu', 'host', '-smp', '4', '-m', '6144',
            '-drive', f'file={disk},format=qcow2,if=virtio,cache=writeback',
            '-device', ('virtio-vga-gl' if gpu else 'virtio-vga') + f',xres={width},yres={height}',
            '-display', 'egl-headless,rendernode=/dev/dri/renderD128' if gpu else 'none',
            '-vnc', f'127.0.0.1:{20 if name == "stock" else 21}',
            '-device', 'qemu-xhci', '-device', 'usb-tablet',
            '-audiodev', 'none,id=lab-audio', '-device', 'ich9-intel-hda', '-device', 'hda-duplex,audiodev=lab-audio',
            '-netdev', f'user,id=net0,hostfwd=tcp:127.0.0.1:{port}-:22', '-device', 'virtio-net-pci,netdev=net0',
            '-device', 'virtio-rng-pci', '-qmp', f'unix:{VM / (name + ".qmp")},server=on,wait=off',
            '-chardev', f'socket,id=serial0,path={VM / (name + ".serial.sock")},server=on,wait=off,logfile={VM / (name + ".serial.log")}',
            '-serial', 'chardev:serial0', '-pidfile', VM / f'{name}.pid', '-daemonize']
    if install:
        args += ['-cdrom', ISO, '-kernel', VM / 'vmlinuz', '-initrd', VM / 'initrd.img',
                 '-append', 'inst.ks=file:/stock.ks inst.stage2=hd:LABEL=Fedora-Knt-ostree-x86_64-44 inst.text console=tty0 console=ttyS0,115200n8', '-no-reboot']
    run(args)
    print(f'{name}: SSH 127.0.0.1:{port}; VNC loopback; QMP {VM / (name + ".qmp")}')

def ssh(name, command):
    port = '2222' if name == 'stock' else '2223'
    return subprocess.call(['ssh', '-i', str(VM / 'id_ed25519'), '-p', port,
        '-o', 'StrictHostKeyChecking=accept-new', '-o', f'UserKnownHostsFile={VM / "known_hosts"}',
        '-o', 'ConnectTimeout=5', '-o', 'BatchMode=yes', 'aven@127.0.0.1', *command])

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['prepare', 'install', 'boot', 'clone', 'status', 'stop', 'screenshot', 'key', 'ssh'])
    p.add_argument('--name', choices=['stock', 'aven'], default='stock')
    p.add_argument('--gpu', action='store_true')
    p.add_argument('--width', type=int, default=1920)
    p.add_argument('--height', type=int, default=1200)
    p.add_argument('args', nargs='*')
    args = p.parse_args()
    if not 800 <= args.width <= 4096 or not 600 <= args.height <= 2560:
        p.error('Use a viewport from 800x600 through 4096x2560')
    VM.mkdir(parents=True, exist_ok=True)
    if args.action == 'prepare': prepare()
    elif args.action in ['install', 'boot']: start(args.name, args.action == 'install', args.gpu, args.width,args.height)
    elif args.action == 'clone':
        if (VM / 'aven.qcow2').exists(): raise RuntimeError('Aven disk already exists')
        try:
            status = qmp('stock', 'query-status')
            raise RuntimeError(f'Power off stock cleanly before cloning: {status}')
        except (ConnectionRefusedError, FileNotFoundError): pass
        run(['qemu-img', 'convert', '-p', '-O', 'qcow2', VM / 'stock.qcow2', VM / 'aven.qcow2'])
    elif args.action == 'status': print(json.dumps(qmp(args.name, 'query-status'), indent=2))
    elif args.action == 'stop': qmp(args.name, 'system_powerdown')
    elif args.action == 'key':
        qmp(args.name, 'human-monitor-command', {'command-line': 'sendkey ' + args.args[0]})
    elif args.action == 'screenshot':
        path = Path(args.args[0]).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            qmp(args.name, 'screendump', {'filename': str(path), 'format': 'png'})
        except RuntimeError as error:
            if 'no surface' not in str(error):raise
            sys.path.insert(0,str(ROOT/'verification'))
            from rfb_capture import capture,png_bytes
            rgb,meta=capture(5920 if args.name=='stock' else 5921)
            path.write_bytes(png_bytes(meta['width'],meta['height'],rgb))
        print(path)
    elif args.action == 'ssh': sys.exit(ssh(args.name, args.args))

if __name__ == '__main__': main()
