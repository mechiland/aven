#!/usr/bin/python3
"""Install the scoped Aven profile after Anaconda deploys the exact Atomic tree."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import gi
gi.require_version('OSTree', '1.0')
from gi.repository import Gio, GLib, OSTree

MEDIA = Path('/run/install/repo/aven')


def run(*args):
    print('+', *args, flush=True)
    subprocess.run([str(arg) for arg in args], check=True)


def main():
    if os.getuid() != 0 or not (MEDIA / 'ostree/repo/config').is_file():
        raise RuntimeError('Run only from the Aven installer %post environment')
    platform = json.loads((MEDIA / 'source/iso/platform.json').read_text())
    ostree = platform['ostree']
    layer, base = ostree['layered_commit'], ostree['base_commit']
    roots = [path for path in [Path('/mnt/sysimage'), Path('/mnt/sysroot')]
             if (path / 'ostree/repo/config').is_file()]
    if not roots:
        raise RuntimeError('Anaconda physical OSTree root was not found')
    physical = roots[0]
    sysroot = OSTree.Sysroot.new(Gio.File.new_for_path(str(physical)))
    sysroot.load(None)
    deployments = [deployment for deployment in sysroot.get_deployments()
                   if deployment.get_osname() == 'fedora' and deployment.get_csum() == layer]
    if len(deployments) != 1:
        raise RuntimeError(f'Expected exactly one Aven deployment, found {deployments}')
    deployment = deployments[0]
    deployment_directory = Path(sysroot.get_deployment_directory(deployment).get_path())
    # Current Anaconda binds the deployment at /mnt/sysroot, then mounts /var,
    # /boot and API filesystems under that alias. Those child mounts do not
    # appear when traversing the original physical deployment directory.
    target = Path('/mnt/sysroot')
    if not target.is_dir() or not os.path.samefile(target, deployment_directory):
        raise RuntimeError('Anaconda system root does not match the exact selected deployment')
    var_mount = subprocess.run(['findmnt', '--mountpoint', str(target / 'var')],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not (target / 'var/lib').is_dir() or var_mount.returncode:
        raise RuntimeError('Anaconda must bind the deployment var before installing the profile')
    repo = physical / 'ostree/repo'
    # A pull of the layer alone does not import its base. rpm-ostree needs both.
    run('ostree', f'--repo={repo}', 'pull-local', '--untrusted', '--depth=0', MEDIA / 'ostree/repo', base)
    run('ostree', f'--repo={repo}', 'refs', '--force', '--create=' + ostree['origin'], base)
    origin = GLib.KeyFile()
    origin.set_string('origin', 'baserefspec', ostree['origin'])
    origin.set_string_list('packages', 'requested', ostree['requested_packages'])
    if not sysroot.write_origin_file(deployment, origin, None):
        raise RuntimeError('Could not preserve the rpm-ostree layering origin')
    # Use the signed Fedora update origin from the deployed tree.
    fedora_remote = target / 'etc/ostree/remotes.d/fedora.conf'
    expected_remote = target / 'usr/etc/ostree/remotes.d/fedora.conf'
    if not expected_remote.is_file():
        raise RuntimeError('The native Fedora update remote is missing')
    shutil.copy2(expected_remote, fedora_remote)
    run('chroot', target, 'ostree', 'show', '--gpg-verify-remote=fedora', base)
    # The original installer also seeds older Flatpak copies. Aven uses the
    # tested native Gwenview/Okular packages; remove only these duplicate apps.
    flatpaks = subprocess.check_output(['chroot', str(target), 'flatpak', 'list',
                                       '--system', '--app', '--columns=application'], text=True).splitlines()
    for app in ['org.kde.gwenview', 'org.kde.okular']:
        if app in flatpaks:
            run('chroot', target, 'flatpak', 'uninstall', '--system', '--noninteractive', '--assumeyes', app)
    destination = target / 'var/lib/aven/source'
    if destination.exists():
        raise RuntimeError('Refusing to replace an existing Aven source installation')
    shutil.copytree(MEDIA / 'source', destination)
    manifest = json.loads((MEDIA / 'source-manifest.json').read_text())
    for item in manifest['files']:
        path = destination / item['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise RuntimeError(f'Source copy checksum mismatch: {path}')
    run(sys.executable, destination / 'typography/install.py', '--root', target)
    for source, relative in [('aven-profile.sh', 'etc/xdg/plasma-workspace/env/aven-profile.sh'),
                             ('aven-layout.desktop', 'etc/xdg/autostart/aven-layout.desktop')]:
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination / 'iso' / source, path)
    run('chroot', target, 'systemctl', 'set-default', 'graphical.target')
    # Anaconda-created users need no second native first-user setup wizard.
    users = [line.split(':') for line in (target / 'etc/passwd').read_text().splitlines()]
    if any(1000 <= int(user[2]) < 60000 for user in users):
        (target / 'etc/plasma-setup-done').touch()
    record = {'schema_version': 1, 'installed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'platform': platform, 'source_manifest': manifest, 'deployment': deployment_directory.name,
              'profile': 'per-user first Plasma login', 'laboratory_profiles_copied': False}
    (target / 'var/lib/aven/installation.json').write_text(json.dumps(record, indent=2) + '\n')
    run('chroot', target, 'restorecon', '-RF', '/etc/fonts/conf.d', '/etc/xdg', '/var/lib/aven')
    print('Aven installation complete; Atomic Fedora origin and package layers preserved.', flush=True)


if __name__ == '__main__':
    main()
