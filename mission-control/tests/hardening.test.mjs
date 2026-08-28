import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, symlink, writeFile } from 'node:fs/promises';
import { request } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { atomicWriteJson } from '../scripts/atomic-io.mjs';
import { extractKnowledgeLinks, parseProjectRoots, redactSnapshot } from '../scripts/security.mjs';
import { safeExternalHref } from '../src/safe-url.js';
import { createMissionControlServer } from '../server.mjs';
import { writeReports } from '../scripts/sync-airadar.mjs';

async function start(options = {}) {
  const server = createMissionControlServer({
    root: options.root || await mkdtemp(join(tmpdir(), 'mc-static-')),
    collect: options.collect || (async () => ({ projects: [], atlas: { nodes: [], edges: [] }, airadar: {} })),
    syncAiradar: options.syncAiradar || (async () => ({ runNumber: 1 })),
    evaluateAiradar: options.evaluateAiradar || (async () => ({ topic_evaluations: [] })),
    setProjectArchived: options.setProjectArchived || (async () => ({ projects: [] })),
    readOnly: options.readOnly || false,
    aiEvaluationEnabled: options.aiEvaluationEnabled || false,
    model: options.model || 'test-model',
    csrfToken: options.csrfToken || 'test-token',
    allowedOrigins: ['http://127.0.0.1'],
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  return { server, port };
}

function call(port, path, { method = 'GET', headers = {}, body = '' } = {}) {
  return new Promise((resolve, reject) => {
    const req = request({ host: '127.0.0.1', port, path, method, headers }, (res) => {
      let text = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => { text += chunk; });
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, text, json: () => JSON.parse(text) }));
    });
    req.on('error', reject);
    req.end(body);
  });
}

const mutationHeaders = {
  origin: 'http://127.0.0.1',
  'sec-fetch-site': 'same-origin',
  'x-mc-csrf-token': 'test-token',
};

test('malformed URL is contained and the server remains healthy', async (t) => {
  const { server, port } = await start();
  t.after(() => server.close());
  assert.equal((await call(port, '/%')).status, 400);
  assert.equal((await call(port, '/api/session')).status, 200);
});

test('static serving rejects symlinks and directories without exposing outside files', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'mc-static-root-'));
  const outside = join(await mkdtemp(join(tmpdir(), 'mc-static-outside-')), 'private.txt');
  await writeFile(join(root, 'index.html'), 'safe');
  await writeFile(outside, 'PRIVATE-CANARY');
  await symlink(outside, join(root, 'link.txt'));
  await mkdir(join(root, 'directory'));
  const { server, port } = await start({ root });
  t.after(() => server.close());
  const link = await call(port, '/link.txt');
  assert.equal(link.status, 403);
  assert.equal(link.text.includes('PRIVATE-CANARY'), false);
  assert.equal((await call(port, '/directory')).status, 404);
  assert.equal((await call(port, '/api/session')).status, 200);
});

test('mutations require same-origin and the per-process CSRF token', async (t) => {
  let calls = 0;
  const { server, port } = await start({ syncAiradar: async () => { calls += 1; } });
  t.after(() => server.close());
  assert.equal((await call(port, '/api/airadar/sync', { method: 'POST' })).status, 403);
  assert.equal((await call(port, '/api/airadar/sync', { method: 'POST', headers: { ...mutationHeaders, origin: 'https://evil.test' } })).status, 403);
  assert.equal(calls, 0);
  assert.equal((await call(port, '/api/airadar/sync', { method: 'POST', headers: mutationHeaders })).status, 200);
  assert.equal(calls, 1);
});

test('sync never evaluates and hosted evaluation is disabled by default', async (t) => {
  let syncs = 0, evaluations = 0;
  const { server, port } = await start({
    syncAiradar: async () => { syncs += 1; },
    evaluateAiradar: async () => { evaluations += 1; },
  });
  t.after(() => server.close());
  await call(port, '/api/airadar/sync', { method: 'POST', headers: mutationHeaders });
  assert.equal(syncs, 1);
  assert.equal(evaluations, 0);
  const response = await call(port, '/api/airadar/evaluate', { method: 'POST', headers: { ...mutationHeaders, 'content-type': 'application/json' }, body: '{}' });
  assert.equal(response.status, 410);
  assert.equal(evaluations, 0);
});

test('concurrent sync requests share one operation', async (t) => {
  let calls = 0;
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  let started;
  const began = new Promise((resolve) => { started = resolve; });
  const { server, port } = await start({ syncAiradar: async () => { calls += 1; started(); await gate; } });
  t.after(() => server.close());
  const a = call(port, '/api/airadar/sync', { method: 'POST', headers: mutationHeaders });
  const b = call(port, '/api/airadar/sync', { method: 'POST', headers: mutationHeaders });
  await began;
  await new Promise((resolve) => setTimeout(resolve, 20));
  release();
  assert.equal((await a).status, 200);
  assert.equal((await b).status, 200);
  assert.equal(calls, 1);
});

