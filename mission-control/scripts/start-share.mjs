import { spawn } from 'node:child_process';

const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const env = { ...process.env, MC_READ_ONLY: '1' };

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { env, stdio: 'inherit' });
    child.on('error', reject);
    child.on('close', (code) => code === 0 ? resolve() : reject(new Error(`${command} exited with ${code}`)));
  });
}

await run(npm, ['run', 'refresh']);
await run(npm, ['run', 'build']);
await run(process.execPath, ['server.mjs']);
