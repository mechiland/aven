# Native Places ownership records

Each successful `configure_places` call that changes visibility publishes one new JSON record in `~/.local/state/aven/places/`. The filename is a UTC timestamp plus a unique suffix. Existing records are never rewritten; each is created exclusively with owner-read-only permissions. No-change calls produce no record.

The output's `ownership_record` field identifies the new record or is null. Records accumulate across installations, so a later no-change install cannot erase the evidence of an earlier change.

## Schema version 1

- `schema_version`: `1`
- `component`: `aven-places`
- `created_at`: UTC ISO timestamp
- `target`: `.local/share/user-places.xbel`
- `before_sha256`, `after_sha256`: hashes of the complete actual XBEL before and after this call
- `changes`: only entries whose `IsHidden` value this call changed

Each change contains:

- `kind`: `system-device` or `system-bookmark`
- `identifiers`: actual modified entry identifiers. A device contains `udi` and `uuid`; a bookmark contains `href`, `title`, and native `id`. An existing device can retain an older UDI while matching the discovered device's UUID, so records deliberately use the entry's actual UDI.
- `previous_is_hidden`: `{ "present": false, "value": null }` for the current default operation. Existing explicit flags, including `false`, are preserved and generate no change record.
- `applied_is_hidden`: `true` as the native string value
- `entry_created`: whether this call created the native device separator; existing bookmarks and device separators are false

No record is inferred merely because a device is currently hidden. Existing hidden entries from installations predating this logging remain unclaimed.

## Publication and restoration

The record is prepared and synced before an atomic XBEL replacement. It is published as `.json` only after that replacement succeeds. Publication failure rolls back the exact XBEL bytes written by this call. The final record and its directory are synced before returning success.

An interrupted process can leave a `.pending` file. That file is **not committed ownership evidence** and is not automatically promoted. Restore tools must accept only finalized `.json` records with the expected schema, component and target.

For devices, restore must prefer a recorded nonempty UUID over UDI, preserve an explicit current `IsHidden=false`, and reverse only the recorded `true` transition. A missing or unknown device is not grounds for changing another entry. Removing the owned `IsHidden` flag preserves native device discovery and any later custom metadata.

The Files tests cover cumulative/exclusive records, no-change behavior, actual UUID-matched identifiers, preservation of explicit visible choices, and rollback on a failed record publication. These records change restoration metadata; they do not change installed visual defaults.
