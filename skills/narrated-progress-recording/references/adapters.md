# Recording adapters

Choose by what the user needs to understand, not by which recorder happens to
be installed.

## iOS or Android app

Use a deterministic UI flow when available (for example Maestro), then capture
the simulator/emulator or device. Verify the recorder is attached to the same
runtime that executed the smoke test. On macOS, Homebrew may install Maestro's
launcher under `~/.maestro/bin` without adding that directory to a non-login
agent shell; test that exact path before declaring Maestro absent.

## Web app or dashboard

Use the project's browser automation for the repeatable path and a local browser
or screen recorder for the final capture. Start from a known local URL and seed
state. Hide developer credentials, personal browser chrome, unrelated tabs, and
private records.

## Data or operational workflow

Prefer a sanitized terminal capture, generated report, screenshots, or a small
slide sequence. Show inputs, transformation, validation, and result. Replace
private data with labeled fixtures and disclose that substitution.

## Audio, transcript, and packaging

Prefer an already-proven local text-to-speech setup such as Kokoro and an
existing `ffmpeg` installation. If those are unavailable, deliver the verified
scene plan and transcript before considering any external service. Include a
plain-text transcript and WebVTT captions beside the video when practical.

## Quality gate

Watch the exported file end to end. Confirm its reported duration, resolution,
audio stream, captions/transcript, and a SHA-256 hash. A successful export
command alone is not visual or narrative QA.
