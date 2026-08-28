import { createReadStream } from 'node:fs';
import { access, readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';
import { collect, setProjectArchived } from './scripts/collect.mjs';
import { syncAiradar } from './scripts/sync-airadar.mjs';
import { evaluateAiradar } from './scripts/evaluate-airadar.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), 'dist');
const port = Number(process.env.PORT || 4173);
const host = process.env.HOST || '127.0.0.1';
const readOnly = process.env.MC_READ_ONLY === '1';
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml' };
const securityHeaders = {
  'content-security-policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
  'referrer-policy': 'no-referrer',
  'x-content-type-options': 'nosniff',
  'x-frame-options': 'DENY',
};
const responseHeaders = (extra = {}) => ({ ...securityHeaders, ...extra });

async function jsonBody(request) {
  let body = '';
  for await (const chunk of request) {
    body += chunk;
    if (body.length > 1024) throw new Error('Request too large');
  }
  return JSON.parse(body || '{}');
}

const server = createServer(async (request, response) => {
  if (request.url?.split('?')[0] === '/data/snapshot.json' && request.method === 'GET') {
    try {
      const snapshot = await collect();
      response.writeHead(200, responseHeaders({ 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }));
      response.end(JSON.stringify(snapshot));
    } catch (error) {
      response.writeHead(500, responseHeaders({ 'content-type': 'application/json; charset=utf-8' }));
      response.end(JSON.stringify({ error: error.message }));
    }
    return;
  }
  if (request.url === '/api/refresh' && request.method === 'POST') {
    try {
      const snapshot = await collect();
      response.writeHead(200, responseHeaders({ 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }));
      response.end(JSON.stringify(snapshot));
    } catch (error) {
      response.writeHead(500, responseHeaders({ 'content-type': 'application/json; charset=utf-8' }));
      response.end(JSON.stringify({ error: error.message }));
    }
    return;
  }
  if (request.url === '/api/airadar/sync' && request.method === 'POST') {
    if (readOnly) {
      response.writeHead(403, responseHeaders({ 'content-type': 'application/json; charset=utf-8' }));
      response.end(JSON.stringify({ error: 'Mission Control is in read-only sharing mode.' }));
      return;
    }
    try {
      await syncAiradar();
      await evaluateAiradar();
      const snapshot = await collect();
      response.writeHead(200, responseHeaders({ 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }));
      response.end(JSON.stringify(snapshot));
    } catch (error) {
      response.writeHead(503, responseHeaders({ 'content-type': 'application/json; charset=utf-8' }));
      response.end(JSON.stringify({ error: 'AIRadar sync or AI evaluation failed.' }));
    }
    return;
  }
  const archiveMatch = request.url?.match(/^\/api\/projects\/([a-z0-9-]+)\/archive$/);
  if (archiveMatch && request.method === 'POST') {
    if (readOnly) {
      response.writeHead(403, responseHeaders({ 'content-type': 'application/json; charset=utf-8' }));
      response.end(JSON.stringify({ error: 'Mission Control is in read-only sharing mode.' }));
      return;
    }
    try {
      const body = await jsonBody(request);
      if (typeof body.archived !== 'boolean') throw new Error('archived must be boolean');
      const snapshot = await setProjectArchived(archiveMatch[1], body.archived);
      response.writeHead(200, responseHeaders({ 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }));
      response.end(JSON.stringify(snapshot));
    } catch (error) {
      response.writeHead(400, responseHeaders({ 'content-type': 'application/json; charset=utf-8' }));
      response.end(JSON.stringify({ error: error.message }));
    }
    return;
  }
  const urlPath = decodeURIComponent((request.url || '/').split('?')[0]);
  const safePath = normalize(urlPath).replace(/^(\.\.(\/|\\|$))+/, '');
  let filePath = resolve(root, `.${safePath}`);
  if (!filePath.startsWith(root)) { response.writeHead(403, responseHeaders()); response.end('Forbidden'); return; }
  try {
    if (urlPath === '/' || !(await access(filePath).then(() => true).catch(() => false))) filePath = join(root, 'index.html');
    response.writeHead(200, responseHeaders({ 'content-type': types[extname(filePath)] || 'application/octet-stream', 'cache-control': extname(filePath) === '.html' || extname(filePath) === '.json' ? 'no-store' : 'public, max-age=31536000, immutable' }));
    createReadStream(filePath).pipe(response);
  } catch {
    response.writeHead(404, responseHeaders()); response.end('Not found');
  }
});

server.listen(port, host, () => console.log(`Mission Control is ${readOnly ? 'read-only' : 'private'} on http://${host}:${port}`));
