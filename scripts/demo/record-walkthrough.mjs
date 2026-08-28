import { mkdir, readdir, rename } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';

const root = resolve(import.meta.dirname, '../..');
const output = resolve(root, '.derived', 'demo-output');
const videoOutput = resolve(output, 'raw');
await mkdir(videoOutput, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  deviceScaleFactor: 1,
  colorScheme: 'dark',
  reducedMotion: 'no-preference',
  recordVideo: { dir: videoOutput, size: { width: 1280, height: 720 } },
});
const page = await context.newPage();
await page.addInitScript(() => {
  addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = `
      .demo-cursor { position: fixed; z-index: 2147483647; width: 22px; height: 22px; left: 50%; top: 50%; border: 2px solid rgba(255,255,255,.96); border-radius: 50%; pointer-events: none; transform: translate(-50%,-50%); box-shadow: 0 0 0 4px rgba(125,166,255,.18), 0 4px 18px rgba(0,0,0,.55); transition: width 120ms ease, height 120ms ease, background 120ms ease; }
      .demo-cursor.down { width: 15px; height: 15px; background: rgba(119,224,189,.62); }
      .demo-click-ring { position: fixed; z-index: 2147483646; width: 20px; height: 20px; border: 2px solid rgba(119,224,189,.8); border-radius: 50%; pointer-events: none; transform: translate(-50%,-50%); animation: demo-ring 520ms ease-out forwards; }
      @keyframes demo-ring { to { width: 58px; height: 58px; opacity: 0; } }
    `;
    document.head.append(style);
    const cursor = document.createElement('div');
    cursor.className = 'demo-cursor';
    document.body.append(cursor);
    addEventListener('mousemove', (event) => {
      cursor.style.left = `${event.clientX}px`;
      cursor.style.top = `${event.clientY}px`;
    }, { passive: true });
    addEventListener('mousedown', (event) => {
      cursor.classList.add('down');
      const ring = document.createElement('div');
      ring.className = 'demo-click-ring';
      ring.style.left = `${event.clientX}px`;
      ring.style.top = `${event.clientY}px`;
      document.body.append(ring);
      setTimeout(() => ring.remove(), 600);
    });
    addEventListener('mouseup', () => cursor.classList.remove('down'));
  });
});

const pause = (milliseconds) => page.waitForTimeout(milliseconds);
async function glideTo(locator, duration = 850) {
  const box = await locator.boundingBox();
  if (!box) throw new Error('Target is not visible');
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: Math.max(12, Math.round(duration / 35)) });
}
async function clickSmooth(locator) {
  await glideTo(locator);
  await pause(250);
  await locator.click();
}

await page.goto('http://127.0.0.1:4173/', { waitUntil: 'domcontentloaded' });
await page.locator('h1').waitFor({ state: 'visible' });
await page.mouse.move(980, 180);
await pause(7000);

await page.mouse.wheel(0, 390);
await pause(2600);
await page.mouse.wheel(0, -390);
await pause(1100);
await clickSmooth(page.getByRole('button', { name: 'Atlas', exact: true }));
await page.getByRole('heading', { name: 'The Atlas' }).waitFor({ state: 'visible' });
await pause(6000);

const contextNode = page.getByRole('button', { name: 'Open Context engineering' });
await clickSmooth(contextNode);
await pause(5200);

await clickSmooth(page.getByRole('link', { name: /Explore Observatory/ }));
await page.getByRole('heading', { name: 'Explore Observatory' }).waitFor({ state: 'visible' });
await pause(5600);

await clickSmooth(page.getByRole('button', { name: 'Skills', exact: true }));
await pause(3900);
const search = page.getByRole('searchbox', { name: 'Search this view…' });
await glideTo(search);
await search.fill('handoff');
await pause(4300);
await search.fill('');
await pause(900);

await clickSmooth(page.getByRole('button', { name: 'Operating Model', exact: true }));
await pause(9000);

await clickSmooth(page.getByRole('link', { name: 'Back to command center', exact: true }));
await page.getByRole('heading', { name: 'Observatory command center.' }).waitFor({ state: 'visible' });
await pause(5500);

await page.evaluate(() => {
  const close = document.createElement('section');
  close.setAttribute('aria-label', 'Observatory closing message');
  close.style.cssText = 'position:fixed;inset:0;z-index:9999;display:grid;place-content:center;text-align:center;background:radial-gradient(circle at 50% 35%,rgba(77,91,180,.34),rgba(5,8,15,.97) 58%);color:#f3f6ff;opacity:0;transition:opacity 900ms ease;font-family:Inter,ui-sans-serif,system-ui,sans-serif';
  close.innerHTML = '<div style="font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:#77e0bd;font-weight:800;margin-bottom:20px">Observatory</div><div style="font-size:48px;line-height:1.08;font-weight:750;letter-spacing:-.045em;max-width:900px">Your agents can change.<br>Your useful memory does not have to.</div><div style="margin-top:26px;color:#9dadc4;font-size:17px">Clone it · Point an agent at AGENTS.md · Build your own</div>';
  document.body.append(close);
  requestAnimationFrame(() => { close.style.opacity = '1'; });
});
await pause(6500);

const video = page.video();
await context.close();
await browser.close();
const rawPath = await video.path();
const finalRawPath = resolve(output, 'observatory-walkthrough-raw.webm');
await rename(rawPath, finalRawPath);

// Keep the raw directory predictable and report unexpected leftovers.
const leftovers = await readdir(videoOutput);
if (leftovers.length) console.warn(`Raw video directory still contains: ${leftovers.join(', ')}`);
console.log(finalRawPath);
