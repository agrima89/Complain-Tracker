#!/usr/bin/env node
/**
 * Reset a student's password in the LOCAL SQLite databases (development only).
 *
 * Usage:  node scripts/reset_password.mjs <email>
 * You'll be asked for the new password (input is hidden).
 *
 * Updates both ./database.db and the copy `netlify dev` uses in the OS temp folder.
 * For production (PostgreSQL) use an admin flow instead; this script never touches it.
 */
import fs from 'fs';
import os from 'os';
import path from 'path';
import readline from 'readline';
import Database from 'better-sqlite3';
import { hashPassword } from '../netlify/functions/utils/auth.mjs';

const email = (process.argv[2] || '').trim().toLowerCase();
if (!email) {
  console.error('Usage: node scripts/reset_password.mjs <email>');
  process.exit(1);
}

const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: !!process.stdin.isTTY });
let prompt = '';
// Show the prompt but hide what is typed.
rl._writeToOutput = (s) => { if (s.includes(prompt)) rl.output.write(prompt); };
const lines = rl[Symbol.asyncIterator]();
const askHidden = async (question) => {
  prompt = question;
  process.stdout.write(question);
  const { value } = await lines.next();
  process.stdout.write('\n');
  return value ?? '';
};

const password = await askHidden('New password (min 8 characters): ');
if (password.length < 8) {
  console.error('Password must be at least 8 characters.');
  process.exit(1);
}
const confirm = await askHidden('Repeat new password: ');
rl.close();
if (confirm !== password) {
  console.error('Passwords do not match.');
  process.exit(1);
}

const hash = hashPassword(password);
const candidates = [
  process.env.DATABASE_PATH,
  path.resolve('database.db'),
  path.join(os.tmpdir(), 'database.db')
].filter(Boolean);

let updated = 0;
for (const file of [...new Set(candidates)]) {
  if (!fs.existsSync(file)) continue;
  const db = new Database(file);
  const res = db.prepare('UPDATE students SET password = ? WHERE LOWER(email) = ?').run(hash, email);
  db.close();
  console.log(`${file}: ${res.changes ? 'updated' : 'no student with that email'}`);
  updated += res.changes;
}

if (!updated) {
  console.error('No matching student found. Check the email, or register a new account.');
  process.exit(1);
}
console.log('Done. Sign in with the new password.');
