# CampusCare — Enhancement Plan

## 1. Analysis

### Basic idea
A campus complaint tracker. Students file complaints (category, block/room, priority, photo evidence) and track them. Admins triage them by department, update status, forward them, add notes, see a heatmap and stats, and export PDFs. It also has duplicate detection, "smart" category detection and a SOC log view.

### Current state: the problems
| Area | Finding |
|---|---|
| Two parallel stacks | Flask + Jinja (`app.py`, `templates/`, `static/`) **and** Netlify functions + static HTML (`netlify/`, `public/`). The CSS and JS are duplicated in `static/` and `public/static/`, so every fix has to be made twice. |
| Repo hygiene | ~150 `scratch_*.py`, `scratch/`, `test_*.py`, `patch_*.py`, `app_dump.txt`, PDFs and `database.db` are committed. This looks bad to any reviewer or recruiter. |
| Backend | No rate limiting on login, register or create. No shared request/response helper (each function repeats headers and JSON boilerplate). The category list has 16 overlapping values that map onto 8 departments. A SQLite `/tmp` fallback lives in the prod code path. There is no real test suite, only ad-hoc scripts. |
| Frontend | About 12k lines of CSS across 9 files with overlapping themes (`3d-campuscare`, `campus-world`, `campus-environment`, `landing`). Heavy background images and 3D effects make it slow and visually noisy. Every page has its own inline styles. |

## 2. Target design (inspired by Suraksha, not copied)
I'm borrowing the patterns, not the brand:
- A dark, near-black canvas. One warm accent (amber/orange) and severity colors (Critical/High/Medium/Low).
- A serif and sans heading mix, with the key phrase in the accent color.
- A **hero that shows the real product**: a live console mock with sample complaints.
- Numbered sections (`00 THE IDEA`, `01 …`) and a **4-step loop**: Report → Route → Resolve → Measure.
- An **explainable verdict**: each complaint card shows *why* it is flagged as a duplicate, urgent or a department match.
- **"Ask in plain English"** search for admins ("high priority hostel issues this week" → filters).
- Honest "measured, not claimed" stats from `public-stats`.
- An app-shell console: sidebar (Overview / Complaints / Heatmap / Evidence / Reports) and a greeting card ("Good morning, 7 complaints need a decision").

## 3. Implementation phases (in order of value per credit)

**Phase 0: Cleanup (cheap, high impact)**
- Move the scratch, patch and ad-hoc test files out of git and update `.gitignore`. Stop tracking `database.db`.
- Make the Netlify stack canonical. Mark Flask as legacy/local, or remove `templates/` and `static/` duplicates.

**Phase 1: Backend hardening**
- `utils/http.mjs`: a `json()` / `error()` helper, a method guard, and a `withAuth(role)` wrapper.
- Rate limiting (DB-backed attempts table) for auth and complaint creation.
- Input validation schema per endpoint, and one canonical category→department map in `utils/taxonomy.mjs`.
- Pagination and filter params on the list endpoints. Indexes on `status`, `department` and `created_at`.
- SLA fields (due-by per priority) plus an overdue flag. Audit log table for status changes, feeding the timeline.
- A real `node --test` suite for the utils plus the CI step.

**Phase 2: Design system**
- Replace the 9 CSS files with `tokens.css`, `base.css`, `components.css`, `app-shell.css` and `landing.css` (target under 3k lines).
- Light and dark tokens, focus rings, reduced-motion support, and mobile-first layouts.

**Phase 3: Pages**
1. Landing: hero plus console preview, the loop, live stats, "try it" (smart category detector running in the browser).
2. Auth pages: a single clean card layout.
3. Student app shell: dashboard, submit (stepper with live smart-detect plus a duplicate warning), my complaints, detail timeline.
4. Admin console: overview greeting, triage table with severity chips and reasons, plain-English filter, heatmap, detail with an audit timeline.

**Phase 4: Polish**
Skeleton loaders, empty states, toasts, a Lighthouse pass (≥90), an accessibility review, and a README with screenshots.

## Credit-saving approach
One phase per session. Reuse the existing APIs (the backend changes are additive). Rewrite the CSS rather than patch it.
