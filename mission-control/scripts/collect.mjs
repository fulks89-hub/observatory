import { access, mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { basename, dirname, extname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import { attachEvaluations, stableBookmarkId } from './ai-evaluation-contract.mjs';

const exec = promisify(execFile);
const appRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const config = JSON.parse(await readFile(join(appRoot, 'config/projects.json'), 'utf8'));
const seed = JSON.parse(await readFile(join(appRoot, 'config/seed.json'), 'utf8'));
const preferencesPath = join(appRoot, 'data', 'preferences.json');
const observatoryRoot = resolve(process.env.OBSERVATORY_ROOT || join(appRoot, '..'));
let preferences = await readJson(preferencesPath, { archivedProjects: {} });

const explicitRoots = (process.env.MC_PROJECT_ROOTS || '').split(':').filter(Boolean);
// Public-safe default: never crawl conventional home-directory locations.
// Local checkout discovery is opt-in through MC_PROJECT_ROOTS.
const roots = [...new Set(explicitRoots.map((value) => resolve(value)))];

async function exists(path) {
  try { await access(path); return true; } catch { return false; }
}

async function findNamed(root, names, depth = 0) {
  if (depth > 3 || !(await exists(root))) return null;
  if (names.includes(basename(root)) && await exists(join(root, '.git'))) return root;
  let entries = [];
  try { entries = await readdir(root, { withFileTypes: true }); } catch { return null; }
  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name.startsWith('.') || ['node_modules', 'dist', 'Library'].includes(entry.name)) continue;
    if (names.includes(entry.name)) {
      const candidate = join(root, entry.name);
      if (await exists(join(candidate, '.git'))) return candidate;
    }
  }
  if (depth === 3) return null;
  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name.startsWith('.') || ['node_modules', 'dist', 'Library', 'outputs'].includes(entry.name)) continue;
    const found = await findNamed(join(root, entry.name), names, depth + 1);
    if (found) return found;
  }
  return null;
}

