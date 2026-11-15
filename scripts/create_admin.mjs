#!/usr/bin/env node
/**
 * Create (or reset the password of) a staff account.
 *
 * Usage:
 *   node scripts/create_admin.mjs <username> [department]
 *
 *   department: one of Electrical, Cleaning, Classroom, Hostel, Wi-Fi/Internet, Library,
 *               Infrastructure, Transport, Other. Leave it out for an all-departments admin.
 *
 * You'll be asked for the password (hidden, at least 12 characters).
 * Uses the same database as the site: set DATABASE_URL (or NETLIFY_DB_URL) to the production
 * PostgreSQL URL to create accounts there; otherwise it writes to the local SQLite database.
 */
import readline from 'readline';
import { query, initDb } from '../netlify/functions/utils/db.mjs';
import { hashPassword } from '../netlify/functions/utils/auth.mjs';

const DEPARTMENTS = ['Electrical', 'Cleaning', 'Classroom', 'Hostel', 'Wi-Fi/Internet', 'Library', 'Infrastructure', 'Transport', 'Other'];
const username = (process.argv[2] || '').trim().toLowerCase();
const department = (process.argv[3] || '').trim();

if (!/^[a-z0-9._-]{3,40}$/.test(username)) {
  console.error('Usage: node scripts/create_admin.mjs <username> [department]\nUsername: 3-40 letters, digits, dot, dash or underscore.');
  process.exit(1);
}
if (department && !DEPARTMENTS.includes(department)) {
  console.error(`Unknown department "${department}". Use one of: ${DEPARTMENTS.join(', ')}`);
  process.exit(1);
}

const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: !!process.stdin.isTTY });
let prompt = '';
rl._writeToOutput = (s) => { if (s.includes(prompt)) rl.output.write(prompt); };
const lines = rl[Symbol.asyncIterator]();
const askHidden = async (q) => { prompt = q; process.stdout.write(q); const { value } = await lines.next(); process.stdout.write('\n'); return value ?? ''; };

const password = await askHidden('Password (min 12 characters): ');
if (password.length < 12) { console.error('Password must be at least 12 characters.'); process.exit(1); }
const confirm = await askHidden('Repeat password: ');
rl.close();
if (confirm !== password) { console.error('Passwords do not match.'); process.exit(1); }

await initDb();
const existing = await query('SELECT admin_id FROM admins WHERE LOWER(username) = $1', [username]);
if (existing.rows.length) {
  await query('UPDATE admins SET password = $1, department = $2 WHERE LOWER(username) = $3', [hashPassword(password), department, username]);
  console.log(`Updated "${username}" (${department || 'all departments'}).`);
} else {
  await query("INSERT INTO admins (username, password, role, department) VALUES ($1, $2, $3, $4)",
    [username, hashPassword(password), department ? 'Department Admin' : 'Super Admin', department]);
  console.log(`Created "${username}" (${department || 'all departments'}).`);
}
process.exit(0);
