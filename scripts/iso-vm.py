#!/usr/bin/env python3
"""Disposable ISO boot/install laboratory, isolated from the stock/Aven proof VMs."""
import argparse
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / '.cache/iso-test'
ISO = ROOT / 'output/Aven-Atomic-KDE-44-0.1.0-prototype-x86_64.iso'


def run(*args, **kwargs):
    return subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def qmp(command, arguments=None):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(20)
        sock.connect(str(LAB / 'vm.qmp'))
        stream = sock.makefile('rwb', buffering=0)
        json.loads(stream.readline())
        def call(cmd, args=None):
            stream.write((json.dumps({'execute': cmd, 'arguments': args or {}}) + '\n').encode())
            while True:
                response = json.loads(stream.readline())
                if 'error' in response:
                    raise RuntimeError(response['error'])
                if 'return' in response:
                    return response['return']
        call('qmp_capabilities')
        return call(command, arguments)


def prepare(iso):
    LAB.mkdir(parents=True, exist_ok=True)
    if not (LAB / 'id_ed25519').exists():
        run('ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', LAB / 'id_ed25519', '-C', 'aven-iso-disposable-test')
    # Test-only account/access and disk erasure, never copied into the public ISO.
    ks = (ROOT / 'baseline/stock.ks.in').read_text()
    ks = ks.replace('@SSH_PUBLIC_KEY@', (LAB / 'id_ed25519.pub').read_text().strip())
    ks = ks.replace('services --enabled=sshd,plasmalogin', 'services --enabled=sshd')
    ks = '\n'.join(line for line in ks.splitlines()
                   if not line.startswith(('ostreesetup ', 'systemctl set-default ', 'touch /etc/plasma-setup-done')))
    run('xorriso', '-osirrox', 'on', '-overwrite', 'on', '-indev', iso,
        '-extract', '/aven/aven.ks', LAB / 'public-aven.ks')
    public = (LAB / 'public-aven.ks').read_text().replace('\ngraphical\n', '\n')
    (LAB / 'iso-test.ks').write_text(ks + '\n' + public)
    run('xorriso', '-osirrox', 'on', '-overwrite', 'on', '-indev', iso,
        '-extract', '/images/pxeboot/vmlinuz', LAB / 'vmlinuz',
        '-extract', '/images/pxeboot/initrd.img', LAB / 'initrd.img')
    archive = run('cpio', '-o', '-H', 'newc', input=b'iso-test.ks\n', cwd=LAB, stdout=subprocess.PIPE).stdout
    with (LAB / 'initrd.img').open('ab') as stream:
        stream.write(archive)


