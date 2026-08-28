import { readFile, stat } from 'node:fs/promises';
import { basename, isAbsolute, join, relative, resolve } from 'node:path';

export async function activeReportsRoot(outputRoot) {
  try {
    const pointer = JSON.parse(await readFile(join(outputRoot, 'current.json'), 'utf8'));
    if (!/^[a-zA-Z0-9._-]+$/.test(pointer.generationId)) throw new Error('AIRadar generation pointer is invalid');
    const candidate = resolve(outputRoot, 'generations', pointer.generationId);
    const generations = resolve(outputRoot, 'generations');
    const contained = relative(generations, candidate);
    if (!contained || contained.startsWith('..') || isAbsolute(contained)) throw new Error('AIRadar generation pointer escapes its store');
    if (!(await stat(join(candidate, 'sync-meta.json'))).isFile()) throw new Error('AIRadar generation is incomplete');
    return candidate;
  } catch (error) {
    if (error?.code === 'ENOENT' && String(error.path || '').endsWith('current.json')) return outputRoot;
    throw error;
  }
}

export function safeGenerationId(metadata = {}) {
  const run = Number.isInteger(metadata.runNumber) ? metadata.runNumber : 'manual';
  const sha = String(metadata.headSha || 'local').replace(/[^a-zA-Z0-9]/g, '').slice(0, 16) || 'local';
  return `${run}-${sha}-${Date.now()}`;
}

export const reportName = (value) => basename(value);
