# Observatory walkthrough media

`observatory-overview.mp4` is the public synthetic product walkthrough pinned in the root README. It was captured from the actual sanitized Mission Control UI; it does not use a personal Observatory, private screenshot, or external media service.

## Artifact contract

- adapter: Playwright 1.62.1 against local Mission Control, Kokoro ONNX 0.4.9 with the `af_heart` voice, FFmpeg 9.0.1;
- display: 1280×720, 30 fps, H.264 video, AAC narration, embedded English captions;
- duration: approximately 64.7 seconds;
- source data: generic `mission-control/config/seed.json` and synthetic canonical examples;
- walkthrough: Overview → Atlas interaction → Explore → skill search → uninitialized Personal Operating Model → closing message;
- sidecars: `observatory-overview-script.txt` and `observatory-overview.vtt`;
- README preview: `observatory-overview-readme.gif` at 640×360;
- provenance: `observatory-overview-manifest.json` records artifact hashes and a deterministic digest of the exact source-input tree. The private release log records the later public merge commit so the manifest does not create a self-referential commit hash.

The release audit records the final SHA-256 hashes and exact public commit. Recompute locally with:

```sh
shasum -a 256 docs/media/observatory-overview.mp4 \
  docs/media/observatory-overview-readme.gif \
  docs/media/observatory-overview-script.txt \
  docs/media/observatory-overview.vtt
```

## Reproduce

The repository does not distribute Kokoro model or voice-pack files. Pass their local paths to the end-to-end builder:

```sh
.venv/bin/python scripts/demo/build-walkthrough.py \
  --model /path/to/kokoro-v1.0.int8.onnx \
  --voices /path/to/voices-v1.0.bin
```

After watching the derived MP4 with audio and inspecting the review frames, publish that unchanged output:

```sh
.venv/bin/python scripts/demo/build-walkthrough.py \
  --model /path/to/kokoro-v1.0.int8.onnx \
  --voices /path/to/voices-v1.0.bin \
  --denylist /private/path/public-release-denylist.txt \
  --publish-reviewed
```

The builder refuses private dashboard environment variables and non-synthetic seed connections, installs hash-locked Kokoro dependencies, uses `npm ci`, captures the actual UI, packages H.264/AAC with embedded captions, creates the GIF, checks media streams and long silence, extracts review frames, and writes the provenance manifest. Preserve the WebVTT sidecar and retain the applicable Kokoro model/runtime license notices when redistributing those components.

Before replacing public media, review the full video with audio enabled, inspect the generated beginning/middle/POM/ending frames, run the repository privacy audit and Gitleaks, and confirm the manifest with `.venv/bin/python scripts/demo/verify-walkthrough.py`. The builder cannot automate the human visual/privacy review.
