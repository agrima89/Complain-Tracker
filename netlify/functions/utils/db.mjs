/**
 * CampusCare - Unified Database Module
 * Connects to PostgreSQL (Netlify Database / Neon / Supabase) when NETLIFY_DB_URL or DATABASE_URL is set,
 * with automatic local and serverless SQLite (/tmp) fallback for seamless Netlify serverless execution.
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';
import pkg from 'pg';
const { Pool } = pkg;
import Database from 'better-sqlite3';
import { hashPassword } from './auth.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PG_URL = process.env.NETLIFY_DB_URL || process.env.DATABASE_URL;
let pool = null;
let sqliteDb = null;

if (PG_URL) {
  pool = new Pool({
    connectionString: PG_URL,
    ssl: PG_URL.includes('localhost') ? false : { rejectUnauthorized: false }
  });
}

export function isPostgres() {
  return !!pool;
}

/**
 * Resolves the SQLite database path safely across environments:
 * - Uses DATABASE_PATH if explicitly defined
 * - In serverless environments (Netlify / AWS Lambda where /var/task is read-only), uses os.tmpdir()/database.db
 *   and copies the bundled seed database.db if available
 * - Falls back to local database.db in project root for local development
 */
function isDirWritable(dir) {
  try {
    const testFile = path.join(dir, `.write_probe_${process.pid}_${Date.now()}`);
    fs.writeFileSync(testFile, '1');
    fs.unlinkSync(testFile);
    return true;
  } catch {
    return false;
  }
}

/**
 * Resolves the SQLite database path safely across environments:
 * - Uses DATABASE_PATH if explicitly defined
 * - In serverless environments (Netlify / AWS Lambda where /var/task is read-only or when cwd is unwritable),
 *   uses os.tmpdir()/database.db and copies the bundled seed database.db if available
 * - Falls back to local database.db in project root for local development
 */
function resolveSqlitePath() {
  if (process.env.DATABASE_PATH) {
    return path.resolve(process.env.DATABASE_PATH);
  }

  // Detect Netlify Serverless / AWS Lambda environment or read-only filesystem
  const isCwdWritable = isDirWritable(process.cwd());
  const isServerless = !isCwdWritable || !!(
    process.env.NETLIFY ||
    process.env.AWS_LAMBDA_FUNCTION_NAME ||
    process.env.LAMBDA_TASK_ROOT ||
    process.env.CONTEXT ||
    process.env.DEPLOY_ID ||
    (process.cwd() && (process.cwd().startsWith('/var/task') || process.cwd().includes('netlify-functions')))
  );

  if (isServerless) {
    const tmpDbPath = path.join(os.tmpdir(), 'database.db');
    const tmpDir = path.dirname(tmpDbPath);
    if (!fs.existsSync(tmpDir)) {
      try { fs.mkdirSync(tmpDir, { recursive: true }); } catch (_) {}
    }

    if (!fs.existsSync(tmpDbPath)) {
      // Find candidate seed database.db files
      const candidates = [
        path.resolve(process.cwd(), 'database.db'),
        path.resolve(process.cwd(), 'public', 'database.db'),
        path.resolve(__dirname, 'database.db'),
        path.resolve(__dirname, '..', 'database.db'),
        path.resolve(__dirname, '..', '..', 'database.db'),
        path.resolve(__dirname, '..', '..', 'public', 'database.db'),
        path.resolve(process.env.LAMBDA_TASK_ROOT || '/var/task', 'database.db'),
        path.resolve(process.env.LAMBDA_TASK_ROOT || '/var/task', 'public', 'database.db')
      ];
      for (const cand of candidates) {
        if (fs.existsSync(cand)) {
          try {
            fs.copyFileSync(cand, tmpDbPath);
            console.log(`[db.mjs] Initialized serverless DB at ${tmpDbPath} from seed ${cand}`);
            break;
          } catch (e) {
            console.warn(`[db.mjs] Warning copying seed database from ${cand}:`, e.message);
          }
        }
      }
    }
    return tmpDbPath;
  }

  // Local development fallback
  return path.resolve(process.cwd(), 'database.db');
}

/**
 * Returns an active SQLite Database instance, lazily connecting and recovering
 * to os.tmpdir()/database.db if local directory is read-only.
 */
