# Offline Aven installer verification

This is an installer ISO based on Fedora's existing Anaconda media. It is not a
live desktop ISO, and a renamed QCOW2 does not satisfy the ISO contract.

## Exact payload identity

- Layer: `37fc46fea2b1059cdbc35c4ff88a2b40ede7fcc105cca76693f11cc4cdffd551`
- Signed Fedora base/parent: `be803f3e3bcdcc54885264702655e6e071864504154bc46044a08cc2aa2ce5df`
- Base version: `44.20260913.0`
- Persistent origin: `fedora:fedora/44/x86_64/kinoite`
- Requested packages: `glibc-langpack-zh`, `gwenview`, `okular`,
  `python3-pyside6`, `thunderbird`.

The layer is locally generated. Its Fedora parent has the verified Fedora 44
signature; do not describe the locally generated layer as signed by Fedora.

## Source findings

The official ISO SHA-256 is
`4a944312b4e861ab625fd9786957174ef122a8a406bbb54caba7665e0d9f0e92`.
Its BIOS and UEFI El Torito entries and hybrid GPT are present. The installer
runtime is `/images/install.img`, an XZ SquashFS containing Anaconda and the old
`/ostree/repo`. It need not be rebuilt merely to add the new offline repository.

The exact ISO's initrd `anaconda-diskroot` mounts optical media read-only at
`/run/install/repo`. `fetch-kickstart-disk` reads the chosen Kickstart from that
mount or a temporary read-only mount. Therefore these paths fit its existing
implementation:

```text
inst.stage2=hd:LABEL=<matching-ISO-label>
inst.ks=hd:LABEL=<matching-ISO-label>:/aven/aven.ks
ostreesetup --osname=fedora --remote=aven-install --url=file:///run/install/repo/aven/ostree/repo --ref=aven/44/x86_64/prototype --nogpg
```

The public Kickstart leaves disk selection, partitioning, and user creation to
Anaconda. It must not contain lab keys, lab users, automatic erasure, passwordless
sudo, or automatic login. The automated disposable-VM test Kickstart is separate.

