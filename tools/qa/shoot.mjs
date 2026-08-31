#!/usr/bin/env node
// shoot.mjs <url> <block> <out.png> [--width 1440] [--target 800] [--full]
// Screenshots the element [data-design="<block>"] of a running app, scaled so its longer edge ≈ --target px
// (same scale as the Figma reference PNGs). --full: whole page instead of one block.
// Setup once: cd teams/tools/qa && npm i && npx playwright install chromium
import { chromium } from "playwright";

const [url, block, out, ...rest] = process.argv.slice(2);
if (!url || !block || !out) { console.error("usage: shoot.mjs <url> <block> <out.png> [--width 1440] [--target 800] [--full]"); process.exit(2); }
const opt = (k, d) => { const i = rest.indexOf(k); return i >= 0 ? rest[i + 1] : d; };
const width = +opt("--width", 1440), target = +opt("--target", 800), full = rest.includes("--full");

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height: 900 }, deviceScaleFactor: Math.min(1, target / width) });
await page.goto(url, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts && document.fonts.ready);
if (full) { await page.screenshot({ path: out, fullPage: true }); }
else {
  const el = page.locator(`[data-design="${block}"]`).first();
  if (!(await el.count())) { console.error(`no element with data-design="${block}" at ${url}`); await browser.close(); process.exit(1); }
  await el.scrollIntoViewIfNeeded();
  await el.screenshot({ path: out });
}
await browser.close();
console.log(out);
