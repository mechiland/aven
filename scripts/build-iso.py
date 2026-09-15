#!/usr/bin/env python3
"""Remaster the verified official Kinoite installer with an offline Aven payload."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    return subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--official', type=Path, default=ROOT / '.cache/downloads/Fedora-Kinoite-ostree-x86_64-44-1.7.iso')
    parser.add_argument('--repo', required=True, type=Path, help='Exported archive-mode OSTree repository with layer and signed base')
    parser.add_argument('--output', type=Path, default=ROOT / 'output/Aven-Atomic-KDE-44-0.1.0-prototype-x86_64.iso')
    parser.add_argument('--tools', type=Path, help='Optional directory containing mcopy, implantisomd5 and checkisomd5')
    args = parser.parse_args()
    if args.tools:
        os.environ['PATH'] = str(args.tools.resolve()) + os.pathsep + os.environ['PATH']
    for name in ['xorriso', 'mcopy', 'implantisomd5', 'checkisomd5']:
        if not shutil.which(name):
            parser.error(f'Missing build tool: {name}')
    platform = json.loads((ROOT / 'iso/platform.json').read_text())
    if digest(args.official) != platform['official_iso']['sha256']:
        parser.error('Official Fedora ISO does not match its verified checksum')
    repo = args.repo.resolve()
    if not (repo / 'config').is_file() or 'mode=archive' not in (repo / 'config').read_text():
        parser.error('The offline OSTree repository must use archive mode')
    ref = repo / 'refs/heads' / platform['ostree']['installer_ref']
    if ref.read_text().strip() != platform['ostree']['layered_commit']:
        parser.error('The installer ref must resolve to the exact tested layer')
    for commit in [platform['ostree']['layered_commit'], platform['ostree']['base_commit']]:
        if not (repo / 'objects' / commit[:2] / (commit[2:] + '.commit')).is_file():
            parser.error(f'Missing commit: {commit}')
    output = args.output.resolve()
    if output.exists():
        parser.error(f'Refusing to overwrite {output}; choose a new candidate output')
    output.parent.mkdir(parents=True, exist_ok=True)
    work = ROOT / '.cache/iso-build' / output.stem
    work.mkdir(parents=True, exist_ok=True)
    media = work / 'aven'
    source = media / 'source'
    if source.exists():
        shutil.rmtree(source)
    source.mkdir(parents=True)
    for name in ['typography', 'visual', 'files', 'preview', 'browser', 'mail', 'photos', 'fixtures', 'integration', 'verification', 'iso']:
        shutil.copytree(ROOT / name, source / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    files = [{'path': str(path.relative_to(source)), 'sha256': digest(path), 'bytes': path.stat().st_size}
             for path in sorted(source.rglob('*')) if path.is_file()]
    source_manifest = {'schema_version': 1,
                       'base_git_commit': run('git', '-C', ROOT, 'rev-parse', 'HEAD', capture_output=True, text=True).stdout.strip(),
                       'source_worktree_dirty': bool(run('git', '-C', ROOT, 'status', '--porcelain', '--', 'iso', 'integration', 'typography', 'visual', 'files', 'preview', 'browser', 'mail', 'photos', 'fixtures', 'verification', capture_output=True, text=True).stdout.strip()),
                       'files': files}
    (media / 'source-manifest.json').write_text(json.dumps(source_manifest, indent=2) + '\n')
    shutil.copy2(ROOT / 'iso/aven.ks', media / 'aven.ks')
    for iso_path, name in [('/EFI/BOOT/grub.cfg', 'efi.cfg'), ('/boot/grub2/grub.cfg', 'bios.cfg')]:
        run('xorriso', '-osirrox', 'on', '-overwrite', 'on', '-indev', args.official, '-extract', iso_path, work / name)
        text = (work / name).read_text().replace('Install Fedora 44', 'Install Aven Atomic KDE 44').replace('install Fedora 44', 'install Aven Atomic KDE 44')
        text = text.replace('set timeout=60', 'set timeout=15')
        label = platform['official_iso']['volume_id']
        text = '\n'.join(line + f' inst.ks=hd:LABEL={label}:/aven/aven.ks'
                         if line.lstrip().startswith('linux ') and 'inst.rescue' not in line else line
                         for line in text.splitlines()) + '\n'
        (work / name).write_text(text)
    # Fedora stores another GRUB config in its appended EFI FAT partition.
    report = run('xorriso', '-indev', args.official, '-report_el_torito', 'plain', capture_output=True, text=True)
    match = re.search(r'El Torito boot img\s*:\s*2\s+UEFI\s+y\s+none\s+\S+\s+\S+\s+(\d+)\s+(\d+)', report.stdout + report.stderr)
    if not match:
        raise RuntimeError('Official ISO EFI boot image layout was not recognized')
    sectors, lba = map(int, match.groups())
    efi = work / 'efiboot.img'
    with args.official.open('rb') as stream:
        stream.seek(lba * 2048)
        efi.write_bytes(stream.read(sectors * 512))
    for name in ['grub.cfg', 'BOOT.conf']:
        run('mcopy', '-o', '-i', efi, work / 'efi.cfg', '::/EFI/BOOT/' + name)
    run('xorriso', '-indev', args.official, '-outdev', output,
        '-boot_image', 'any', 'replay',
        '-append_partition', '2', '28732ac11ff8d211ba4b00a0c93ec93b', efi,
        '-map', media, '/aven', '-map', repo, '/aven/ostree/repo',
        '-map', work / 'efi.cfg', '/EFI/BOOT/grub.cfg',
        '-map', work / 'bios.cfg', '/boot/grub2/grub.cfg',
        '-volid', platform['official_iso']['volume_id'], '-commit', '-end')
    run('implantisomd5', '--force', output)
    run('checkisomd5', output)
    manifest = platform | {'built_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          'iso': {'file': output.name, 'sha256': digest(output), 'bytes': output.stat().st_size},
                          'paths': {'kickstart': '/aven/aven.ks', 'repo': '/aven/ostree/repo', 'source': '/aven/source'},
                          'source_manifest': source_manifest, 'boot_install_verified': False}
    output.with_suffix('.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'iso': str(output), 'sha256': manifest['iso']['sha256'], 'bytes': output.stat().st_size}, indent=2))


if __name__ == '__main__':
    main()
