/**
 * CampusCare - Build Script
 * public/ is the single source of truth for the Netlify site. This script only checks it.
 *
 * It used to copy the legacy Flask static/ folder into public/static, which silently replaced
 * newer files (auth-state.js, auth-page.js, auth-page.css) with stale copies on every deploy.
 * The Flask app keeps its own static/ folder; never copy it into public/.
 */

import fs from 'fs';
import path from 'path';

const rootDir = process.cwd();
const publicDir = path.resolve(rootDir, 'public');
const problems = [];

// 1. Every /static/... asset referenced by a page must exist.
const pages = fs.readdirSync(publicDir).filter(f => f.endsWith('.html'));
const OPTIONAL = new Set(['/static/video/campus.mp4']); // home page falls back to a photo
for (const page of pages) {
  const html = fs.readFileSync(path.join(publicDir, page), 'utf8');
  for (const [, ref] of html.matchAll(/(?:src|href)="(\/static\/[^"?#]+)"/g)) {
    if (OPTIONAL.has(ref)) continue;
    if (!fs.existsSync(path.join(publicDir, ref))) problems.push(`${page} references missing ${ref}`);
  }
}

// 2. Nothing private may be published.
for (const forbidden of ['database.db', 'database_backup.db', '.env']) {
  if (fs.existsSync(path.join(publicDir, forbidden))) problems.push(`public/${forbidden} must not be deployed`);
}

if (problems.length) {
  console.error('[Build] Failed:\n  ' + problems.join('\n  '));
  process.exit(1);
}
console.log(`[Build] OK: ${pages.length} pages checked, all referenced assets present.`);
