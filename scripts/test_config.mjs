import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const root = process.cwd();
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

const pkg = JSON.parse(read('package.json'));
const netlify = read('netlify.toml');
const auth = read('netlify/functions/utils/auth.mjs');
const db = read('netlify/functions/utils/db.mjs');
const build = read('scripts/build.js');
const studentLogin = read('public/login.html');
const adminLogin = read('public/admin-login.html');
const envExample = read('.env.example');
const readme = read('README.md');

assert.equal(pkg.type, 'module', 'project must use ES modules');
assert.match(netlify, /publish\s*=\s*"public"/, 'Netlify publish directory must be public');
assert.match(netlify, /functions\s*=\s*"netlify\/functions"/, 'Netlify function directory must be configured');
assert.match(auth, /configuredJwtSecret/, 'JWT secret must be configured explicitly in production');
assert.match(auth, /secure: process\.env\.NODE_ENV === 'production'/, 'session cookie must be Secure in production');
assert.match(db, /persistent PostgreSQL connection is required in production/, 'production must not silently use ephemeral SQLite');
assert.match(db, /Fresh database has no administrators/, 'fresh database must not seed a predictable admin password');
assert.doesNotMatch(db, /electrical123|cleaning123|classroom123|hostel123|wifi123|library123|transport123|other123/, 'department demo passwords must not be seeded');
assert.doesNotMatch(studentLogin, /Demo Student Account|Pass@12345|aryan99@culkomail\.in/, 'student demo credentials must not be public');
assert.doesNotMatch(adminLogin, /Demo Admin Account|admin123/, 'admin demo credentials must not be public');
assert.doesNotMatch(envExample, /^[ \t]*(?:NETLIFY_DB_URL|DATABASE_URL)[ \t]*=[ \t]*[^ \t\r\n#]+/im, 'example environment file must not contain an active database URL');
assert.doesNotMatch(envExample, /^[ \t]*(?:JWT_SECRET|ADMIN_PASSWORD)[ \t]*=[ \t]*[^ \t\r\n#]+/im, 'example environment file must not contain active secrets');
assert.doesNotMatch(build, /copyFileSync\(dbSrc, dbDest\)/, 'build must not copy SQLite database into public assets');
assert.doesNotMatch(readme, /\| \*\*Admin Portal\*\* \| Administrator \| `admin` \| `admin123`/, 'README must not publish default admin credentials');
assert.equal(fs.existsSync(path.join(root, 'public/database.db')), false, 'public/database.db must not exist');

console.log('Campus Care configuration/security smoke tests passed.');
console.log('Note: these checks do not replace end-to-end API tests against a configured PostgreSQL database.');
