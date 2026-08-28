# Walkthrough build tools

This directory reproduces the public synthetic product walkthrough from the actual sanitized Mission Control UI. It never uses a personal dashboard, private screenshot, or hosted speech service.

Requirements are Node.js 22.12+, Python 3.12+, FFmpeg/ffprobe, and local Kokoro model and voice assets. Playwright is locked by `package-lock.json`; Kokoro and its transitive Python dependencies are hash-locked by `requirements-kokoro.txt`.

Run from the repository root:

```sh
.venv/bin/python scripts/demo/build-walkthrough.py \
  --model /path/to/kokoro-v1.0.int8.onnx \
  --voices /path/to/voices-v1.0.bin
```

Watch the derived MP4 with audio and inspect every file under `.derived/demo-output/review-frames/`. Publish only that reviewed output:

```sh
.venv/bin/python scripts/demo/build-walkthrough.py \
  --model /path/to/kokoro-v1.0.int8.onnx \
  --voices /path/to/voices-v1.0.bin \
  --denylist /private/path/public-release-denylist.txt \
  --publish-reviewed
```

The first command leaves MP4/GIF output under `.derived/demo-output/`. `--publish-reviewed` does not recapture; it re-verifies and denylist-scans those reviewed files before replacing checked-in media and writing `docs/media/observatory-overview-manifest.json`.

The builder checks deterministic properties, not human judgment. Before commit, watch the complete MP4 with audio, inspect `.derived/demo-output/review-frames/`, run the repository-specific private denylist and Gitleaks audits, and confirm that the narration makes no unsupported claim.
