const REDACTIONS = ['projects', 'atlas', 'airadar'];

export function parseProjectRoots(value, delimiter) {
  return String(value || '').split(delimiter).map((item) => item.trim()).filter(Boolean);
}

export function extractKnowledgeLinks(markdown = '') {
  const content = String(markdown)
    .replace(/^---\s*\n[\s\S]*?\n---\s*(?:\n|$)/, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/```[\s\S]*?```|~~~[\s\S]*?~~~/g, '')
    .replace(/`[^`\n]*`/g, '');
  const links = [];
  for (const match of content.matchAll(/\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)/g)) {
    links.push({ target: match[1], kind: 'markdown-link' });
  }
  for (const match of content.matchAll(/!?\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]/g)) {
    links.push({ target: match[1].trim(), kind: 'obsidian-wikilink' });
  }
  return links;
}

export function redactSnapshot(snapshot, readOnly) {
  if (!readOnly) return { ...snapshot, readOnly: false, sharing: { redactions: [] } };
  return {
    generatedAt: snapshot.generatedAt,
    mode: 'shared-redacted',
    githubEnabled: false,
    readOnly: true,
    projects: [],
    atlas: { nodes: [], edges: [], source: 'redacted in shared read-only mode' },
    airadar: {
      daily: { trends: [] }, weekly: { trends: [] }, x: { bookmarks: [], enabled: false },
      inbox: { captures: [] }, latest: { signals: [] }, sync: null, aiEvaluation: null,
      watchlist: { people: [], projects: [], repositories: [] },
    },
    sharing: { redactions: REDACTIONS },
  };
}
