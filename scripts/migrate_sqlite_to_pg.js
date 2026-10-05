/**
 * CampusCare - SQLite to PostgreSQL Data Migration Script
 * Migrates existing data from local SQLite database (database.db) to PostgreSQL (Netlify Database / Neon).
 *
 * Usage:
 *   node scripts/migrate_sqlite_to_pg.js
 *
 * Environment variables:
 *   NETLIFY_DB_URL or DATABASE_URL : PostgreSQL connection string
 *   DATABASE_PATH (optional)       : Path to SQLite database (default: database.db)
 */

import path from 'path';
import fs from 'fs';
import pkg from 'pg';
const { Pool } = pkg;
import Database from 'better-sqlite3';
import { initDb } from '../netlify/functions/utils/db.mjs';

const pgUrl = process.env.NETLIFY_DB_URL || process.env.DATABASE_URL;

if (!pgUrl) {
  console.error("ERROR: No PostgreSQL connection string found.");
  console.error("Please set NETLIFY_DB_URL or DATABASE_URL before running this script.");
  console.error("Example: set DATABASE_URL=postgres://user:password@host:port/dbname && node scripts/migrate_sqlite_to_pg.js");
  process.exit(1);
}

const sqlitePath = path.resolve(process.cwd(), process.env.DATABASE_PATH || 'database.db');
if (!fs.existsSync(sqlitePath)) {
  console.error(`ERROR: SQLite database file not found at: ${sqlitePath}`);
  process.exit(1);
}

const sqlite = new Database(sqlitePath);
const pgPool = new Pool({
  connectionString: pgUrl,
  ssl: pgUrl.includes('localhost') ? false : { rejectUnauthorized: false }
});

