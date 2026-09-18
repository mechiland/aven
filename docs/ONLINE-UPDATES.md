# Install and update Aven without an ISO

Aven can be added to an installed **Fedora Kinoite 44, x86_64** system. The
installer keeps the Fedora Atomic origin and uses `rpm-ostree` for missing
system dependencies. The initial Union installation also stages the tested
Plasma 6.8 Beta package set. Fedora Workstation, mutable Fedora KDE, other Fedora
releases and other architectures are not supported by this first updater.

The updater distributes Aven separately from Fedora. Appearance and integration
changes use small signed component archives; unchanged archives are reused from
the local cache. No ISO is built or downloaded by this workflow. System packages
are larger and are needed during initial setup or an explicit platform change.

## Install

Download `Aven-Installer.tar.gz` from the
[Kinoite 44 update channel](https://github.com/mechiland/aven/releases/tag/aven-kinoite-44).
The installer contains a Python client and its pinned release public key. Check
the published SHA-256 checksum before extracting. Run these commands in Konsole
as your normal desktop user, with Files, Firefox, Thunderbird, Photos and Preview
closed:

```sh
tar -xzf Aven-Installer.tar.gz
python3 aven-installer/aven.py install
```

Do not run the installer itself with `sudo`. It requests elevated permissions
only for Fedora package transactions and the two Aven fontconfig rules. If it
stages dependencies, it exits with code 10 and asks for a reboot. After rebooting,
finish from Konsole with:

```sh
~/.local/bin/aven update
```

The completed installation asks you to log out and back in so existing desktop
processes load the new assets. Later logins normally include `~/.local/bin` in
PATH, so the shorter `aven` command works too.

For an existing Aven ISO installation, use the same installer. It recognizes the
existing Aven browser profile, retains accounts and settings, and adopts the
installation into the component update channel. It does not reinstall Fedora.

## Routine updates

```sh
aven check                  # available version, changed components, download size
aven update --download-only # verify and cache the release without applying it
aven update                 # close focused apps before applying
aven status                 # installed version and recovery state
```

`aven update` refreshes Aven theme assets, Preview code, browser/mail chrome and
native launch integration. **It preserves existing app preferences, panel
layout, pinned apps, folder views, toolbar customization and application data.**
Initial defaults belong to the user once installed. To deliberately reapply the
current release's layout and defaults, use `aven update --reset-defaults`; this
is an explicit reset and should not be used for ordinary updates.

Fedora system/security updates remain in Discover or `rpm-ostree upgrade`.
Aven does not replace their update mechanism. Because Union currently uses
locally pinned Beta replacements, compatibility with future Fedora/Plasma
versions must be verified before expanding the supported platform. The updater
checks the tested Dolphin, Firefox, Thunderbird, Gwenview and Qt series before
applying; it fails without applying Aven if those versions are incompatible.

## Failure recovery and rollback

Downloads are authenticated before extraction or execution. A failed download
does not change installed files. An interrupted application leaves an explicit
journal and does not report the new version as installed. Retry recovery before
starting another update:

```sh
aven recover
```

For recovery or rollback, close the apps and log out of Plasma, then use a text
console (Ctrl+Alt+F3) or SSH. This prevents running applications and Plasma from
writing their cached configuration over restored files.

```sh
aven rollback
```

Rollback restores the preceding Aven assets and the settings actually changed
by that update. It checks for subsequent edits before writing and reports
conflicts instead of silently overwriting them. Mail messages, bookmarks,
documents and photos are never included in the recovery payload. Preference
files, including account settings, are backed up privately; mail stores,
browser databases and password databases are not. Ordinary updates leave those
account preferences unchanged. This is **Aven profile recovery**, separate from `rpm-ostree rollback` for
the Fedora deployment and platform packages.

Installation state lives in `~/.local/state/aven/updates/`; downloads and verified
source versions live in `~/.local/share/aven/updater/`. Keep the transaction
snapshots and the previous source version if you want to retain rollback.

## Release a small change

The publisher's RSA signing key is stored outside the repository. Never include
the private key in an installer, artifact, commit or website. Keep an offline
backup: clients pin the public key and reject a replacement key.

```sh
python3 updates/build.py \
  --key /secure/path/aven-release.pem \
  --version 0.4.1 --sequence 2 \
  --output output/updates-0.4.1 \
  --platform-cache /path/to/verified/union-rpms \
  --asset-base https://github.com/mechiland/aven/releases/download/aven-kinoite-44

python3 updates/publish.py --directory output/updates-0.4.1
python3 updates/publish.py --directory output/updates-0.4.1 --publish
```

The first publication also needs `--notes docs/releases/v0.4.0-updates.md`.
The build is a component packaging operation, not an OS compose. Component
archives are deterministic. Their names include SHA-256, so unchanged components
keep the same identity. Publishing reuses existing immutable objects, uploads
new objects first, and activates the signed channel manifest last. The fixed
channel release is a prerelease and does not replace the latest ISO release.

Always use a new, increasing sequence, including for manifest renewal. Signed
metadata expires after 90 days; refresh it before expiry. Clients reject expired
metadata, decreasing sequences and changed contents under the same sequence.
Local rollback is available even when the network/channel is unavailable.

For a private/offline mirror, put all artifacts in one directory and supply
`--channel file:///absolute/path/channel.json --key /path/to/release.pub` during
the first installation. Remote channels must use HTTPS; insecure HTTP and
HTTPS-to-HTTP redirects are rejected. A configured installation cannot silently
switch channels or signing keys.

## Verification

```sh
python3 -m unittest discover -s updates/tests -v
python3 -m unittest discover -s files/tests -v
python3 -m unittest discover -s verification/tests -v
```

Native installation/upgrade evidence is recorded under
`evidence/verification/online-updates/`. This release changes distribution and
updating, and does not assign new visual scores to Union. Visual acceptance
remains separate from installation/update acceptance.