test('hosted evaluation is unavailable and cannot invoke an injected evaluator', async (t) => {
  let calls = 0;
  const { server, port } = await start({ aiEvaluationEnabled: true, evaluateAiradar: async () => { calls += 1; } });
  t.after(() => server.close());
  const session = await call(port, '/api/session');
  assert.equal(session.json().aiEvaluation.enabled, false);
  assert.equal((await call(port, '/api/airadar/evaluate', { method: 'POST', headers: mutationHeaders })).status, 410);
  assert.equal(calls, 0);
});

test('request bodies have a byte cap', async (t) => {
  const { server, port } = await start();
  t.after(() => server.close());
  const response = await call(port, '/api/projects/example/archive', { method: 'POST', headers: { ...mutationHeaders, 'content-type': 'application/json' }, body: JSON.stringify({ archived: true, padding: 'x'.repeat(17 * 1024) }) });
  assert.equal(response.status, 413);
});

test('read-only snapshot redaction removes all sensitive canaries', () => {
  const canary = 'PRIVATE-CANARY';
  const redacted = redactSnapshot({
    projects: [{ id: canary, name: canary, objective: canary, blockers: [canary] }],
    atlas: { nodes: [{ label: canary, description: canary }], edges: [{ source: canary, target: canary }] },
    airadar: { daily: { trends: [{ title: canary }] }, x: { bookmarks: [{ text: canary }] }, watchlist: { people: [canary] } },
  }, true);
  assert.equal(JSON.stringify(redacted).includes(canary), false);
  assert.deepEqual(redacted.projects, []);
  assert.deepEqual(redacted.atlas.nodes, []);
});

test('read-only server never serves a stale Explore projection', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'mc-explore-'));
  await mkdir(join(root, 'data'));
  await writeFile(join(root, 'index.html'), 'safe');
  await writeFile(join(root, 'data', 'explore.json'), '{"resources":[{"title":"PRIVATE-CANARY"}]}');
  const { server, port } = await start({ root, readOnly: true });
  t.after(() => server.close());
  const response = await call(port, '/data/explore.json');
  assert.equal(response.status, 200);
  assert.equal(response.text.includes('PRIVATE-CANARY'), false);
  assert.deepEqual(response.json().resources, []);
});

test('safe external links accept only credential-free HTTP(S)', () => {
  assert.equal(safeExternalHref('https://example.test/a'), 'https://example.test/a');
  assert.equal(safeExternalHref('http://example.test'), 'http://example.test/');
  for (const value of ['javascript:alert(1)', 'data:text/html,x', 'file:///tmp/x', '//example.test', 'https://u:p@example.test', 'bad']) assert.equal(safeExternalHref(value), null);
});

test('project-root parsing honors the supplied platform delimiter', () => {
  assert.deepEqual(parseProjectRoots('/a:/b', ':'), ['/a', '/b']);
  assert.deepEqual(parseProjectRoots('C:\\one;D:\\two', ';'), ['C:\\one', 'D:\\two']);
});

test('Atlas link extraction supports Markdown and Obsidian forms', () => {
  const links = extractKnowledgeLinks('[A](../concepts/a.md) [[b]] [[c|Alias]] [[d#Part]] ![[e]]');
  assert.deepEqual(links.map((item) => item.target), ['../concepts/a.md', 'b', 'c', 'd', 'e']);
});

test('Atlas ignores link examples in metadata, comments, and code', () => {
  const markdown = '---\nexample: "[[metadata]]"\n---\n<!-- [[comment]] -->\n`[[inline]]`\n```text\n[[fenced]]\n```\n[[real]]';
  assert.deepEqual(extractKnowledgeLinks(markdown).map((item) => item.target), ['real']);
});

test('atomic JSON writes replace complete files', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'mc-atomic-'));
  const path = join(directory, 'value.json');
  await writeFile(path, '{"old":true}\n');
  await atomicWriteJson(path, { next: true });
  assert.deepEqual(JSON.parse(await readFile(path, 'utf8')), { next: true });
});

test('AIRadar reports commit as one pointed generation', async () => {
  const output = await mkdtemp(join(tmpdir(), 'mc-reports-'));
  const reports = {
    'daily.json': { trends: [] }, 'weekly.json': { trends: [] }, 'latest.json': { signals: [] },
    'shared-inbox.json': { captures: [] }, 'x-bookmarks.json': { bookmarks: [] },
  };
  const result = await writeReports(async (name) => JSON.stringify(reports[name]), { runNumber: 7, headSha: 'abc123' }, output);
  const pointer = JSON.parse(await readFile(join(output, 'current.json'), 'utf8'));
  assert.equal(pointer.generationId, result.generationId);
  assert.deepEqual(JSON.parse(await readFile(join(output, 'generations', result.generationId, 'daily.json'), 'utf8')), { trends: [] });
});

test('AIRadar rejects malformed report items before changing the generation pointer', async () => {
  const output = await mkdtemp(join(tmpdir(), 'mc-invalid-reports-'));
  const reports = {
    'daily.json': { trends: [null] }, 'weekly.json': { trends: [] }, 'latest.json': { signals: [] },
    'shared-inbox.json': { captures: [] }, 'x-bookmarks.json': { bookmarks: [] },
  };
  await assert.rejects(() => writeReports(async (name) => JSON.stringify(reports[name]), { runNumber: 9, headSha: 'bad' }, output), /malformed item/);
  await assert.rejects(() => readFile(join(output, 'current.json'), 'utf8'), /ENOENT/);
});