async function migrate() {
  console.log("=== CampusCare Data Migration: SQLite -> PostgreSQL ===");
  console.log(`Source SQLite: ${sqlitePath}`);
  console.log(`Target PostgreSQL: ${pgUrl.split('@')[1] || 'Configured URL'}`);

  // 1. Ensure target schema is initialized
  console.log("\n1. Verifying and initializing target PostgreSQL schema...");
  await initDb();
  console.log("   Schema initialized successfully.");

  const client = await pgPool.connect();

  try {
    await client.query("BEGIN");

    // 2. Migrate Students
    console.log("\n2. Migrating 'students' table...");
    const students = sqlite.prepare("SELECT * FROM students").all();
    let studentCount = 0;
    for (const s of students) {
      await client.query(`
        INSERT INTO students (student_id, name, email, password)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (email) DO UPDATE
        SET name = EXCLUDED.name, password = EXCLUDED.password
      `, [s.student_id, s.name, s.email, s.password]);
      studentCount++;
    }
    await client.query(`SELECT setval('students_student_id_seq', (SELECT COALESCE(MAX(student_id), 1) FROM students))`);
    console.log(`   Migrated ${studentCount} students.`);

    // 3. Migrate Admins
    console.log("\n3. Migrating 'admins' table...");
    const admins = sqlite.prepare("SELECT * FROM admins").all();
    let adminCount = 0;
    for (const a of admins) {
      await client.query(`
        INSERT INTO admins (admin_id, username, password, role, department)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (username) DO UPDATE
        SET password = EXCLUDED.password, role = EXCLUDED.role, department = EXCLUDED.department
      `, [a.admin_id, a.username, a.password, a.role || 'Super Admin', a.department || '']);
      adminCount++;
    }
    await client.query(`SELECT setval('admins_admin_id_seq', (SELECT COALESCE(MAX(admin_id), 1) FROM admins))`);
    console.log(`   Migrated ${adminCount} admins.`);

    // 4. Migrate Complaints
    console.log("\n4. Migrating 'complaints' table...");
    const complaints = sqlite.prepare("SELECT * FROM complaints").all();
    let complaintCount = 0;
    for (const c of complaints) {
      await client.query(`
        INSERT INTO complaints (
          complaint_id, ticket_id, student_id, category, description, photo_path,
          block, floor_no, room_no, corridor_side, nearby_area, additional_location,
          location, priority, status, date, last_updated, first_responded_at,
          transport_type, bus_number, route, pickup_drop_point, transport_complaint_type,
          department, forwarded_to, forwarded_by, forwarded_at,
          resolved_by_department, department_resolution_time, student_confirmation,
          student_confirmation_time, final_resolution_time, original_complaint_id,
          regeneration_count, regenerated_by_student, regeneration_reason,
          previous_resolution_details, complaint_fingerprint, affected_student_count,
          group_id, is_primary
        ) VALUES (
          $1, $2, $3, $4, $5, $6,
          $7, $8, $9, $10, $11, $12,
          $13, $14, $15, $16, $17, $18,
          $19, $20, $21, $22, $23,
          $24, $25, $26, $27,
          $28, $29, $30,
          $31, $32, $33,
          $34, $35, $36,
          $37, $38, $39,
          $40, $41
        )
        ON CONFLICT (complaint_id) DO UPDATE
        SET ticket_id = EXCLUDED.ticket_id, status = EXCLUDED.status, last_updated = EXCLUDED.last_updated
      `, [
        c.complaint_id, c.ticket_id || '', c.student_id, c.category, c.description, c.photo_path || '',
        c.block || '', c.floor_no || '', c.room_no || '', c.corridor_side || '', c.nearby_area || '', c.additional_location || '',
        c.location, c.priority, c.status, c.date, c.last_updated || '', c.first_responded_at || '',
        c.transport_type || '', c.bus_number || '', c.route || '', c.pickup_drop_point || '', c.transport_complaint_type || '',
        c.department || '', c.forwarded_to || '', c.forwarded_by || '', c.forwarded_at || '',
        c.resolved_by_department || 0, c.department_resolution_time || '', c.student_confirmation || '',
        c.student_confirmation_time || '', c.final_resolution_time || '', c.original_complaint_id || null,
        c.regeneration_count || 0, c.regenerated_by_student || 0, c.regeneration_reason || '',
        c.previous_resolution_details || '', c.complaint_fingerprint || '', c.affected_student_count || 1,
        c.group_id || null, Boolean(c.is_primary ?? true)
      ]);
      complaintCount++;
    }
    await client.query(`SELECT setval('complaints_complaint_id_seq', (SELECT COALESCE(MAX(complaint_id), 1) FROM complaints))`);
    console.log(`   Migrated ${complaintCount} complaints.`);

    // 5. Migrate Complaint Reporters
    console.log("\n5. Migrating 'complaint_reporters' table...");
    const reporters = sqlite.prepare("SELECT * FROM complaint_reporters").all();
    let reporterCount = 0;
    for (const r of reporters) {
      await client.query(`
        INSERT INTO complaint_reporters (id, complaint_id, student_id, student_email, reported_at)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (complaint_id, student_id) DO NOTHING
      `, [r.id, r.complaint_id, r.student_id, r.student_email || '', r.reported_at]);
      reporterCount++;
    }
    await client.query(`SELECT setval('complaint_reporters_id_seq', (SELECT COALESCE(MAX(id), 1) FROM complaint_reporters))`);
    console.log(`   Migrated ${reporterCount} complaint reporters.`);

    // 6. Migrate Complaint Status History
    console.log("\n6. Migrating 'complaint_status_history' table...");
    const history = sqlite.prepare("SELECT * FROM complaint_status_history").all();
    let historyCount = 0;
    for (const h of history) {
      await client.query(`
        INSERT INTO complaint_status_history (history_id, complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (history_id) DO NOTHING
      `, [h.history_id, h.complaint_id, h.admin_id, h.admin_name, h.old_status, h.new_status, h.remarks, h.changed_at]);
      historyCount++;
    }
    if (historyCount > 0) {
      await client.query(`SELECT setval('complaint_status_history_history_id_seq', (SELECT COALESCE(MAX(history_id), 1) FROM complaint_status_history))`);
    }
    console.log(`   Migrated ${historyCount} status history entries.`);

    // 7. Migrate Admin Notes
    console.log("\n7. Migrating 'admin_notes' table...");
    const notes = sqlite.prepare("SELECT * FROM admin_notes").all();
    let noteCount = 0;
    for (const n of notes) {
      await client.query(`
        INSERT INTO admin_notes (note_id, complaint_id, admin_id, admin_name, note, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (note_id) DO NOTHING
      `, [n.note_id, n.complaint_id, n.admin_id, n.admin_name, n.note, n.created_at]);
      noteCount++;
    }
    if (noteCount > 0) {
      await client.query(`SELECT setval('admin_notes_note_id_seq', (SELECT COALESCE(MAX(note_id), 1) FROM admin_notes))`);
    }
    console.log(`   Migrated ${noteCount} admin notes.`);

    // 8. Migrate SOC Audit Logs
    console.log("\n8. Migrating 'soc_audit_logs' table...");
    const socLogs = sqlite.prepare("SELECT * FROM soc_audit_logs").all();
    let socCount = 0;
    for (const l of socLogs) {
      await client.query(`
        INSERT INTO soc_audit_logs (log_id, event_type, user_email, complaint_id, department, severity, timestamp, details)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (log_id) DO NOTHING
      `, [l.log_id, l.event_type, l.user_email, l.complaint_id, l.department, l.severity, l.timestamp, l.details]);
      socCount++;
    }
    if (socCount > 0) {
      await client.query(`SELECT setval('soc_audit_logs_log_id_seq', (SELECT COALESCE(MAX(log_id), 1) FROM soc_audit_logs))`);
    }
    console.log(`   Migrated ${socCount} SOC audit logs.`);

    // 9. Migrate Active Complaint Slots
    console.log("\n9. Migrating 'active_complaint_slots' table...");
    const slots = sqlite.prepare("SELECT * FROM active_complaint_slots").all();
    let slotCount = 0;
    for (const sl of slots) {
      await client.query(`
        INSERT INTO active_complaint_slots (slot_id, slot_key, complaint_id, student_id, created_at)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (slot_key) DO NOTHING
      `, [sl.slot_id, sl.slot_key, sl.complaint_id, sl.student_id, sl.created_at]);
      slotCount++;
    }
    if (slotCount > 0) {
      await client.query(`SELECT setval('active_complaint_slots_slot_id_seq', (SELECT COALESCE(MAX(slot_id), 1) FROM active_complaint_slots))`);
    }
    console.log(`   Migrated ${slotCount} active complaint slots.`);

    await client.query("COMMIT");
    console.log("\n SUCCESS! All data migrated to PostgreSQL successfully.");

  } catch (err) {
    await client.query("ROLLBACK");
    console.error("\n MIGRATION FAILED! Rolled back transaction.");
    console.error(err);
    process.exit(1);
  } finally {
    client.release();
    await pgPool.end();
  }
}

migrate();
