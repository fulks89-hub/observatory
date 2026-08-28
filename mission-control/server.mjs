import { randomBytes } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { access, lstat, realpath } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, isAbsolute, join, normalize, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';
import { pipeline } from 'node:stream/promises';
import { collect, setProjectArchived } from './scripts/collect.mjs';
import { syncAiradar } from './scripts/sync-airadar.mjs';
import { redactSnapshot } from './scripts/security.mjs';

const appRoot = resolve(dirname(fileURLToPath(import.meta.url)));
const defaultRoot = join(appRoot, 'dist');
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png' };
const securityHeaders = { 'content-security-policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'", 'referrer-policy': 'no-referrer', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY' };
const headers = (extra = {}) => ({ ...securityHeaders, ...extra });
const jsonHeaders = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' };

function sendJson(response, status, value) {
  if (response.headersSent) return response.destroy();
  response.writeHead(status, headers(jsonHeaders));
  response.end(JSON.stringify(value));
}

async function jsonBody(request, limit = 16 * 1024) {
  const declared = Number(request.headers['content-length'] || 0);
  if (Number.isFinite(declared) && declared > limit) throw Object.assign(new Error('Request too large'), { status: 413 });
  const chunks = [];
  let bytes = 0;
  for await (const chunk of request) {
    bytes += chunk.length;
    if (bytes > limit) throw Object.assign(new Error('Request too large'), { status: 413 });
    chunks.push(chunk);
  }
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'); }
  catch { throw Object.assign(new Error('Invalid JSON'), { status: 400 }); }
}

function singleFlight() {
  let active = null;
  return (operation) => {
    if (active) return active;
    active = Promise.resolve().then(operation).finally(() => { active = null; });
    return active;
  };
}

export function createMissionControlServer(options = {}) {
  const root = resolve(options.root || defaultRoot);
  const realRoot = realpath(root);
  const readOnly = options.readOnly ?? process.env.MC_READ_ONLY === '1';
  const csrfToken = options.csrfToken || randomBytes(32).toString('hex');
  const collectFn = options.collect || collect;
  const archiveFn = options.setProjectArchived || setProjectArchived;
  const syncFn = options.syncAiradar || syncAiradar;
  const allowedOrigins = new Set(options.allowedOrigins || []);
  const runCollect = singleFlight(), runSync = singleFlight();
  const mutationAllowed = (request) => {
    const fetchSite = request.headers['sec-fetch-site'];
    return Boolean(request.headers.origin && allowedOrigins.has(request.headers.origin)
      && (!fetchSite || fetchSite === 'same-origin' || fetchSite === 'none')
      && request.headers['x-mc-csrf-token'] === csrfToken);
  };
  const snapshot = async () => redactSnapshot(await runCollect(() => collectFn()), readOnly);

  const server = createServer((request, response) => {
    void (async () => {
      let url;
      try { url = new URL(request.url || '/', 'http://mission-control.invalid'); decodeURIComponent(url.pathname); }
      catch { sendJson(response, 400, { error: 'Malformed request URL.' }); return; }
      const path = url.pathname;
      if (path === '/api/session' && request.method === 'GET') {
        sendJson(response, 200, { csrfToken, readOnly, aiEvaluation: { enabled: false, reason: 'No hosted evaluator is shipped; untrusted reports must not reach an agent with local tools.' } }); return;
      }
      if (path === '/data/snapshot.json' && request.method === 'GET') { sendJson(response, 200, await snapshot()); return; }
      if (path === '/data/explore.json' && request.method === 'GET' && readOnly) {
        sendJson(response, 200, { generatedAt: new Date().toISOString(), readOnly: true, counts: { records: 0, skills: 0, rules: 0, personalOperatingModel: 0 }, skills: [], policyKeys: [], index: [], resources: [], rules: [], personalOperatingModel: [], redactions: ['counts', 'skills', 'policyKeys', 'index', 'resources', 'rules', 'personalOperatingModel'] }); return;
      }
      const mutation = path === '/api/refresh' || path === '/api/airadar/sync' || path === '/api/airadar/evaluate' || /^\/api\/projects\/[a-z0-9-]+\/archive$/.test(path);
      if (mutation && request.method === 'POST' && !mutationAllowed(request)) { sendJson(response, 403, { error: 'Mutation request rejected.' }); return; }
      if (mutation && request.method === 'POST' && readOnly) { sendJson(response, 403, { error: 'Mission Control is in read-only sharing mode.' }); return; }
      if (path === '/api/refresh' && request.method === 'POST') { sendJson(response, 200, await snapshot()); return; }
      if (path === '/api/airadar/sync' && request.method === 'POST') { await runSync(() => syncFn()); sendJson(response, 200, await snapshot()); return; }
      if (path === '/api/airadar/evaluate' && request.method === 'POST') {
        sendJson(response, 410, { error: 'Hosted evaluation is unavailable because no tool-free inference boundary is configured.' }); return;
      }
      const archiveMatch = path.match(/^\/api\/projects\/([a-z0-9-]+)\/archive$/);
      if (archiveMatch && request.method === 'POST') {
        const body = await jsonBody(request);
        if (!body || typeof body !== 'object' || Array.isArray(body) || typeof body.archived !== 'boolean') { sendJson(response, 400, { error: 'archived must be boolean' }); return; }
        sendJson(response, 200, redactSnapshot(await archiveFn(archiveMatch[1], body.archived), false)); return;
      }
      if (path.startsWith('/api/')) { sendJson(response, mutation ? 405 : 404, { error: mutation ? 'Method not allowed.' : 'API route not found.' }); return; }
      if (!['GET', 'HEAD'].includes(request.method || '')) { response.writeHead(405, headers({ allow: 'GET, HEAD' })); response.end(); return; }
      const decoded = decodeURIComponent(path);
      const safePath = normalize(decoded).replace(/^[/\\]+/, '');
      let filePath = resolve(root, safePath);
      if (relative(root, filePath).startsWith('..')) { response.writeHead(403, headers()); response.end('Forbidden'); return; }
      const available = await access(filePath).then(() => true).catch(() => false);
      if (decoded === '/' || !available) filePath = join(root, 'index.html');
      const rootPath = await realRoot;
      const fileInfo = await lstat(filePath).catch(() => null);
      if (!fileInfo) { response.writeHead(404, headers()); response.end('Not found'); return; }
      if (fileInfo.isSymbolicLink()) { response.writeHead(403, headers()); response.end('Forbidden'); return; }
      const canonicalPath = await realpath(filePath).catch(() => null);
      const contained = canonicalPath ? relative(rootPath, canonicalPath) : '..';
      if (!canonicalPath || contained.startsWith('..') || isAbsolute(contained)) { response.writeHead(403, headers()); response.end('Forbidden'); return; }
      const canonicalInfo = await lstat(canonicalPath).catch(() => null);
      if (!canonicalInfo?.isFile()) { response.writeHead(404, headers()); response.end('Not found'); return; }
      filePath = canonicalPath;
      response.writeHead(200, headers({ 'content-type': types[extname(filePath)] || 'application/octet-stream', 'cache-control': ['.html', '.json'].includes(extname(filePath)) ? 'no-store' : 'public, max-age=31536000, immutable' }));
      if (request.method === 'HEAD') { response.end(); return; }
      await pipeline(createReadStream(filePath), response);
    })().catch((error) => {
      if (response.destroyed) return;
      const status = Number(error?.status) || 500;
      sendJson(response, status, { error: status < 500 ? error.message : 'Mission Control request failed.' });
    });
  });
  server.on('clientError', (_error, socket) => socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n'));
  return server;
}

export function startMissionControl() {
  const port = Number(process.env.PORT || 4173);
  const host = process.env.HOST || '127.0.0.1';
  if (!['127.0.0.1', 'localhost', '::1'].includes(host)) throw new Error('Mission Control only binds to a loopback host.');
  const displayHost = host === '::1' ? '[::1]' : host;
  const origins = [`http://127.0.0.1:${port}`, `http://localhost:${port}`, `http://[::1]:${port}`, ...String(process.env.MC_ALLOWED_ORIGINS || '').split(',').map((v) => v.trim()).filter(Boolean)];
  const server = createMissionControlServer({ allowedOrigins: origins });
  server.listen(port, host, () => console.log(`Mission Control is ${process.env.MC_READ_ONLY === '1' ? 'read-only' : 'private'} on http://${displayHost}:${port}`));
  return server;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) startMissionControl();
