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
- narration may be synthetic/local TTS;
- no third-party copyrighted screenshots or branding beyond plain-text names needed to explain compatibility.

## Storyboard

1. **Observatory — a memory layer for AI agents**
   - Show four generic nodes: Knowledge, Projects, Operating Model, Skills.
   - Explain that different agents can share one durable context layer.

2. **Markdown is the source of truth**
   - Show Markdown → Git history → Any agent.
   - Explain readable storage, version history, review, rollback, and portability.

3. **Personal Operating Model**
   - Show generic cards: Decision principles, Evidence standards, Agent autonomy, Reusable lessons.
   - Explain that it is optional and owner-reviewed, not a personality profile.

4. **Context-efficient retrieval**
   - Show Search → Match → Open 1–3 → Work.
   - Explain that Observatory consults broadly but loads narrowly.

5. **Skills + Decision Frontier**
   - Show skill catalog routing and a small unresolved-decision tree.
   - Explain that agents load the matching procedure and use Decision Frontier only for foggy multi-session work.

6. **Mission Control**
   - Show generic tabs: Overview, Atlas, Explore, AIRadar.
   - Within Explore show Index, Skills, Resources, Rules, Operating Model.
   - State that views are projections; Markdown/Git remain authoritative.

7. **Closing**
   - Text: `Your agents can change. Your useful memory does not have to.`
   - Text: `Clone it. Point an agent at AGENTS.md. Build your own Observatory.`

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
