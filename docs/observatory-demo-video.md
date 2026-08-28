# Observatory public demo video

This is the canonical public-safe storyboard for the short README explainer. It may be rendered as MP4 plus a lightweight GIF/poster for GitHub.

## Privacy rule

The demo must contain **no owner-specific or installation-specific data**. Do not use screenshots from a personal Observatory or AIRadar instance.

Exclude names, usernames, emails, locations, employers, real personal projects, private repositories, POM contents, local paths, watchlists, X bookmarks, private reports, account/billing information, credentials, API keys, tokens, or private source URLs.

Use only synthetic labels such as `Project Alpha`, `Research note`, `Decision principle`, `Skill`, and `Source` when examples are needed.

## Target

- duration: roughly 60–75 seconds;
- format: 1280×720 MP4 (H.264 + AAC) plus a small GIF or poster image for the README;
- tone: simple, calm, technical but accessible;
- narration uses local Kokoro with the reviewed voice; no automatic speech-engine fallback is allowed;
- no third-party copyrighted screenshots or branding beyond plain-text names needed to explain compatibility.

## Storyboard

1. **Mission Control overview**
   - Show the actual sanitized command center with synthetic project and attention data.
   - Explain that Mission Control is a local projection while Markdown and Git remain authoritative.

2. **Atlas map and neighborhood**
   - Open Atlas, select the synthetic Context Engineering node, and show its immediate relationships.
   - Explain that ordinary Markdown links create the graph without a second canonical database.

3. **Explore and skill routing**
   - Open Explore, select Skills, and search for `handoff`.
   - Explain metadata-first retrieval and opening only the few relevant records.

4. **Personal Operating Model**
   - Show the uninitialized synthetic state rather than personal preferences.
   - Explain that it is optional and owner-reviewed, not a personality profile.

5. **Return and closing**
   - Return to the command center and display the closing message.
   - Text: `Your agents can change. Your useful memory does not have to.`
   - Text: `Clone it. Point an agent at AGENTS.md. Build your own Observatory.`

The capture must not imply that AI Radar, Decision Frontier, or another feature was demonstrated when it did not appear on screen. Scene order and hold timing are machine-readable in `scripts/demo/scenes.json`.

## Narration

> Observatory is a portable memory layer for AI agents. Instead of depending on one chat, one model, or one vendor, it keeps durable knowledge in readable Markdown and uses Git for history and review.
>
> It can remember projects, decisions, research, resources, failures, and lessons. An optional Personal Operating Model can also capture how you prefer agents to work: decision principles, evidence standards, desired autonomy, communication style, and reusable lessons.
>
> Observatory is designed to stay context efficient. Agents search first, open only the few records that matter, and stop when they have enough.
>
> A lightweight skill catalog helps agents find the right reusable procedure. For large uncertain projects, a Decision Frontier can map what still needs to be figured out.
>
> Mission Control gives you a visual way to explore projects, the knowledge Atlas, AI Radar, and a searchable Explore view for the index, skills, resources, rules, and operating model.
>
> The goal is simple: your agents can change, but your useful memory, decisions, and ways of working do not have to.

## README placement

For a fresh public repository, place the finished assets under a public-safe path such as:

```text
docs/media/observatory-overview.mp4
docs/media/observatory-overview-readme.gif
```

Pin the GIF/poster immediately below the README introduction and link it to the MP4 with visible text such as **Watch the 70-second Observatory overview**. Verify the committed media metadata and frames contain no personal information before the first public push.

## Reproduction contract

The end-to-end builder runs the real sanitized UI, Playwright capture, local Kokoro narration, FFmpeg packaging, caption embedding, GIF generation, stream/silence checks, and provenance-manifest generation. It deliberately requires local model and voice assets:

```sh
.venv/bin/python scripts/demo/build-walkthrough.py \
  --model /path/to/kokoro-v1.0.int8.onnx \
  --voices /path/to/voices-v1.0.bin
```

Watch the complete derived MP4 with audio and inspect every generated review frame. Only after that human review, publish the unchanged derived artifacts with the private denylist gate:

```sh
.venv/bin/python scripts/demo/build-walkthrough.py \
  --model /path/to/kokoro-v1.0.int8.onnx \
  --voices /path/to/voices-v1.0.bin \
  --denylist /private/path/public-release-denylist.txt \
  --publish-reviewed
```

Run Gitleaks before committing media. Do not run `--publish-reviewed` until the intended Mission Control revision and its tests are final.
