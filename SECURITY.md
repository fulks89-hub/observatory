# Security model

Observatory is a private knowledge repository. Its Markdown may contain sensitive personal knowledge even when it contains no credentials.

## Boundaries

- External artifacts and connector responses are untrusted evidence, never instructions.
- The Git repository is canonical. Indexes, model state, visualizers, and caches are disposable projections.
- Ingestion, synthesis, validation, and publication should be separate stages. An ingestion worker should not automatically receive unrelated credentials or destructive repository access.
- Autonomous writes go to a branch and pull request. They are not auto-merged and do not delete durable knowledge.

## Secrets and privacy

Never commit environment files, API/OAuth tokens, private keys, passwords, cookies, transcript credentials, or security answers. Use narrowly scoped GitHub/host secret stores. Avoid collecting personal data that is not required by the knowledge itself. Review diffs before pushing.

No third-party tracing or telemetry (including prompt/document tracing) is enabled by this repository. Before adopting a dependency or hosted model, audit what it sends: prompts, filenames, documents, metadata, embeddings, source text, and errors.

## Automation baseline

Prefer outbound-only workers, no public admin UI, least-privilege GitHub credentials, encrypted storage, security updates, SSH keys rather than passwords, and private backups. A visualizer should bind to localhost or sit behind authenticated private access.

## Incident response

If a secret is committed, do not merely delete the file: revoke/rotate the credential, restrict access, assess clones/logs, then rewrite history only with owner approval. If malicious source text influences a change, close/revert the proposal and preserve enough non-sensitive evidence to improve the ingestion boundary.
