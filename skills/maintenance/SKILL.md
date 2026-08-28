---
name: maintenance
description: Maintain corpus quality without destructive or schema-losing edits.
---

# Maintenance procedure

Check duplicate subjects, broken links, orphans, inconsistent names, unsupported claims, lifecycle freshness, and navigation maps. Prefer proposed merges over deletion. Preserve unknown fields and provenance byte-for-byte where practical. Never silently upgrade trust. Run `.venv/bin/observatory preserve <base-ref>` before publication; intentional destructive changes require a scoped human approval record. Keep generated indexes outside canonical directories and reproducible. Validate and submit all autonomous changes for review.
