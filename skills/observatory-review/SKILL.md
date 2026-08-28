---
name: observatory-review
description: Run the provider-neutral “Review my brain” queue without silently changing trust.
---

# Review my Observatory

Use this workflow to present a prioritized review queue. It is read-only until the owner chooses an explicit action.

## Modes and selection

- **combined** (default): mix the highest-priority eligible items from all other modes.
- **unverified**: canonical documents with no `verified` event.
- **staged**: Git-tracked candidate Markdown under `staging/`.
- **stale**: canonical documents whose `stale_after` date is today or earlier.
- **disputed**: documents that explicitly record conflicting evidence, a dispute, or unresolved disagreement; never infer a dispute merely from missing verification.

Return 7 cards by default (the owner may request another count). Deduplicate cards by path. Rank actionable disputes first, then staged candidates, stale material, and unverified material; within a tier prefer active-project relevance, greater consequence, and then oldest freshness date. Use the repository path as the deterministic final tie-breaker. A mode-specific request filters rather than merely reorders the queue.

## Derived review state

Derive, but do not persist, the displayed state from OKF metadata:

- **unverified**: no valid `verified` event;
- **machine-confirmed**: at least one valid verification event exists, but none has an actor beginning `human:`;
- **human-reviewed**: at least one valid verification event has an actor beginning `human:`.

`generated`, `status`, source count, praise, liking, a thumbs-up, and save requests do not change review state. Freshness and dispute status are separate from verification.

## Review cards and actions

Each card includes title and path, selection reason, derived review state, provenance/evidence summary, freshness or dispute details, relevant project connections, and one recommended next action. Never expose secrets or reproduce unnecessary personal data from a candidate.

Offer explicit actions for each card:

- **Approve/edit content**: apply the specified content edit while preserving metadata; approval alone adds no verification event.
- **Verify this**: run `skills/source-verification/SKILL.md`; record only the verification event actually performed.
- **Refresh**: research current primary sources and propose an attributable update without implying verification beyond the checks performed.
- **Brain this**: promote a staged candidate through the ingest workflow; preserve provenance and remove or archive the staged copy only with explicit owner approval.
- **Keep staged**, **defer**, or **dismiss from this batch**: leave canonical knowledge and trust unchanged.

Before any write, restate the chosen card and action when the request is ambiguous. Never interpret praise, liking, a thumbs-up, “save this,” or ordinary approval as human verification. Only an explicit human request to record their completed review may create a `human:*` verification event.
