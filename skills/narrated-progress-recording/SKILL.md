---
name: narrated-progress-recording
description: Plan, capture, narrate, verify, and log a truthful progress recording for an app sprint, dashboard, workflow, or other demonstrable project. Use at major app-sprint checkpoints and whenever the owner asks for a narrated demo, walkthrough, progress video, or recording.
---

# Narrated progress recording

Create a concise, reproducible account of what the verified product can do at
one exact source revision. A recording is communication evidence, not proof that
untested behavior works.

## Trigger and status

- At every major app-development checkpoint, add a recording status to the
  project handoff: `produced`, `deferred`, or `not applicable`, with a reason.
- Produce media when the owner requests it or a project has an explicit standing
  recording policy. Do not spend model/provider credits merely because a sprint
  ended.
- For dashboards, data workflows, and non-app work, activate this skill when the
  owner asks for a recording, walkthrough, or narrated update.

## Workflow

1. Read the project status/handoff and inspect the exact branch or commit.
2. Run the relevant smoke tests. Build the narration only from behavior actually
   observed on that revision; label limitations and simulated data plainly.
3. Select the smallest adapter in
   [`references/adapters.md`](references/adapters.md). Reuse a project-owned
   recording script when one exists.
4. Draft a short scene plan: setup, user-visible change, one important edge or
   privacy behavior, verification result, and next step. Keep secrets, personal
   data, file paths, notifications, tokens, and unrelated apps out of frame and
   narration.
5. Capture locally when practical. Prefer local speech synthesis and local media
   tools; do not upload private screenshots, video, source, or narration to an
   external service without exact user authorization for that data and service.
6. Review the complete output with audio enabled. Confirm intelligibility,
   captions/transcript alignment, no unsupported claim, no private leakage, and
   no stale footage from another revision.
7. Store the artifact only in the project-approved location. Record commit,
   commands/tests, adapter, duration, transcript/caption paths, artifact hash,
   limitations, and distribution status in the project handoff or demo log.
8. Never publish, message, email, or upload the recording without explicit
   destination authorization.

## Required deliverables

- recording file or a clearly logged deferral;
- narration script or transcript;
- captions when the format supports them;
- exact commit and validation evidence;
- privacy review and artifact hash;
- reproduction instructions sufficient for another agent to update it.

## Failure behavior

If the chosen capture tool is unavailable, preserve the script and scene plan,
try another local adapter, and log the missing dependency. Do not fabricate
footage, claim a smoke test ran when it did not, or weaken privacy boundaries to
finish a recording.
