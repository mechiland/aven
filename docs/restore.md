# Restoring the focused Aven profile

`verification/restore_profile.py` restores the settings Aven changes. It preserves
Firefox and Thunderbird profiles, mail, bookmarks, photos, documents, application
binaries, and the Fedora Atomic deployment. It never runs `rpm-ostree`, edits
`/usr`, removes packages, or closes applications.

The current prototype has incomplete original-state records for some early Files
installations. A later backup is not automatically a stock backup. The independent
stock VM remains the exact baseline; this helper does not silently copy its files
over the Aven home. Unresolved original states remain explicit in the output.

## Complete snapshot for a future installation

Run this **before** installing Aven in a fresh home:

```sh
python3 verification/restore_profile.py snapshot --home "$HOME"
```

The printed directory under `.local/state/aven/focused-before-*` records original
file hashes, symlinks, and absent paths. It covers shared Plasma/GTK settings,
Dolphin settings and folder metadata, Gwenview settings, Aven launchers, and
default application associations. It does not include browser or mail profiles.
Creating this snapshot after installation records the current state, not stock.

## Plan and apply a settings restore

Select the exact snapshot you intend to restore:

```sh
python3 verification/restore_profile.py restore --home "$HOME" \
  --snapshot "$HOME/.local/state/aven/focused-before-TIMESTAMP"
```

The default command only prints a plan. Review `operations`, `unresolved`, and
`warnings`. To apply it, log out of Plasma and close the four applications, then
run the same command with `--apply` from SSH or a text console as the home owner.
The helper refuses a live desktop restore because running applications can write
their old settings back over restored files. It does not kill processes.

Every changed file is archived first under `.local/state/aven/restores/*`.
`restore-result.json` records completed writes, including partial failure.
Regular-file replacements are atomic and verified against their planned hashes.
To undo, choose the printed `undo_archive` with `restore --snapshot` in the same
way. Existing snapshots are never overwritten.

MIME association restoration changes only the types Aven configures. New,
unrelated associations remain. Places restoration changes only the hidden flags
for the original Desktop, Music, Videos, and Recent Locations system entries;
custom bookmarks remain. Other saved configuration files return to their chosen
snapshot contents; their current contents remain in the undo archive.

For system-device visibility, select each immutable record created by the Files
installer when it actually changed an entry:

```sh
python3 verification/restore_profile.py restore --home "$HOME" \
  --snapshot "$HOME/.local/state/aven/focused-before-TIMESTAMP" \
  --places-record "$HOME/.local/state/aven/places/ACTUAL-RECORD.json"
```

Repeat `--places-record` for multiple relevant installations. The plan reports
each record's hash. Only recorded device flags still set to Aven's applied value
are eligible; UUID identifies a disk before its reusable kernel device name.
Explicit later visibility choices, removable devices, unknown entries, custom
bookmarks, and added metadata remain. Ambiguous identities are unresolved.
Native device metadata remains when its hidden flag is removed.

Older round-03 device changes lack durable ownership records. Their hidden flags
remain without an actual-change record; a snapshot difference alone does not
establish Aven ownership. No retrospective record is invented. An unchanged
post-restore Places file can be undone byte exactly from the recovery archive.
If bookmarks changed after restoration, the helper retains those changes and
reports device-flag undo for manual review instead of replacing the whole file.

## Existing installer backups

For the current installer, select each applicable backup explicitly:

```sh
python3 verification/restore_profile.py restore --home "$HOME" \
  --shared-backup "$HOME/.local/state/aven/TIMESTAMP" \
  --defaults-backup "$HOME/.local/state/aven/profile-defaults-TIMESTAMP" \
  --photos-backup "$HOME/.config/gwenviewrc.pre-aven-TIMESTAMP"
```

New shared/default manifests record actual copied paths, original absence, and
hashes. Earlier shared manifests may list files that were never copied; those
entries remain unresolved. Files `.pre-aven` backups and the explicitly selected
Gwenview backup have no historical hashes or original-absence records. A rerun
may have backed up an already modified file. Choose timestamps using installation
records; the helper does not guess which one represents stock.

Unrecorded Aven launchers and markers remain installed under this legacy route.
Installed visual assets and preview code also remain. Restored defaults select
the prior applications, and restored theme configuration selects prior surfaces.
Browser and mail data remain available in `.local/share/aven/` throughout.

## Font rules

The font installer changes two named files in `/etc/fonts/conf.d`. Plan disabling
only the recognized Aven-owned rules inside the Atomic guest:

```sh
sudo python3 verification/restore_profile.py fonts --root /
```

Add `--apply` after reviewing the plan. A file is removed only when its XML
description identifies it as Aven-owned. If a known pre-install file existed,
restore that exact backup instead:

```sh
sudo python3 verification/restore_profile.py fonts --root / \
  --backup '60-aven-families.conf=/etc/fonts/conf.d/60-aven-families.conf.pre-aven-TIMESTAMP'
```

Each font change is archived under `/var/lib/aven/font-restores/*`; undo with
`fonts --root / --snapshot ARCHIVE --apply`. Existing applications must restart
to pick up restored font rules. Disabling rules alone does not reconstruct any
unknown pre-install contents or remove the installed font packages.

## Atomic rollback and validation limits

Fedora deployment rollback is separate from restoring mutable home settings.
This helper leaves deployments and their rollback entries intact. The
[rpm-ostree administrator handbook](https://coreos.github.io/rpm-ostree/administrator-handbook/)
documents deployment inspection and `rpm-ostree rollback`; the
[project overview](https://coreos.github.io/rpm-ostree/)
explains the distinction between the operating-system tree and mutable data.
Use those deployment controls separately when an OS/package change needs reversal.

Exit status is `0` for a complete scoped plan/apply, `2` when original states
remain unresolved, and `1` for an error. A partial legacy restore is not an exact
return to stock.

Validation performed: temporary-home snapshot/restore/undo; preservation of mail,
Firefox data, custom bookmarks, and unrelated MIME entries; missing-state and
hash-tamper rejection; symlink-parent rejection; offline font disable/undo; and
canonical home-path handling for Kinoite's `/home` to `/var/home` link. No live
desktop restore or Atomic deployment rollback has been exercised yet. Native
post-restore appearance and application behavior remain pending.

Fourteen focused offline Places tests additionally cover exact recorded device
ownership, UUID reuse and renaming, explicit visibility, ambiguous entries,
custom bookmarks, record rejection, and restore/undo with subsequent user edits.
