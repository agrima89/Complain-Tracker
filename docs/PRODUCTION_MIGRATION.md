# Production database migration and release checklist

## Current state

The Netlify serverless functions can use PostgreSQL through `NETLIFY_DB_URL` or `DATABASE_URL`. SQLite is suitable for local development, but a SQLite file inside a serverless function or `/tmp` is not durable shared production storage. Do not deploy a database migration until a persistent PostgreSQL database is provisioned and verified.

The repository's root `database.db` is deliberately retained for now as a migration source. Do not delete it, overwrite it, or clear complaint rows before taking and verifying a backup and migrating the records.

## Required sequence

1. **Freeze risky changes.** Keep the security pull request separate from `main` until a persistent database is ready. Do not merge this branch while the production database URL is missing.
2. **Make a protected backup.** On the machine holding the authoritative SQLite database, stop writes briefly and make a dated copy of `database.db`. Also back up the `uploads/` evidence files. Restrict access to both backups; they can contain student personal information and credentials.
3. **Provision PostgreSQL.** Use a managed PostgreSQL database and a least-privilege application user. Configure SSL and restrict database access. Never commit its connection string.
4. **Configure secrets in Netlify.** Set `NETLIFY_DB_URL` (or `DATABASE_URL`), a unique random `JWT_SECRET`, and a unique `ADMIN_PASSWORD` only if the first administrator must be initialized. Do not paste values into tickets, chat, source code, or build logs.
5. **Run migration from the protected source copy.** From a trusted local environment with Node dependencies installed, point `DATABASE_PATH` at the verified SQLite backup and set the PostgreSQL URL in the shell environment. Run `npm run migrate:pg`. Never run a migration against the production database until a backup exists and the target has been reviewed.
6. **Verify counts and relationships.** Compare counts for students, admins, complaints, complaint reporters, status history, admin notes, audit logs, and active complaint slots. Check a sample of ticket IDs, statuses, duplicate reporter groups, and foreign-key relationships. Verify evidence files are copied to durable object storage and every stored evidence reference resolves.
7. **Test against the migrated target.** Verify student login and account isolation; complaint creation with required evidence; duplicate prevention and multi-reporter grouping; status changes; HOD department boundaries; evidence authorization; PDF downloads; logout/session expiry; and public statistics.
8. **Deploy only after review.** Run build and regression tests, then merge the pull request and monitor Netlify function logs. If checks fail, roll back the deploy without deleting either database.
9. **Remove exposed artifacts only after validation.** The repository is public and currently contains a root SQLite database. Treat any data or credentials committed in it as potentially exposed. Once the migration is verified and an approved clean copy is safely archived, remove the database and any evidence/backup artifacts from the repository and rotate passwords/session secrets. Removing the file from the latest commit does not remove old Git history; consider repository history cleanup and rotate credentials regardless.

## Important

- Never run cleanup SQL such as `DELETE FROM complaints` as part of deployment.
- Never rely on SQLite in `/tmp` for production records.
- Do not make the new production code live until the PostgreSQL connection and required secrets are configured.
- A successful static-site build does not prove the API, database, authentication, uploads, or PDFs work.
