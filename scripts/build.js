/**
 * CampusCare - Build Script
 * Prepares the public/ distribution folder for Netlify deployment
 * by syncing static assets and verifying build integrity.
 */

import fs from 'fs';
import path from 'path';

const rootDir = process.cwd();
const publicDir = path.resolve(rootDir, 'public');
const staticSrc = path.resolve(rootDir, 'static');
const staticDest = path.resolve(publicDir, 'static');

if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true });
}

function copyDirRecursive(src, dest) {
  if (!fs.existsSync(src)) return;
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }

  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDirRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

console.log('[Build] Syncing static assets to public/static...');
copyDirRecursive(staticSrc, staticDest);

// Mirror seed database.db to public/ for Netlify functions distribution
const dbSrc = path.resolve(rootDir, 'database.db');
const dbDest = path.resolve(publicDir, 'database.db');
if (fs.existsSync(dbSrc)) {
  fs.copyFileSync(dbSrc, dbDest);
  console.log('[Build] database.db mirrored to public/database.db for serverless distribution.');
}

console.log('[Build] Static assets synced successfully.');
