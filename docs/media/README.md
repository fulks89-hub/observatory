# Observatory walkthrough media

`observatory-overview.mp4` is the public synthetic product walkthrough pinned in the root README. It was captured from the actual sanitized Mission Control UI; it does not use a personal Observatory, private screenshot, or external media service.

## Artifact contract

- adapter: Playwright 1.62.1 against local Mission Control, macOS local speech synthesis, FFmpeg 9.0.1;
- display: 1280×720, 30 fps, H.264 video, AAC narration, embedded English captions;
- duration: approximately 64.7 seconds;
- source data: generic `mission-control/config/seed.json` and synthetic canonical examples;
- walkthrough: Overview → Atlas interaction → Explore → skill search → uninitialized Personal Operating Model → closing message;
- sidecars: `observatory-overview-script.txt` and `observatory-overview.vtt`;
- README preview: `observatory-overview-readme.gif` at 640×360;
- source revision: the fresh-history public release containing these assets; verify the exact commit with `git rev-parse HEAD`.

The release audit records the final SHA-256 hashes and exact public commit. Recompute locally with:

```sh
shasum -a 256 docs/media/observatory-overview.mp4 \
  docs/media/observatory-overview-readme.gif \
  docs/media/observatory-overview-script.txt \
  docs/media/observatory-overview.vtt
```

## Reproduce

Start the sanitized dashboard without `MC_PROJECT_ROOTS` so it uses only synthetic seed data:

```sh
cd mission-control
npm ci
npm run check
npm test
npm run dev -- --port 4173
```

In another shell:

```sh
cd scripts/demo
npm ci
npx playwright install chromium
npm run record
```

The deterministic raw capture is written to `.derived/demo-output/observatory-walkthrough-raw.webm`. Generate narration from `docs/media/observatory-overview-script.txt` with a local voice, then package it with FFmpeg as H.264/AAC at 1280×720. Preserve `docs/media/observatory-overview.vtt` as both an embedded caption stream and a sidecar.

Before replacing public media, review the full video with audio enabled, inspect beginning/middle/POM/ending frames, run `ffprobe` to confirm streams and dimensions, run the repository privacy audit, and update the recorded hashes and exact source commit.