The embedded Anaconda OSTree pull specifies the chosen ref and untrusted-object
validation, but no parent depth. Import the Fedora base explicitly in `%post`
even if the exported archive contains it. The old embedded repository is only a
local object cache; it does not replace the chosen URL. This agrees with the
public [Anaconda implementation](https://github.com/rhinstaller/anaconda/blob/main/pyanaconda/modules/payloads/payload/rpm_ostree/installation.py).

## Export and post-install origin

Run exports in a dedicated build directory, leaving the source repository intact:

```sh
ostree --repo="$aven_export_repo" init --mode=archive-z2
ostree --repo="$aven_export_repo" pull-local --untrusted --depth=1 \
  /sysroot/ostree/repo "$aven_layer"
ostree --repo="$aven_export_repo" refs --create=aven/44/x86_64/prototype "$aven_layer"
ostree --repo="$aven_export_repo" refs --create=fedora/44/x86_64/kinoite "$aven_base"
ostree --repo="$aven_export_repo" summary -u
ostree --repo="$aven_export_repo" fsck
```

Archive-mode promotion and limited history are standard
[OSTree repository operations](https://ostreedev.github.io/ostree/repository-management/).
Archive mode preserves the exact commits and SELinux metadata without copying the
mutable tested home or `/etc` into a new system tree.

In `%post --nochroot`, the default physical sysroot is `/mnt/sysimage` (also
confirmed by the completed stock install logs). Resolve the actual deployment
through `OSTree.Sysroot.get_deployment_directory`, as the embedded installer does:

```python
from gi.repository import Gio, GLib, OSTree
target = OSTree.Sysroot.new(Gio.File.new_for_path('/mnt/sysimage'))
target.load(None)
deployments = target.get_deployments()
assert len(deployments) == 1
deployment = deployments[0]
assert deployment.get_osname() == 'fedora'
assert deployment.get_csum() == aven_layer
deployment_path = target.get_deployment_directory(deployment).get_path()
```

The candidate-02 installation exposed an important distinction: Anaconda binds
the actual deployment at `/mnt/sysroot`, then mounts `/var`, `/run`, and `/boot`
under that alias. Those mounts are not visible through the original GI deployment
directory. The earlier source-only contract incorrectly treated the two paths as
interchangeable; the actual install corrected that assumption.

Require `os.path.samefile('/mnt/sysroot', deployment_path)`, then use
`/mnt/sysroot` for chroot, font installation, and source copying. Require
`findmnt --mountpoint /mnt/sysroot/var` to succeed before writing
`/mnt/sysroot/var/lib/aven/source`. Retain `/mnt/sysimage/ostree/repo` for repository
operations and the GI sysroot for the origin writer. This avoids copying into an
unmounted or incorrect `/var` when the user selects separate storage.

Install the two font rules beneath `/mnt/sysroot/etc`, and set up the first-user
profile using source-owned hooks. Do not copy the lab home. The system-account
guard must run before state-directory creation so Fedora Plasma Setup remains
untouched until it creates a normal user.

The unchanged installer runtime also imports old bundled Flatpak applications.
Remove only the system `org.kde.gwenview` and `org.kde.okular` duplicates during
the install, retaining the tested native layered applications. Do not use a
general all-app or unused-runtime cleanup. Verify the system application list
after installation; Atomic commit identity alone cannot detect `/var` Flatpaks.

Import the parent and point the Fedora tracking ref at the base, not the layer:

```sh
ostree --repo=/mnt/sysimage/ostree/repo pull-local --untrusted \
  /run/install/repo/aven/ostree/repo "$aven_base"
ostree --repo=/mnt/sysimage/ostree/repo refs --force \
  --create=fedora:fedora/44/x86_64/kinoite "$aven_base"
```

Write a fresh layered origin through the public API (confirmed present in the
tested guest); this avoids keeping Anaconda's temporary plain installer refspec:

```python
origin = GLib.KeyFile()
origin.set_string('origin', 'baserefspec', 'fedora:fedora/44/x86_64/kinoite')
origin.set_string_list('packages', 'requested', [
    'glibc-langpack-zh', 'gwenview', 'okular', 'python3-pyside6', 'thunderbird'])
assert target.write_origin_file(deployment, origin, None)
```

Preserve `/etc/ostree/remotes.d/fedora.conf` from the Fedora payload with its
HTTPS URL, keyring, and GPG verification. Do not replace it with the ISO's local
URL or disable Fedora update verification. Pinning the initial deployment keeps
the tested state available after an update. These post-install steps still need
to be exercised on a new disposable ISO installation; read-only source checks
alone do not establish success.

## Audits and required observations

`iso_audit.py media` accepts this manifest contract:

```json
{
  "iso": {"file": "Aven-x86_64.iso", "sha256": "full-file-SHA256"},
  "ostree": {
    "layered_commit": "exact-layer-above",
    "base_commit": "exact-base-above",
    "origin": "fedora:fedora/44/x86_64/kinoite",
    "requested_packages": ["glibc-langpack-zh", "gwenview", "okular", "python3-pyside6", "thunderbird"]
  },
  "paths": {"kickstart": "/aven/aven.ks", "repo": "/aven/ostree/repo", "source": "/aven/source.tar.gz"}
}
```

```sh
python3 verification/iso_audit.py media --manifest output/ISO-MANIFEST.json \
  --iso output/Aven-x86_64.iso --output evidence/verification/iso-media-audit.json
python3 verification/iso_audit.py installed --ssh-host aven@127.0.0.1 \
  --ssh-port 2224 --identity .cache/iso-test/id_ed25519 \
  --known-hosts .cache/iso-test/known_hosts \
  --output evidence/verification/iso-installed-audit.json
```

The installed audit streams a read-only root probe; it does not copy files to the
guest, change the desktop, update, or reboot. Atomic identity and desktop startup
are reported separately. Startup requires the native Plasma Login Manager to be
loaded, active and enabled, the graphical default target, and no system Gwenview
or Okular Flatpak duplicates. This does not establish first-login visual success.
The earlier identity-only probe passed against the existing tested Aven guest at
`evidence/verification/iso-probe-existing-aven.json`; that is not ISO installation
evidence.

Release acceptance also needs these actual observations:

1. Boot the finished ISO through firmware from the optical image, with no direct
   `-kernel`/`-initrd` bypass. Confirm the public Anaconda UI appears and leaves
   disk/user decisions available. Record BIOS and UEFI separately; do not infer
   either boot mode or Secure Boot from the presence of boot catalog entries.
2. Install to a fresh disposable disk with network disconnected. Complete both
   `%post` and the first-login profile without downloading required packages.
   A separate automated test Kickstart may supply disposable lab access.
3. Eject the ISO and boot the installed disk. Run the Atomic identity audit and
   record the first-user profile completion marker/log. Check native app launches,
   default handlers, preview, SC/TC text, and genuine screenshots from this new
   installation. The previously tested VM does not substitute for this check.
4. Reboot once more; confirm the profile is not reapplied and remains usable.
   No live rollback or hardware/Secure Boot support is claimed until exercised.
5. Record the complete ISO SHA-256 and test/release manifest. If asset size forces
   splitting, publish exact reassembly instructions and the complete ISO hash;
   fragments must not be described as individually bootable ISO images.
