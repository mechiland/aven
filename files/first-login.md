# Finalize Places after native initialization

Headless profile seeding can run before KDE creates `~/.local/share/user-places.xbel`.
`files/install.py` intentionally leaves missing native bookmarks alone. First-login
integration must finish this step after Plasma's session bus and native Places
model are running, before writing its successful completion marker:

```sh
python3 files/finalize-places.py --timeout 30
```

Run as the desktop user. `--home /path` is available for an explicit target home.
The command prints JSON; exit **0** and `complete: true` mean configuration
finished. Exit **75** means readiness timed out; exit **1** means a permanent
refusal or write failure. The caller must check the exit code and leave its
completion marker absent on failure. No full profile reapplication is needed.

The command waits for an existing, parseable XBEL bookmark list. It never creates
one, launches an application, or replaces a symlink. On an Atomic system, a
successful Solid inventory must include the read-only overlay root and every
mounted system block entry, with typed drive properties. Two consecutive complete
classifications must agree before applying defaults. Each inventory subprocess
shares a bounded remaining timeout; the default total readiness budget is 30 s.

The existing `configure_places` writer makes the same narrowly scoped changes as
normal installation and creates its usual immutable ownership record. Explicit
`IsHidden=false`, custom bookmarks, removable disks and user-data volumes remain
unchanged. A second invocation succeeds without another write or ownership record.
In particular Fedora's shared `/var/home` volume remains visible; hiding all
Storage Devices would be a different policy.

KDE's [KBookmarkManager](https://github.com/KDE/kbookmarks/blob/v6.30.0/src/kbookmarkmanager.cpp)
watches its native XBEL file and notifies models when it changes. First-login
runtime verification must still inspect a fresh Dolphin window and subsequent
reboot, since native model initialization and bookmark writes happen asynchronously.

Regression checks:

```sh
python3 -m unittest discover -s files/tests -p 'test_*.py'
```

Coverage includes delayed native creation, complete versus partial device
inventories, transient discovery failures, bounded timeout without file creation,
malformed native data, symlink refusal, explicit visible choices and idempotence.
