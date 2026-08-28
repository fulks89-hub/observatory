import { mkdtemp, mkdir, readFile, readdir, rename, rm, stat } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { tmpdir } from 'node:os';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import { atomicWriteJson } from './atomic-io.mjs';
import { safeGenerationId } from './airadar-store.mjs';

const exec = promisify(execFile);
const appRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = join(appRoot, 'data', 'airadar');
const expectedReports = ['daily.json', 'weekly.json', 'latest.json', 'shared-inbox.json', 'x-bookmarks.json'];
const repo = (process.env.MC_AIRADAR_REPO || '').trim();
const trustedBranch = (process.env.MC_AIRADAR_BRANCH || 'main').trim();
const workflow = 'Passive AI discovery';
const MAX_ZIP_BYTES = 50 * 1024 * 1024;
const MAX_REPORT_BYTES = 10 * 1024 * 1024;
const MAX_TOTAL_BYTES = 25 * 1024 * 1024;
const MAX_ITEMS = 5000;

function validateReport(name, value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${name} is not a JSON object`);
  if (name === 'daily.json' || name === 'weekly.json') {
    if (!Array.isArray(value.trends)) throw new Error(`${name} is missing trends`);
  }
  if (name === 'latest.json' && !Array.isArray(value.signals)) throw new Error(`${name} is missing signals`);
  if (name === 'shared-inbox.json' && !Array.isArray(value.captures)) throw new Error(`${name} is missing captures`);
  if (name === 'x-bookmarks.json' && !Array.isArray(value.bookmarks)) throw new Error(`${name} is missing bookmarks`);
  const arrays = [value.trends, value.signals, value.captures, value.bookmarks].filter(Array.isArray);
  if (arrays.some((items) => items.length > MAX_ITEMS)) throw new Error(`${name} exceeds the ${MAX_ITEMS}-item safety limit`);
  if (arrays.some((items) => items.some((item) => !item || typeof item !== 'object' || Array.isArray(item)))) throw new Error(`${name} contains a malformed item`);
  for (const trend of value.trends || []) {
    if (trend.signals !== undefined && (!Array.isArray(trend.signals) || trend.signals.some((item) => !item || typeof item !== 'object' || Array.isArray(item)))) throw new Error(`${name} contains malformed trend signals`);
  }
}

export async function writeReports(readReport, metadata, outputRoot = output) {
  const reports = {};
  let totalBytes = 0;
  for (const name of expectedReports) {
    const text = await readReport(name);
    const bytes = Buffer.byteLength(text, 'utf8');
    if (bytes > MAX_REPORT_BYTES) throw new Error(`${name} exceeds the report size limit`);
    totalBytes += bytes;
    if (totalBytes > MAX_TOTAL_BYTES) throw new Error('AIRadar reports exceed the aggregate size limit');
    const value = JSON.parse(text);
    validateReport(name, value);
    reports[name] = JSON.stringify(value, null, 2) + '\n';
  }
  const generationId = safeGenerationId(metadata);
  const generations = join(outputRoot, 'generations');
  const staging = join(generations, `.staging-${generationId}`);
  const destination = join(generations, generationId);
  await mkdir(staging, { recursive: true });
  const sync = { ...metadata, generationId, source: 'private-github-artifact', syncedAt: new Date().toISOString() };
  try {
    for (const [name, text] of Object.entries(reports)) await atomicWriteJson(join(staging, name), JSON.parse(text));
    await atomicWriteJson(join(staging, 'sync-meta.json'), sync);
    await rename(staging, destination);
    await atomicWriteJson(join(outputRoot, 'current.json'), { generationId });
    const priorNames = (await readdir(generations, { withFileTypes: true })).filter((entry) => entry.isDirectory() && !entry.name.startsWith('.staging-') && entry.name !== generationId).map((entry) => entry.name);
    const prior = await Promise.all(priorNames.map(async (name) => ({ name, mtime: (await stat(join(generations, name))).mtimeMs })));
    prior.sort((left, right) => right.mtime - left.mtime);
    await Promise.all(prior.slice(4).map(({ name }) => rm(join(generations, name), { recursive: true, force: true })));
  } catch (error) {
    await rm(staging, { recursive: true, force: true });
    throw error;
  }
  return sync;
}

export async function importArtifactZip(zipPath, metadata = {}) {
  const safeZip = resolve(zipPath);
  if ((await stat(safeZip)).size > MAX_ZIP_BYTES) throw new Error('Artifact zip exceeds the size limit');
  const { stdout: listing } = await exec('unzip', ['-Z1', safeZip], { maxBuffer: 1024 * 1024, timeout: 30_000 });
  const entries = listing.split(/\r?\n/).filter(Boolean);
  for (const name of expectedReports) if (!entries.includes(name)) throw new Error(`Artifact is missing ${name}`);
  if (entries.length > 64 || new Set(entries).size !== entries.length) throw new Error('Artifact has too many or duplicate entries');
  if (entries.some((name) => name.startsWith('/') || name.split('/').includes('..'))) throw new Error('Unsafe artifact path');
  if (entries.some((name) => !expectedReports.includes(name))) throw new Error('Artifact contains an unexpected entry');
  return writeReports(async (name) => (await exec('unzip', ['-p', safeZip, name], { maxBuffer: 10 * 1024 * 1024, timeout: 30_000 })).stdout, metadata);
}

export async function syncAiradar() {
  if (!/^[\w.-]+\/[\w.-]+$/.test(repo)) {
    throw new Error('Set MC_AIRADAR_REPO to an exact owner/repository value before syncing');
  }
  await exec('gh', ['auth', 'status', '--hostname', 'github.com'], { timeout: 30_000 });
  const { stdout } = await exec('gh', ['run', 'list', '--repo', repo, '--workflow', workflow, '--branch', trustedBranch, '--status', 'success', '--limit', '1', '--json', 'databaseId,headSha,headBranch,event,number,updatedAt,conclusion'], { timeout: 30_000 });
  const run = JSON.parse(stdout)[0];
  if (!run || run.conclusion !== 'success' || !Number.isInteger(run.databaseId) || run.headBranch !== trustedBranch || !['push', 'schedule', 'workflow_dispatch'].includes(run.event)) throw new Error('No trusted successful AIRadar workflow run found');
  const temp = await mkdtemp(join(tmpdir(), 'mission-control-airadar-'));
  try {
    await exec('gh', ['run', 'download', String(run.databaseId), '--repo', repo, '--name', 'ai-radar-signals', '--dir', temp], { maxBuffer: 10 * 1024 * 1024, timeout: 120_000 });
    const entries = await readdir(temp, { withFileTypes: true });
    if (entries.length !== expectedReports.length || entries.some((entry) => !entry.isFile() || !expectedReports.includes(entry.name))) throw new Error('Artifact must contain only the expected regular report files');
    // Wait for every report to be read before the temporary download is removed.
    return await writeReports((name) => readFile(join(temp, basename(name)), 'utf8'), {
      runId: run.databaseId,
      runNumber: run.number,
      headSha: run.headSha,
      runUpdatedAt: run.updatedAt,
      repository: repo,
      branch: run.headBranch,
      event: run.event,
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
