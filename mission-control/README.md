# Observatory Mission Control

Observatory Mission Control is the optional local React dashboard for Observatory. It summarizes configured projects, Git state, blockers, next actions, and—when connected—generated AI Radar reports.

The **Atlas** tab derives its nodes and edges from ordinary links among `projects/`, `concepts/`, `research/`, `ideas/`, and `questions/`. It is an optional view, not a second source of truth. Select any object to inspect its immediate neighborhood.

The **Explore Observatory** surface is a list/search companion to Atlas. It derives a disposable `public/data/explore.json` projection from canonical Markdown and repository instructions so the owner can quickly browse the root index, reusable skills, resources/knowledge records, repository rules, and Personal Operating Model metadata. The generated projection is ignored by Git and never becomes canonical memory.

The cosmic background is a project-local generated asset at `public/assets/observatory-cosmic-field.png`. CSS keeps its stars crisp and visible while dark, translucent card surfaces preserve interface readability.

## Dashboard structure

Mission Control uses a deliberate information hierarchy:

1. **Control plane:** the sticky header keeps the Observatory identity, primary views, privacy mode, and refresh action stable.
2. **Sky window:** the Overview leaves a responsive band of unobstructed Milky Way above the `Observatory command center` hero. This is atmosphere and orientation, not content.
3. **Command summary:** four compact indicators answer what is online, changing, blocked, or newly discovered.
4. **Working portfolio:** project cards hold objectives, health, delivery state, and local Git evidence without turning the overview into a full project-management system.
5. **Attention and boundary:** the bottom panels separate next blockers from security and data-boundary status.
6. **Specialized views:** Atlas, AI Radar, and X Posts each own one job rather than competing inside the Overview.
7. **Explore:** a searchable read-only browser answers “what do I have?” while Atlas answers “how is it connected?”

The Atlas uses deterministic concentric orbits: projects occupy the inner orbit and concepts, research, ideas, and questions occupy one or more outer orbits. Labels use alternating lanes and opaque backing pills; long labels are truncated visually but preserved in accessible names. At higher node density, labels are limited to projects, the selection, and a manageable set of adjacent objects. The map collapses to a single-column layout on narrow screens, keeps its inspector below the graph, and lets filter chips scroll horizontally instead of widening the page.

Explore reads only metadata and text already present in Observatory. In normal local-owner mode it exposes index groupings, skill metadata, canonical record metadata, core repository rules, and POM record metadata. When `MC_READ_ONLY=1` is enabled, Explore fails closed: private index details, canonical record lists, rule text, and POM details are redacted by default while aggregate counts and non-sensitive skill metadata remain available.

It binds to `127.0.0.1` by default, stores preferences locally, omits filesystem paths from browser snapshots, and performs no remote writes.

## Start

Requires Node.js 22.12 or newer.

```bash
npm install
npm start
```

Open <http://127.0.0.1:4173>. Use the **Explore Observatory** control to open the searchable browser. For development, run `npm run dev`.

Every `refresh`, `dev`, `build`, and `start` run regenerates both the ordinary Mission Control snapshot and the ignored Explore projection.

## Configure projects

Edit `config/projects.json`. Mission Control does not crawl home-directory locations by default. To opt in to local project discovery, provide one or more colon-separated parent directories in `MC_PROJECT_ROOTS`. When it finds a configured checkout beneath an approved root, it reads `.ops/PROJECT_STATUS.md` and local Git status.

Set `OBSERVATORY_ROOT` only if this dashboard is moved outside its Observatory repository. By default the Atlas and Explore collector read the parent repository.

The supplied `config/seed.json` contains a small synthetic fallback snapshot for the configured projects when a checkout is not found. It is display data, not canonical Observatory memory. Never replace it with personal data in a public repository.

## Connect AI Radar

Place the AI Radar template beside this repository or add its parent folder to `MC_PROJECT_ROOTS`. Mission Control will read generated `reports/*.json` directly from a local checkout.

Optional private GitHub artifact synchronization is disabled until all of the following are true:

1. GitHub CLI is authenticated with appropriate read access.
2. `MC_AIRADAR_REPO` is set to an exact `owner/repository` value.
3. You explicitly run `npm run sync:airadar` or use the local dashboard control.

Imported report data remains ignored by Git.

## Short authenticated reviews

Mission Control has no built-in user login. Never run a bare public tunnel to it. For a short invited review, keep the app on `127.0.0.1`, run it in read-only mode, and make the tunnel enforce authentication plus an exact viewer allowlist.

1. Copy `config/ngrok-policy.example.yml` to the ignored file `config/ngrok-policy.local.yml`.
2. Replace the example addresses with the exact Google-account emails allowed to view the dashboard. Keep the deny rule.
3. Start the read-only dashboard with `npm run start:share`.
4. In another terminal, run `ngrok http 127.0.0.1:4173 --traffic-policy-file=config/ngrok-policy.local.yml`.
5. Test the URL while signed out and with an unlisted account before sharing it.

Stop both processes when the review ends. The temporary URL works only while this Mac, Mission Control, and the tunnel are running. Review the visible project and AI Radar data before inviting anyone.

For private access from a device in the same Tailscale network, keep the server bound to localhost and use `tailscale serve --bg http://127.0.0.1:4173`. Do not use Tailscale Funnel, which is public exposure.

## Security boundary

- External report content is rendered as untrusted evidence, never instructions.
- `MC_READ_ONLY=1` blocks archive changes and artifact synchronization.
- `MC_READ_ONLY=1` also redacts private Explore index/resource/rule/POM details by default.
- Generated `public/data/snapshot.json` and `public/data/explore.json` are ignored and must never be used as canonical memory.
- No credentials or local filesystem paths enter the browser bundle.
- The server has no built-in public authentication. Do not expose it to the public internet.
- `npm run start:share` enables read-only/redacted mode; authenticated tunnel access is still required.
