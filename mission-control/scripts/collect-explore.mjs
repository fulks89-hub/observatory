import { access, readFile, readdir } from 'node:fs/promises';
import { basename, dirname, extname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { atomicWriteJson } from './atomic-io.mjs';

const appRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const observatoryRoot = resolve(process.env.OBSERVATORY_ROOT || join(appRoot, '..'));
const readOnly = process.env.MC_READ_ONLY === '1';
const canonicalDirs = ['projects', 'concepts', 'sources', 'research', 'people', 'ideas', 'questions', 'personal-operating-model'];

async function exists(path) {
  try { await access(path); return true; } catch { return false; }
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

function frontmatter(markdown) {
  const match = markdown.match(/^---\s*\n([\s\S]*?)\n---\s*(?:\n|$)/);
  if (!match) return {};
  const data = {};
  for (const line of match[1].split(/\r?\n/)) {
    const item = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!item) continue;
    let value = item[2].trim().replace(/^['"]|['"]$/g, '');
    if (value.startsWith('[') && value.endsWith(']')) {
      value = value.slice(1, -1).split(',').map((part) => part.trim().replace(/^['"]|['"]$/g, '')).filter(Boolean);
    }
    data[item[1]] = value;
  }
  return data;
}

function firstParagraph(markdown) {
  return markdown
    .replace(/^---[\s\S]*?---\s*/m, '')
    .split(/\n\s*\n/)
    .map((block) => block.trim())
    .find((block) => block && !block.startsWith('#'))
    ?.replace(/\[[^\]]+\]\([^)]+\)/g, (match) => match.replace(/\(([^)]+)\)/, ''))
    .replace(/[`*_>#]/g, '')
    .replace(/\s+/g, ' ')
    .slice(0, 280) || '';
}

function displayTitle(path, data) {
  return data.title || data.name || basename(path, '.md').replace(/[-_]/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

async function collectRecords() {
  const files = (await Promise.all(canonicalDirs.map((directory) => markdownFiles(join(observatoryRoot, directory))))).flat();
  return Promise.all(files.map(async (path) => {
    const markdown = await readFile(path, 'utf8');
    const data = frontmatter(markdown);
    return {
      path: relative(observatoryRoot, path).replace(/\\/g, '/'),
      type: data.type || 'Note',
      title: displayTitle(path, data),
      description: data.description || firstParagraph(markdown),
      tags: Array.isArray(data.tags) ? data.tags : [],
      status: data.project_status || data.status || '',
    };
  }));
}

async function collectIndex() {
  const path = join(observatoryRoot, 'index.md');
  if (!(await exists(path))) return [];
  const markdown = await readFile(path, 'utf8');
  const sections = [];
  let current = { title: 'Overview', items: [] };
  for (const line of markdown.split(/\r?\n/)) {
    const heading = line.match(/^##\s+(.+)$/);
    if (heading) {
      if (current.items.length) sections.push(current);
      current = { title: heading[1].trim(), items: [] };
      continue;
    }
    for (const match of line.matchAll(/\[([^\]]+)\]\(([^)]+)\)/g)) {
      current.items.push({ label: match[1], path: match[2] });
    }
  }
  if (current.items.length) sections.push(current);
  return sections;
}

async function collectSkills() {
  const files = await markdownFiles(join(observatoryRoot, 'skills'));
  const skillFiles = files.filter((path) => basename(path) === 'SKILL.md');
  return Promise.all(skillFiles.map(async (path) => {
    const markdown = await readFile(path, 'utf8');
    const data = frontmatter(markdown);
    return {
      path: relative(observatoryRoot, path).replace(/\\/g, '/'),
      name: data.name || basename(dirname(path)).replace(/[-_]/g, ' '),
      description: data.description || firstParagraph(markdown),
      vendor: relative(join(observatoryRoot, 'skills'), path).startsWith('vendor/') ? relative(join(observatoryRoot, 'skills', 'vendor'), path).split(/[\\/]/)[0] : '',
    };
  }));
}

async function collectRules() {
  const path = join(observatoryRoot, 'AGENTS.md');
  if (!(await exists(path))) return [];
  const markdown = await readFile(path, 'utf8');
  const core = markdown.match(/## Core rules\s*\n([\s\S]*?)(?=\n## |$)/)?.[1] || '';
  return core.split(/\r?\n/).map((line) => line.match(/^\s*(\d+)\.\s+(.+)$/)).filter(Boolean).map((match) => ({ number: Number(match[1]), text: match[2].trim() }));
}

async function collectPolicyKeys() {
  const path = join(observatoryRoot, '.observatory', 'policies.yaml');
  if (!(await exists(path))) return [];
  const yaml = await readFile(path, 'utf8');
  return yaml.split(/\r?\n/).map((line) => line.match(/^([A-Za-z0-9_-]+):\s*$/)?.[1]).filter(Boolean);
}

export async function collectExplore() {
  const [records, index, skills, rules, policyKeys] = await Promise.all([
    collectRecords(), collectIndex(), collectSkills(), collectRules(), collectPolicyKeys(),
  ]);
  const personal = records.filter((record) => ['OperatingPrinciple', 'OperatingPreference', 'OperatingLesson'].includes(record.type));
  const resources = records.filter((record) => !personal.includes(record));
  const explore = {
    generatedAt: new Date().toISOString(),
    readOnly,
    counts: {
      records: records.length,
      skills: skills.length,
      rules: rules.length,
      personalOperatingModel: personal.length,
    },
    skills,
    policyKeys,
    index: readOnly ? [] : index,
    resources: readOnly ? [] : resources,
    rules: readOnly ? [] : rules,
    personalOperatingModel: readOnly ? [] : personal,
    redactions: readOnly ? ['index', 'resources', 'rules', 'personalOperatingModel'] : [],
  };
  await atomicWriteJson(join(appRoot, 'public', 'data', 'explore.json'), explore);
  return explore;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const explore = await collectExplore();
  console.log(`Explore refreshed: ${explore.counts.records} records, ${explore.counts.skills} skills.`);
}
