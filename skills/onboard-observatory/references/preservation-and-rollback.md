# Preservation and rollback

Use this reference when an approved onboarding plan may change an existing rule, configuration, Markdown, JSON, or owner document.

## Define the rollback boundary

Inventory the exact files that may change. Include root and nested agent instructions, provider settings, global rule files, and non-Git documents only when the owner explicitly placed them in scope. Exclude secrets and unrelated files unless the owner separately authorizes their exact source and private backup destination.

Explain what can be restored from file copies and what cannot. File preservation does not reverse messages, uploads, permission changes, external service state, database mutations, credential rotation, or other side effects.

## Snapshot before writing

1. Obtain explicit approval for the exact source list and a private local destination outside public/shared repositories. Treat cloud-synced destinations as external disclosure unless the owner approves them.
2. Create a new non-overwriting snapshot directory with restrictive access where supported.
3. Copy each regular file byte-for-byte without following unexpected symbolic links. Preserve its filename, mode, and timestamps when practical.
4. Write a local manifest containing the original absolute path, snapshot-relative path, byte size, mode, modification time, SHA-256, and Git repository/commit/blob identity when available.
5. Hash every backup copy independently and compare it with the source. A missing file, read failure, copy failure, symlink ambiguity, or hash mismatch blocks the corresponding source write.
6. Show the owner the snapshot location, covered files, verification result, and exclusions before integration begins.

Never commit the snapshot or its manifest. Paths and backed-up content may reveal private information even when the files contain no credentials.

## Integrate and verify

- Modify only files listed in the approved packet and verified manifest.
- Record post-change hashes and the exact validation performed.
- Stop on an unapproved target, changed source, new conflict, or expanded scope; refresh the packet and approval rather than silently extending it.
- Keep the snapshot until the owner accepts the integration and retention decision.

## Roll back safely

Rollback is a separate write operation. Present the exact restore targets, current-versus-snapshot hashes, expected effects, and validation plan; obtain explicit approval before overwriting current files.

Restore only manifested files, preserve any unrelated new files, and verify restored hashes against the manifest. Re-run the affected agent/provider checks after restoration. Report any state that could not be reversed, and never describe rollback as complete until every in-scope hash and required validation passes.
