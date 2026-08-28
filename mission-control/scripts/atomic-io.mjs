import { randomBytes } from 'node:crypto';
import { mkdir, open, rename, rm } from 'node:fs/promises';
import { dirname } from 'node:path';

export async function atomicWriteFile(path, contents, { mode = 0o600 } = {}) {
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.${process.pid}.${randomBytes(8).toString('hex')}.tmp`;
  let handle;
  try {
    handle = await open(temporary, 'wx', mode);
    await handle.writeFile(contents, 'utf8');
    await handle.sync();
    await handle.close();
    handle = null;
    await rename(temporary, path);
  } finally {
    await handle?.close().catch(() => {});
    await rm(temporary, { force: true }).catch(() => {});
  }
}

export function atomicWriteJson(path, value, options) {
  return atomicWriteFile(path, `${JSON.stringify(value, null, 2)}\n`, options);
}