export function getSqliteDb() {
  if (sqliteDb) return sqliteDb;

  let dbPath = resolveSqlitePath();
  const dbDir = path.dirname(dbPath);
  if (!fs.existsSync(dbDir)) {
    try {
      fs.mkdirSync(dbDir, { recursive: true });
    } catch (_) {}
  }

  try {
    sqliteDb = new Database(dbPath);
    // Use DELETE journal mode in serverless or temp directories to avoid .shm / .wal lock issues
    const isTemp = dbPath.includes('tmp') || dbPath.includes('Temp') || !isDirWritable(path.dirname(dbPath));
    if (isTemp) {
      sqliteDb.pragma('journal_mode = DELETE');
    } else {
      sqliteDb.pragma('journal_mode = WAL');
    }
    sqliteDb.pragma('foreign_keys = ON');
    return sqliteDb;
  } catch (err) {
    console.error(`[db.mjs] Error opening database at ${dbPath}:`, err.message);

    // If opening failed (e.g. read-only filesystem), retry with os.tmpdir()/database.db
    const fallbackPath = path.join(os.tmpdir(), 'database.db');
    if (dbPath !== fallbackPath) {
      try {
        console.warn(`[db.mjs] Retrying fallback connection to ${fallbackPath}...`);
        const fallbackDir = path.dirname(fallbackPath);
        if (!fs.existsSync(fallbackDir)) {
          try { fs.mkdirSync(fallbackDir, { recursive: true }); } catch (_) {}
        }
        if (fs.existsSync(dbPath) && !fs.existsSync(fallbackPath)) {
          try { fs.copyFileSync(dbPath, fallbackPath); } catch (_) {}
        }
        sqliteDb = new Database(fallbackPath);
        sqliteDb.pragma('journal_mode = DELETE');
        sqliteDb.pragma('foreign_keys = ON');
        console.log('[db.mjs] Fallback SQLite connection established at:', fallbackPath);
        return sqliteDb;
      } catch (fallbackErr) {
        console.error('[db.mjs] Critical fallback error:', fallbackErr.message);
        throw fallbackErr;
      }
    }
    throw err;
  }
}

/**
 * Executes a SQL query with parameter normalization.
 * In code, write standard Postgres style: SELECT * FROM foo WHERE id = $1 AND name = $2
 * If running on SQLite, $1, $2 are automatically converted to ?
 */
export async function query(text, params = []) {
  if (pool) {
    const client = await pool.connect();
    try {
      const res = await client.query(text, params);
      return {
        rows: res.rows || [],
        rowCount: res.rowCount || 0,
        lastRowId: res.rows?.[0]?.id || res.rows?.[0]?.student_id || res.rows?.[0]?.complaint_id || null
      };
    } finally {
      client.release();
    }
  } else {
    const db = getSqliteDb();
    // SQLite execution: map $1, $2 to ? in order of appearance
    const matches = [...text.matchAll(/\$([0-9]+)/g)];
    let sqliteParams = params;
    if (matches.length > 0) {
      sqliteParams = matches.map(m => params[parseInt(m[1], 10) - 1]);
    }
    let convertedSql = text.replace(/\$([0-9]+)/g, '?');

    // Remove RETURNING clauses for standard SQLite unless supported, or handle gracefully
    const hasReturning = /RETURNING\s+([a-zA-Z0-9_, *]+)/i.test(convertedSql);
    const isSelect = /^\s*SELECT/i.test(convertedSql);

    if (isSelect || hasReturning) {
      try {
        const stmt = db.prepare(convertedSql);
        const rows = stmt.all(...sqliteParams);
        return {
          rows: rows || [],
          rowCount: rows.length,
          lastRowId: rows[0]?.id || rows[0]?.student_id || rows[0]?.complaint_id || null
        };
      } catch (err) {
        // If RETURNING failed on an older sqlite version
        if (hasReturning) {
          const strippedSql = convertedSql.replace(/RETURNING\s+([a-zA-Z0-9_, *]+)/i, '');
          const stmt = db.prepare(strippedSql);
          const info = stmt.run(...sqliteParams);
          return {
            rows: [{ id: info.lastInsertRowid }],
            rowCount: info.changes,
            lastRowId: info.lastInsertRowid
          };
        }
        throw err;
      }
    } else {
      const stmt = db.prepare(convertedSql);
      const info = stmt.run(...sqliteParams);
      return {
        rows: [],
        rowCount: info.changes,
        lastRowId: info.lastInsertRowid
      };
    }
  }
}