def start(mode, iso, uefi=False, disk=None):
    LAB.mkdir(parents=True, exist_ok=True)
    if (LAB / 'vm.qmp').exists():
        try:
            qmp('query-status')
        except (ConnectionRefusedError, FileNotFoundError):
            (LAB / 'vm.qmp').unlink(missing_ok=True)
        else:
            raise RuntimeError('ISO test VM is already running')
    args = ['qemu-system-x86_64', '-name', 'Aven ISO verification', '-machine', 'q35,accel=kvm',
            '-cpu', 'host', '-smp', '4', '-m', '6144',
            '-device', 'virtio-vga-gl,xres=1920,yres=1200',
            '-display', 'egl-headless,rendernode=/dev/dri/renderD128', '-vnc', '127.0.0.1:22',
            '-device', 'qemu-xhci', '-device', 'usb-tablet',
            '-audiodev', 'none,id=audio', '-device', 'ich9-intel-hda', '-device', 'hda-duplex,audiodev=audio',
            # restrict=on blocks guest access to the internet; forwarded local SSH remains available.
            '-netdev', 'user,id=net0,restrict=on,hostfwd=tcp:127.0.0.1:2224-:22', '-device', 'virtio-net-pci,netdev=net0',
            '-device', 'virtio-rng-pci', '-qmp', f'unix:{LAB / "vm.qmp"},server=on,wait=off',
            '-chardev', f'socket,id=serial,path={LAB / "serial.sock"},server=on,wait=off,logfile={LAB / (mode + ("-uefi" if uefi else "-bios") + ".serial.log")}',
            '-serial', 'chardev:serial', '-pidfile', LAB / 'vm.pid', '-daemonize']
    if uefi:
        vars_path = LAB / 'OVMF_VARS.fd'
        if not vars_path.exists():
            shutil.copy2('/usr/share/OVMF/OVMF_VARS_4M.fd', vars_path)
        args += ['-drive', 'if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd',
                 '-drive', f'if=pflash,format=raw,file={vars_path}']
    disk = (disk or LAB / 'installed.qcow2').resolve()
    if mode in ['install', 'public-install']:
        if disk.exists():
            raise RuntimeError('Refusing to overwrite a test installation; archive it explicitly first')
        run('qemu-img', 'create', '-f', 'qcow2', disk, '48G')
        args += ['-drive', f'file={disk},format=qcow2,if=virtio', '-cdrom', str(iso)]
        if mode == 'public-install':
            args += ['-boot', 'order=d']
        else:
            args += [
                 '-kernel', str(LAB / 'vmlinuz'), '-initrd', str(LAB / 'initrd.img'),
                 '-append', 'inst.ks=file:/iso-test.ks inst.stage2=hd:LABEL=Fedora-Knt-ostree-x86_64-44 inst.text console=tty0 console=ttyS0,115200n8', '-no-reboot']
    elif mode == 'optical':
        args += ['-cdrom', str(iso), '-boot', 'order=d']
    elif mode == 'boot':
        if not disk.exists():
            raise RuntimeError('Install the disposable disk first')
        args += ['-drive', f'file={disk},format=qcow2,if=virtio', '-boot', 'order=c']
    run(*args)
    print(f'{mode}: SSH 2224, VNC 5922; internet restricted; UEFI={uefi}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'optical', 'install', 'public-install', 'boot', 'status', 'stop', 'quit', 'key', 'click', 'text', 'screenshot', 'ssh'])
    parser.add_argument('--iso', type=Path, default=ISO)
    parser.add_argument('--uefi', action='store_true')
    parser.add_argument('--disk', type=Path, help='Explicit disposable test disk; new installs never overwrite it')
    parser.add_argument('args', nargs='*')
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.iso)
    elif args.action in ['optical', 'install', 'public-install', 'boot']:
        start(args.action, args.iso, args.uefi, args.disk)
    elif args.action == 'status':
        print(json.dumps(qmp('query-status')))
    elif args.action in ['stop', 'quit']:
        qmp('system_powerdown' if args.action == 'stop' else 'quit')
    elif args.action == 'key':
        qmp('human-monitor-command', {'command-line': 'sendkey ' + args.args[0]})
    elif args.action == 'click':
        x, y = map(int, args.args)
        if not (0 <= x < 1920 and 0 <= y < 1200):
            parser.error('Coordinates must be within the 1920x1200 test viewport')
        qmp('input-send-event', {'events': [{'type': 'abs', 'data': {'axis': axis, 'value': round(value / (size - 1) * 32767)}}
                                         for axis, value, size in [('x', x, 1920), ('y', y, 1200)]]})
        time.sleep(.12)
        qmp('input-send-event', {'events': [{'type': 'btn', 'data': {'down': True, 'button': 'left'}}]})
        time.sleep(.1)
        qmp('input-send-event', {'events': [{'type': 'btn', 'data': {'down': False, 'button': 'left'}}]})
    elif args.action == 'text':
        names = {' ': 'spc', '-': 'minus', '_': 'shift-minus', '.': 'dot', '/': 'slash',
                 ':': 'shift-semicolon', ';': 'semicolon', '=': 'equal', '+': 'shift-equal',
                 '@': 'shift-2', '\n': 'ret', "'": 'apostrophe', '"': 'shift-apostrophe',
                 '>': 'shift-dot', '<': 'shift-comma', '|': 'shift-backslash', '~': 'shift-grave',
                 '*': 'shift-8', '&': 'shift-7', '!': 'shift-1', '$': 'shift-4',
                 '(': 'shift-9', ')': 'shift-0', ',': 'comma', '?': 'shift-slash'}
        keys = []
        for char in args.args[0]:
            if char in names:
                keys.append(names[char])
            elif char.isascii() and char.isalnum():
                keys.append('shift-' + char.lower() if char.isupper() else char)
            else:
                parser.error('The native typing helper supports only mapped ASCII text')
        for key in keys:
            qmp('human-monitor-command', {'command-line': 'sendkey ' + key + ' 30'})
            time.sleep(.045)
    elif args.action == 'screenshot':
        path = Path(args.args[0]).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        sys.path.insert(0, str(ROOT / 'verification'))
        from rfb_capture import capture, png_bytes
        rgb, meta = capture(5922)
        path.write_bytes(png_bytes(meta['width'], meta['height'], rgb))
        print(path)
    elif args.action == 'ssh':
        sys.exit(subprocess.call(['ssh', '-i', str(LAB / 'id_ed25519'), '-p', '2224', '-o', 'BatchMode=yes',
                                  '-o', 'StrictHostKeyChecking=accept-new', '-o', f'UserKnownHostsFile={LAB / "known_hosts"}',
                                  '-o', 'ConnectTimeout=5', 'aven@127.0.0.1', *args.args]))


if __name__ == '__main__':
    main()