function parseSections(markdown = '') {
  const sections = {};
  let key = 'intro';
  for (const line of markdown.split(/\r?\n/)) {
    const heading = line.match(/^##\s+(.+)$/);
    if (heading) { key = heading[1].trim().toLowerCase(); sections[key] = []; continue; }
    if (line.trim()) (sections[key] ||= []).push(line.trim());
  }
  return sections;
}

function cleanLine(line = '') {
  return line.replace(/^[-*]\s+/, '').replace(/^\d+\.\s+/, '').replace(/`/g, '').trim();
}

async function gitState(path) {
  try {
    const [{ stdout: branch }, { stdout: head }, { stdout: status }, { stdout: timestamp }] = await Promise.all([
      exec('git', ['-C', path, 'branch', '--show-current']),
      exec('git', ['-C', path, 'rev-parse', '--short', 'HEAD']),
      exec('git', ['-C', path, 'status', '--porcelain']),
      exec('git', ['-C', path, 'log', '-1', '--format=%cI']),
    ]);
    return { branch: branch.trim(), head: head.trim(), dirty: Boolean(status.trim()), lastCommitAt: timestamp.trim() };
  } catch { return null; }
}

async function githubState(repo) {
  if (process.env.MC_ENABLE_GITHUB !== '1' || !/^[\w.-]+\/[\w.-]+$/.test(repo)) return null;
  try {
    const [prs, issues, run] = await Promise.all([
      exec('gh', ['pr', 'list', '--repo', repo, '--state', 'open', '--json', 'number']),
      exec('gh', ['issue', 'list', '--repo', repo, '--state', 'open', '--json', 'number']),
      exec('gh', ['run', 'list', '--repo', repo, '--limit', '1', '--json', 'conclusion,status,updatedAt,name']),
    ]);
    const latest = JSON.parse(run.stdout)[0] || null;
    return {
      openPrs: JSON.parse(prs.stdout).length,
      openIssues: JSON.parse(issues.stdout).length,
      ci: !latest ? 'unknown' : latest.status !== 'completed' ? 'running' : latest.conclusion === 'success' ? 'passing' : 'failing',
      workflow: latest,
    };
  } catch { return null; }
}

async function readJson(path, fallback) {
  try { return JSON.parse(await readFile(path, 'utf8')); } catch { return fallback; }
}

function frontmatterValue(markdown, key) {
  const match = markdown.match(new RegExp(`^${key}:\\s*(.+)$`, 'm'));
  return match ? match[1].trim().replace(/^['"]|['"]$/g, '') : '';
}

function atlasDescription(markdown) {
  const explicit = frontmatterValue(markdown, 'description');
  if (explicit) return explicit;
  const paragraph = markdown
    .replace(/^---[\s\S]*?---\s*/m, '')
    .split(/\n\s*\n/)
    .find((block) => block.trim() && !block.trim().startsWith('#'));
  return cleanLine(paragraph || '').slice(0, 240);
}

async function markdownFiles(directory) {
  if (!(await exists(directory))) return [];
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await markdownFiles(path));
    else if (entry.isFile() && extname(entry.name) === '.md') files.push(path);
  }
  return files;
}

async function collectAtlas() {
  const groups = ['projects', 'concepts', 'research', 'ideas', 'questions'];
  const files = (await Promise.all(groups.map((group) => markdownFiles(join(observatoryRoot, group))))).flat();
  const records = await Promise.all(files.map(async (path) => {
    const markdown = await readFile(path, 'utf8');
    const id = relative(observatoryRoot, path).replace(/\\/g, '/').replace(/\.md$/, '');
    const fallbackTitle = basename(path, '.md').replace(/[-_]/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
    return {
      id,
      path,
      markdown,
      label: frontmatterValue(markdown, 'title') || fallbackTitle,
      type: frontmatterValue(markdown, 'type') || 'Note',
      description: atlasDescription(markdown),
      status: frontmatterValue(markdown, 'project_status') || frontmatterValue(markdown, 'status') || '',
    };
  }));
  const known = new Map(records.map((record) => [resolve(record.path), record.id]));
  const edges = [];
  const seen = new Set();
  for (const record of records) {
    const linkPattern = /\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)/g;
    for (const match of record.markdown.matchAll(linkPattern)) {
      let linkedPath = '';
      try { linkedPath = decodeURIComponent(match[1]); } catch { continue; }
      const targetPath = resolve(dirname(record.path), linkedPath);
      const target = known.get(targetPath);
      if (!target || target === record.id) continue;
      const key = [record.id, target].sort().join('|');
      if (seen.has(key)) continue;
      seen.add(key);
      edges.push({ source: record.id, target, kind: 'markdown-link' });
    }
  }
  const degree = new Map(records.map((record) => [record.id, 0]));
  for (const edge of edges) {
    degree.set(edge.source, (degree.get(edge.source) || 0) + 1);
    degree.set(edge.target, (degree.get(edge.target) || 0) + 1);
  }
  return {
    nodes: records.map(({ path: _path, markdown: _markdown, ...record }) => ({ ...record, connections: degree.get(record.id) || 0 })),
    edges,
    source: 'canonical Markdown links',
  };
}

async function projectSnapshot(project) {
  let localPath = null;
  for (const root of roots) {
    localPath = await findNamed(root, project.localNames);
    if (localPath) break;
  }
  const base = seed.projects[project.id] || {};
  let status = {};
  if (localPath) {
    const statusPath = join(localPath, '.ops', 'PROJECT_STATUS.md');
    if (await exists(statusPath)) {
      const sections = parseSections(await readFile(statusPath, 'utf8'));
      const objective = (sections['current objective'] || []).map(cleanLine).join(' ');
      const blockers = (sections['blockers / risks'] || sections['external setup remaining'] || []).filter((line) => /^[-*]/.test(line)).map(cleanLine).slice(0, 4);
      const nextActions = (sections['next actions'] || []).filter((line) => /^\d+\./.test(line)).map(cleanLine).slice(0, 4);
      const lastUpdated = cleanLine((sections['last updated'] || [base.lastUpdated])[0]);
      status = { objective: objective || base.objective, blockers, nextActions, lastUpdated };
    }
  }
  const [git, github] = await Promise.all([localPath ? gitState(localPath) : null, githubState(project.repo)]);
  const archivePreference = preferences.archivedProjects?.[project.id];
  const archived = typeof archivePreference === 'boolean'
    ? archivePreference
    : archivePreference?.archived ?? Boolean(project.archived);
  const activityAt = github?.workflow?.updatedAt || git?.lastCommitAt || status.lastUpdated || base.lastUpdated || null;
  const activityBaseline = typeof archivePreference === 'object' ? archivePreference.activityBaseline : null;
  const archiveAttention = Boolean(
    archived && activityAt && activityBaseline && Date.parse(activityAt) > Date.parse(activityBaseline)
  );
  return {
    ...project,
    ...base,
    ...status,
    ...(github || {}),
    local: Boolean(localPath),
    localPath,
    git,
    source: localPath ? 'local checkout' : 'synthetic seed snapshot',
    archived,
    archivedAt: typeof archivePreference === 'object' ? archivePreference.archivedAt : null,
    activityAt,
    archiveAttention,
  };
}

export async function setProjectArchived(projectId, archived) {
  const projectConfig = config.find((project) => project.id === projectId);
  if (!projectConfig) throw new Error('Unknown project');
  const project = await projectSnapshot(projectConfig);
  const now = new Date().toISOString();
  preferences = {
    ...preferences,
    archivedProjects: {
      ...(preferences.archivedProjects || {}),
      [projectId]: {
        archived: Boolean(archived),
        archivedAt: archived ? now : null,
        activityBaseline: project.activityAt || now,
      },
    },
  };
  await mkdir(dirname(preferencesPath), { recursive: true });
  await writeFile(preferencesPath, JSON.stringify(preferences, null, 2) + '\n');
  return collect();
}

export async function collect() {
  const [projects, atlas] = await Promise.all([
    Promise.all(config.map(projectSnapshot)),
    collectAtlas(),
  ]);
  const airadarProject = projects.find((item) => item.id === 'airadar');
  const localReports = airadarProject?.localPath ? join(airadarProject.localPath, 'reports') : null;
  const syncedReports = join(appRoot, 'data', 'airadar');
  // An explicit GitHub artifact sync is the strongest freshness signal. Prefer
  // it over an arbitrarily discovered checkout, which may be on an older branch.
  const reports = await exists(join(syncedReports, 'daily.json'))
    ? syncedReports
    : localReports && await exists(join(localReports, 'daily.json')) ? localReports : null;
  const watchlistPath = airadarProject?.localPath ? join(airadarProject.localPath, 'config', 'watchlist.json') : null;
  const watchlistJson = watchlistPath ? await readJson(watchlistPath, null) : null;
  const daily = reports ? await readJson(join(reports, 'daily.json'), seed.airadar.daily) : seed.airadar.daily;
  const weekly = reports ? await readJson(join(reports, 'weekly.json'), seed.airadar.weekly) : seed.airadar.weekly;
  const xReport = reports ? await readJson(join(reports, 'x-bookmarks.json'), seed.airadar.x) : seed.airadar.x;
  const aiEvaluation = reports ? await readJson(join(reports, 'ai-evaluations.json'), null) : null;
  const publicEvaluation = aiEvaluation ? {
    schemaVersion: aiEvaluation.schemaVersion,
    provider: aiEvaluation.provider,
    model: aiEvaluation.model,
    generatedAt: aiEvaluation.generatedAt,
    sourceRun: aiEvaluation.sourceRun,
    topicCount: aiEvaluation.topic_evaluations?.length || 0,
    x_digest: (aiEvaluation.x_digest || []).map((item) => ({
      ...item,
      sources: item.bookmark_ids.map((id) => {
        const bookmark = (xReport.bookmarks || []).find((candidate) => stableBookmarkId(candidate) === id);
        return bookmark ? { id, url: bookmark.url, author: bookmark.author_username || bookmark.author_name || 'X' } : { id };
      }),
    })),
  } : null;
  const airadar = {
    daily: attachEvaluations(daily, aiEvaluation),
    weekly: attachEvaluations(weekly, aiEvaluation),
    x: xReport,
    inbox: reports ? await readJson(join(reports, 'shared-inbox.json'), seed.airadar.inbox) : seed.airadar.inbox,
    latest: reports ? await readJson(join(reports, 'latest.json'), { generated_at: null, signals: [] }) : { generated_at: null, signals: [] },
    sync: reports ? await readJson(join(reports, 'sync-meta.json'), { source: localReports === reports ? 'local-checkout' : 'local-reports' }) : null,
    aiEvaluation: publicEvaluation,
    watchlist: watchlistJson ? {
      ...seed.airadar.watchlist,
      repositories: watchlistJson.github_repositories || seed.airadar.watchlist.repositories,
    } : seed.airadar.watchlist,
  };
  // Filesystem paths help the collector find local repositories but are never
  // needed by the browser. Keep them out of both local and shared snapshots.
  const publicProjects = projects.map(({ localPath: _localPath, ...project }) => project);
  const snapshot = {
    generatedAt: new Date().toISOString(),
    mode: projects.some((project) => project.local) ? 'local-live' : 'snapshot',
    githubEnabled: process.env.MC_ENABLE_GITHUB === '1',
    readOnly: process.env.MC_READ_ONLY === '1',
    projects: publicProjects,
    atlas,
    airadar,
  };
  await mkdir(join(appRoot, 'public', 'data'), { recursive: true });
  await writeFile(join(appRoot, 'public', 'data', 'snapshot.json'), JSON.stringify(snapshot, null, 2) + '\n');
  return snapshot;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const snapshot = await collect();
  console.log(`Mission Control refreshed: ${snapshot.projects.filter((project) => project.local).length} local projects found.`);
}