export async function initDb() {
  const isPg = isPostgres();
  const serialType = isPg ? 'SERIAL PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT';
  const textDefault = (val) => `TEXT DEFAULT '${val}'`;
  const boolType = isPg ? 'BOOLEAN DEFAULT TRUE' : 'INTEGER DEFAULT 1';

  // 1. Students
  await query(`
    CREATE TABLE IF NOT EXISTS students (
      student_id ${serialType},
      name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL
    )
  `);

  // 2. Complaints
  await query(`
    CREATE TABLE IF NOT EXISTS complaints (
      complaint_id ${serialType},
      ticket_id TEXT DEFAULT '',
      student_id INTEGER NOT NULL,
      category TEXT NOT NULL,
      description TEXT NOT NULL,
      photo_path TEXT DEFAULT '',
      block TEXT DEFAULT '',
      floor_no TEXT DEFAULT '',
      room_no TEXT DEFAULT '',
      corridor_side TEXT DEFAULT '',
      nearby_area TEXT DEFAULT '',
      additional_location TEXT DEFAULT '',
      location TEXT NOT NULL,
      priority TEXT NOT NULL,
      status TEXT NOT NULL,
      date TEXT NOT NULL,
      last_updated TEXT DEFAULT '',
      first_responded_at TEXT DEFAULT '',
      transport_type TEXT DEFAULT '',
      bus_number TEXT DEFAULT '',
      route TEXT DEFAULT '',
      pickup_drop_point TEXT DEFAULT '',
      transport_complaint_type TEXT DEFAULT '',
      department TEXT DEFAULT '',
      forwarded_to TEXT DEFAULT '',
      forwarded_by TEXT DEFAULT '',
      forwarded_at TEXT DEFAULT '',
      resolved_by_department INTEGER DEFAULT 0,
      department_resolution_time TEXT DEFAULT '',
      student_confirmation TEXT DEFAULT '',
      student_confirmation_time TEXT DEFAULT '',
      final_resolution_time TEXT DEFAULT '',
      original_complaint_id INTEGER,
      regeneration_count INTEGER DEFAULT 0,
      regenerated_by_student INTEGER DEFAULT 0,
      regeneration_reason TEXT DEFAULT '',
      previous_resolution_details TEXT DEFAULT '',
      complaint_fingerprint TEXT DEFAULT '',
      affected_student_count INTEGER DEFAULT 1,
      group_id INTEGER,
      is_primary ${boolType},
      assigned_authority TEXT DEFAULT '',
      resolution_remarks TEXT DEFAULT '',
      resolved_at TEXT DEFAULT ''
    )
  `);

  // 3. Admins
  await query(`
    CREATE TABLE IF NOT EXISTS admins (
      admin_id ${serialType},
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      role TEXT DEFAULT 'Super Admin',
      department TEXT DEFAULT ''
    )
  `);

  // 4. Status History
  await query(`
    CREATE TABLE IF NOT EXISTS complaint_status_history (
      history_id ${serialType},
      complaint_id INTEGER NOT NULL,
      admin_id INTEGER,
      admin_name TEXT DEFAULT 'System',
      changed_by TEXT DEFAULT 'System',
      old_status TEXT,
      previous_status TEXT,
      new_status TEXT NOT NULL,
      remarks TEXT DEFAULT '',
      comment TEXT DEFAULT '',
      changed_at TEXT NOT NULL
    )
  `);

  // 5. Admin Notes
  await query(`
    CREATE TABLE IF NOT EXISTS admin_notes (
      note_id ${serialType},
      complaint_id INTEGER NOT NULL,
      admin_id INTEGER NOT NULL,
      admin_name TEXT NOT NULL,
      note TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
  `);

  // 6. SOC Audit Logs
  await query(`
    CREATE TABLE IF NOT EXISTS soc_audit_logs (
      log_id ${serialType},
      event_type TEXT NOT NULL,
      user_email TEXT DEFAULT '',
      complaint_id TEXT DEFAULT '',
      department TEXT DEFAULT '',
      severity TEXT DEFAULT 'LOW',
      timestamp TEXT NOT NULL,
      details TEXT DEFAULT ''
    )
  `);

  // 7. Complaint Reporters
  await query(`
    CREATE TABLE IF NOT EXISTS complaint_reporters (
      id ${serialType},
      complaint_id INTEGER NOT NULL,
      student_id INTEGER NOT NULL,
      student_email TEXT DEFAULT '',
      reported_at TEXT NOT NULL,
      UNIQUE(complaint_id, student_id)
    )
  `);

  // 8. Active Complaint Slots
  await query(`
    CREATE TABLE IF NOT EXISTS active_complaint_slots (
      slot_id ${serialType},
      slot_key TEXT UNIQUE NOT NULL,
      complaint_id INTEGER NOT NULL,
      student_id INTEGER NOT NULL,
      created_at TEXT NOT NULL
    )
  `);

  // Safe Column Migration for existing tables
  const extraColumns = [
    { table: 'complaints', column: 'assigned_authority', type: "TEXT DEFAULT ''" },
    { table: 'complaints', column: 'resolution_remarks', type: "TEXT DEFAULT ''" },
    { table: 'complaints', column: 'resolved_at', type: "TEXT DEFAULT ''" },
    { table: 'complaint_status_history', column: 'changed_by', type: "TEXT DEFAULT 'System'" },
    { table: 'complaint_status_history', column: 'previous_status', type: "TEXT DEFAULT ''" },
    { table: 'complaint_status_history', column: 'comment', type: "TEXT DEFAULT ''" }
  ];

  for (const { table, column, type } of extraColumns) {
    try {
      await query(`ALTER TABLE ${table} ADD COLUMN ${column} ${type}`);
    } catch (_) {
      // Column already exists
    }
  }

  // Seed default admin and department admins if admins table is empty
  const adminCheck = await query(`SELECT COUNT(*) as count FROM admins`);
  const adminCount = parseInt(adminCheck.rows[0]?.count || 0, 10);
  if (adminCount === 0) {
    const adminPassword = process.env.ADMIN_PASSWORD || 'admin123';
    const hashed = hashPassword(adminPassword);
    await query(
      `INSERT INTO admins (username, password, role, department) VALUES ($1, $2, $3, $4)`,
      ['admin', hashed, 'Super Admin', '']
    );

    const deptAccounts = [
      ["electrical_admin", "electrical123", "HOD", "Electrical"],
      ["cleaning_admin", "cleaning123", "HOD", "Cleaning"],
      ["classroom_admin", "classroom123", "HOD", "Classroom"],
      ["hostel_admin", "hostel123", "HOD", "Hostel"],
      ["wifi_admin", "wifi123", "HOD", "Wi-Fi/Internet"],
      ["library_admin", "library123", "HOD", "Library"],
      ["infra_admin", "infra123", "HOD", "Infrastructure"],
      ["transport_admin", "transport123", "HOD", "Transport"],
      ["other_admin", "other123", "HOD", "Other"]
    ];

    for (const [u, p, r, d] of deptAccounts) {
      await query(
        `INSERT INTO admins (username, password, role, department) VALUES ($1, $2, $3, $4)`,
        [u, hashPassword(p), r, d]
      );
    }
  }

  // Seed default students if students table is empty
  const studentCheck = await query(`SELECT COUNT(*) as count FROM students`);
  const studentCount = parseInt(studentCheck.rows[0]?.count || 0, 10);
  if (studentCount === 0) {
    const initialStudents = [
      ["Aryan Sharma", "aryan99@culkomail.in", hashPassword("Pass@12345")],
      ["Agrima Bajpai", "bajpaiagrima89@gmail.com", hashPassword("12345")],
      ["Agrima", "agrima@gmail.com", hashPassword("12345")],
      ["Mayank Awasthi", "mayankawas@culkomail.in", hashPassword("1234")]
    ];
    for (const [sName, sEmail, sPass] of initialStudents) {
      try {
        await query(
          `INSERT INTO students (name, email, password) VALUES ($1, $2, $3)`,
          [sName, sEmail, sPass]
        );
      } catch (_) {}
    }
  }
}
