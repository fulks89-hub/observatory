# Try Observatory

Explore the public starter with its synthetic examples before choosing where your own knowledge will live. You need Git and Python 3.12+. The optional dashboard needs Node.js 22.12+.

## Search the starter

On macOS or Linux:

```sh
git clone https://github.com/fulks89-hub/observatory.git
cd observatory
scripts/bootstrap-observatory.sh --check
scripts/bootstrap-observatory.sh --install
.venv/bin/observatory search --json --limit 5 "knowledge"
.venv/bin/observatory validate
```

The install step creates a local Python environment and downloads the locked dependencies. The search returns matching records in the starter; open one of the returned Markdown files to inspect the underlying knowledge.

Windows users can follow [START-HERE.md](../START-HERE.md) for the PowerShell setup.

## Open Mission Control

In the same checkout:

```sh
cd mission-control
npm ci
npm start
```

Open <http://127.0.0.1:4173>. Explore the dashboard and Atlas, then inspect the corresponding files in your editor. Stop the server with Ctrl+C. The dashboard is a local view over the files, not a hosted account or a separate memory store.

## Make it yours

Before adding personal notes, follow the [guided setup](../START-HERE.md) to establish local-only storage or an owner-controlled private repository. The public starter's remote is not a destination for your personal knowledge.

Report setup problems or suggest improvements through [GitHub issues](https://github.com/fulks89-hub/observatory/issues/new/choose), using synthetic examples and redacted output.
