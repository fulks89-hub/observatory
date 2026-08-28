import { mkdtemp, mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { tmpdir } from 'node:os';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const appRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = join(appRoot, 'data', 'airadar');
const expectedReports = ['daily.json', 'weekly.json', 'latest.json', 'shared-inbox.json', 'x-bookmarks.json'];
const repo = (process.env.MC_AIRADAR_REPO || '').trim();
const workflow = 'Passive AI discovery';

function validateReport(name, value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${name} is not a JSON object`);
  if (name === 'daily.json' || name === 'weekly.json') {
    if (!Array.isArray(value.trends)) throw new Error(`${name} is missing trends`);
  }
  if (name === 'latest.json' && !Array.isArray(value.signals)) throw new Error(`${name} is missing signals`);
  if (name === 'shared-inbox.json' && !Array.isArray(value.captures)) throw new Error(`${name} is missing captures`);
  if (name === 'x-bookmarks.json' && !Array.isArray(value.bookmarks)) throw new Error(`${name} is missing bookmarks`);
}

async function writeReports(readReport, metadata) {
  const reports = {};
  for (const name of expectedReports) {
    const text = await readReport(name);
    const value = JSON.parse(text);
    validateReport(name, value);
    reports[name] = JSON.stringify(value, null, 2) + '\n';
  }
  await mkdir(output, { recursive: true });
  for (const [name, text] of Object.entries(reports)) await writeFile(join(output, name), text, 'utf8');
  const sync = { ...metadata, source: 'private-github-artifact', syncedAt: new Date().toISOString() };
  await writeFile(join(output, 'sync-meta.json'), JSON.stringify(sync, null, 2) + '\n', 'utf8');
  return sync;
}

export async function importArtifactZip(zipPath, metadata = {}) {
  const safeZip = resolve(zipPath);
  const { stdout: listing } = await exec('unzip', ['-Z1', safeZip], { maxBuffer: 1024 * 1024 });
  const entries = listing.split(/\r?\n/).filter(Boolean);
  for (const name of expectedReports) if (!entries.includes(name)) throw new Error(`Artifact is missing ${name}`);
  if (entries.some((name) => name.startsWith('/') || name.split('/').includes('..'))) throw new Error('Unsafe artifact path');
  return writeReports(async (name) => (await exec('unzip', ['-p', safeZip, name], { maxBuffer: 10 * 1024 * 1024 })).stdout, metadata);
}

export async function syncAiradar() {
  if (!/^[\w.-]+\/[\w.-]+$/.test(repo)) {
    throw new Error('Set MC_AIRADAR_REPO to an exact owner/repository value before syncing');
  }
  await exec('gh', ['auth', 'status', '--hostname', 'github.com']);
  const { stdout } = await exec('gh', ['run', 'list', '--repo', repo, '--workflow', workflow, '--status', 'success', '--limit', '1', '--json', 'databaseId,headSha,number,updatedAt,conclusion']);
  const run = JSON.parse(stdout)[0];
  if (!run || run.conclusion !== 'success' || !Number.isInteger(run.databaseId)) throw new Error('No successful AIRadar workflow run found');
  const temp = await mkdtemp(join(tmpdir(), 'mission-control-airadar-'));
  try {
    await exec('gh', ['run', 'download', String(run.databaseId), '--repo', repo, '--name', 'ai-radar-signals', '--dir', temp], { maxBuffer: 10 * 1024 * 1024 });
    const entries = await readdir(temp, { withFileTypes: true });
    if (entries.some((entry) => entry.isSymbolicLink())) throw new Error('Artifact contains a symbolic link');
    // Wait for every report to be read before the temporary download is removed.
    return await writeReports((name) => readFile(join(temp, basename(name)), 'utf8'), {
      runId: run.databaseId,
      runNumber: run.number,
      headSha: run.headSha,
      runUpdatedAt: run.updatedAt,
    });
  } finally {
    await rm(temp, { recursive: true, force: true });
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const zipIndex = process.argv.indexOf('--artifact-zip');
  const runIndex = process.argv.indexOf('--run-number');
  const shaIndex = process.argv.indexOf('--head-sha');
  const digestIndex = process.argv.indexOf('--artifact-digest');
  const sync = zipIndex >= 0
    ? await importArtifactZip(process.argv[zipIndex + 1], {
        runNumber: runIndex >= 0 ? Number(process.argv[runIndex + 1]) : null,
        headSha: shaIndex >= 0 ? process.argv[shaIndex + 1] : null,
        artifactDigest: digestIndex >= 0 ? process.argv[digestIndex + 1] : null,
      })
    : await syncAiradar();
  console.log(`AIRadar synced from run #${sync.runNumber || 'unknown'}.`);
}
