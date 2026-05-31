# Decisions

**Project Experience Explorer — CS 467 Spring 2026**

A record of significant technical and product decisions made during the project. Helps the team avoid relitigating settled questions and gives context for why things are the way they are.

---

## Format

Each entry includes what was decided, why, what alternatives were considered, and when it was decided.

---

## Decision Log

---

### 001 — Tech stack

**Date:** April 12, 2026
**Decision:** Flask (Python), PyMySQL, Jinja2 templates, Google App Engine, Google Cloud SQL

**Why:**
- All three team members are most comfortable with Python
- Caleb is actively using Flask in a concurrent cloud computing course — less context switching
- Jinja2 templates reduce complexity vs a separate React/Vue frontend
- App Engine is familiar from prior coursework
- Cloud SQL keeps everything in one GCP project

**Alternatives considered:**
- Django — rejected, too heavy for the scope of this project
- React frontend — rejected, adds complexity without meaningful benefit for a review platform
- OSU Engineering servers — rejected, VPN-only access would prevent public browsing

---

### 002 — Raw SQL over ORM

**Date:** April 12, 2026
**Decision:** Use PyMySQL with raw SQL. No SQLAlchemy or ORM.

**Why:**
- All three team members know raw SQL from CS 340
- PyMySQL is simpler and lighter — no extra abstraction layer
- Raw SQL gives more control and is easier to debug
- SQLAlchemy adds a learning curve with no meaningful benefit at this project's scale

**Alternatives considered:**
- SQLAlchemy ORM — rejected, unnecessary overhead
- SQLAlchemy Core (raw SQL via SQLAlchemy) — rejected, pointless middleman if we're writing raw SQL anyway

---

### 003 — Public browsing, ONID required to submit

**Date:** April 12, 2026
**Decision:** Anyone can browse and read reviews without logging in. ONID authentication is required to submit a review, rate helpfulness, or comment.

**Why:**
- Original spec says "display the info to visitors" — public browsing was always intended
- Requiring login to browse adds friction and reduces the app's usefulness
- Requiring login to submit prevents spam and anonymous abuse
- ONID auth is the natural fit since the audience is OSU students

**Alternatives considered:**
- OSU students only for viewing — rejected, enforcement requires auth which adds complexity and friction
- Fully open (no auth at all) — rejected, would allow spam reviews

---

### 004 — Same pseudonym per user across all reviews

**Date:** April 12, 2026
**Decision:** Each user gets one consistent pseudonym that appears on all their reviews.

**Why:**
- Builds reviewer credibility — readers can see all reviews from the same pseudonym and judge consistency
- This is how Ed Discussion does it, which was cited in the project spec as a reference
- Different pseudonym per review loses the credibility signal

**Alternatives considered:**
- Different pseudonym per review — rejected, loses credibility and doesn't match the Ed Discussion reference

---

### 005 — Term of experience shown, not submission date

**Date:** April 12, 2026
**Decision:** Reviews display the term when the experience happened (e.g. "Spring 2026"), not when the review was submitted.

**Why:**
- A review submitted in 2028 about a project done in Spring 2026 should show Spring 2026
- The submission date is irrelevant to the reader — they care about when the project was done
- This is explicitly called out in the project spec: "not necessarily the same when it was submitted by a student"

**Implementation note:** The reviews table needs a `term` field (user-entered) separate from `created_at` (auto-set on submission).

---

### 006 — Pre-populated project list via scraping and manual entry

**Date:** April 12, 2026
**Decision:** Seed the project list from the OSU Capstone portal using BeautifulSoup scraping and manual entry.

**Why:**
- Prevents duplicate/misspelled project names from reviewers typing freeform
- Scraping gets the bulk of the list automatically
- Manual entry covers anything the scraper misses or new projects added mid-term

**Status:** Complete — 28 CS467 projects seeded as of April 23, 2026. Scraper is idempotent (uses `ON DUPLICATE KEY UPDATE`) and safe to re-run.

---

### 007 — Google Cloud SQL for database hosting

**Date:** April 13, 2026
**Decision:** Use Google Cloud SQL (MySQL) for the production database. Local development uses the same Cloud SQL instance via the Cloud SQL Auth Proxy.

**Why:**
- School GCP credits available — no cost concern
- Keeps everything in one GCP project (App Engine + Cloud SQL)
- Cleaner architecture than pointing at an external school MySQL server

**Future consideration:** Move local development to local MySQL installs to isolate dev from production data. Migration files in `/migrations` will support this transition. See `DATABASE_PLAN.md`.

---

### 008 — Secret Manager for credentials

**Date:** April 13, 2026
**Decision:** Store the database password in GCP Secret Manager. Flask reads it at runtime on App Engine. Local development uses a `.env` file.

**Why:**
- Password never lives in code or config files
- `.env` files are ignored by git and never committed
- Secret Manager is the GCP-native solution — integrates cleanly with App Engine

**Alternatives considered:**
- Hardcoding in app.yaml — rejected, app.yaml is committed to the repo
- Environment variables set at deploy time — rejected, requires remembering to include them on every deploy

---

### 009 — GitHub Actions CI/CD

**Date:** April 13, 2026
**Decision:** Use GitHub Actions for CI/CD. flake8 linting runs on every PR. Automatic deployment to App Engine on every merge to main.

**Why:**
- Enforces PEP 8 consistently across all team members
- Removes manual deploy step — merging a PR is enough
- Catches style violations before they get into main
- Industry standard practice worth learning

**Implementation:** `.github/workflows/lint.yml` and `.github/workflows/deploy.yml`

---

### 010 — Migration files for schema management

**Date:** April 13, 2026
**Decision:** Use numbered SQL migration files in `/migrations` instead of a single DROP + recreate DDL file.

**Why:**
- Allows schema to evolve without losing production data
- Schema changes are version controlled alongside code
- `001_initial_schema.sql` can still use DROP IF EXISTS during early development
- Once real user data exists, only additive migrations (ALTER TABLE, CREATE TABLE)

**Alternatives considered:**
- Single DDL file with DROP IF EXISTS — fine for class projects, not suitable for a live app with real data
- Alembic / Flyway — overkill for a three person team, manual migration files are sufficient

**See also:** `DATABASE_PLAN.md`

---

### 011 — Rating columns on reviews table

**Date:** April 23, 2026
**Decision:** Rating criteria are columns directly on the reviews table: `complexity`, `workload`, `team_dynamics`, `would_recommend` (all 1-5 integers). No separate criteria or review_ratings tables.

**Why:**
- Criteria are fixed for the project scope — no need for dynamic extensibility
- Simpler queries — `SELECT complexity, workload FROM reviews` just works with no JOINs
- Maps directly to what Ben built in the templates
- Easier to explain and demo in Progress Reports

**Alternatives considered:**
- Separate `criteria` and `review_ratings` tables (Henry's original approach) — rejected for this project's scope. Technically superior for extensibility but adds unnecessary complexity for a fixed set of 4 criteria.

**Note:** Column was originally named `difficulty`. Renamed to `complexity` in migration 008 (May 2026) — "complexity" more accurately describes what the rating measures.

---

---

### 012 — Term entry standardized to dropdown

**Date:** May 2026
**Decision:** Replace the free-text term input on the review submission form with a generated dropdown (`generate_terms()`) covering the past 5 years by quarter.

**Why:**
- Free-text allowed arbitrary values (e.g. "asdf") that pollute filters and display
- A generated list of valid academic quarters covers all realistic use cases
- Consistent values enable reliable filtering by term on the project detail page

**Note:** Term filter dropdowns (e.g. on the project detail page) query `DISTINCT term` from actual reviews — they only show terms that have reviews, not the full generated list.

---

### 013 — Browse page filter panel

**Date:** May 2026
**Decision:** Replace the inline filter bar with a collapsible filter panel. Sort moved into the panel. Min/max range selects for all four rating criteria. Active filter count badge on the toggle button.

**Why:**
- Inline filter bar was cluttered and the sort dropdown felt redundant next to search
- Collapsible panel keeps the browse page clean by default and reveals options on demand
- Min/max ranges are more useful than single-value filters for ratings
- Sort logically belongs with filters rather than the search bar

---

### 014 — Review editing (owner only)

**Date:** May 2026
**Decision:** Reviewers can edit their own reviews via `/review/<id>/edit`. Ownership is enforced server-side (403 if student_id doesn't match session). Edit button is only rendered for the review's author.

**Why:**
- Reviewers may want to correct mistakes or update their experience
- Server-side ownership check prevents spoofed requests
- Client-side hiding of the button is UX only, not a security measure

---

### 015 — AI use field on reviews (optional)

**Date:** May 2026
**Decision:** Add an optional `ai_use` field to reviews. Fixed dropdown options: Not used / Research / learning / Code generation / Debugging / troubleshooting / Multiple / other.

**Why:**
- Relevant context for readers — knowing how a team used AI affects how they interpret the review
- Optional keeps the form lightweight; not all reviewers have relevant AI use to report
- Fixed options prevent free-text noise; covers the realistic range of use cases

---

### 016 — Review pagination and term filtering on project detail

**Date:** May 2026
**Decision:** Reviews on project detail pages are paginated (5 per page) and filterable by term. Always sorted by helpfulness score (helpful votes minus not-helpful votes), most recent as tiebreaker. No user-selectable sort on the detail page.

**Why:**
- Projects with many reviews need pagination to remain readable
- Term filtering lets readers find reviews from a specific quarter
- Fixing sort to helpfulness removes the risk of conflicts between sort and term filter state
- A second sort axis (e.g. most recent) was removed to keep state management simple

---

## Open Decisions

| # | Question | Status |
|---|----------|--------|
| 017 | Local MySQL for dev vs shared Cloud SQL? | Deferred — team comfortable with proxy approach |
| 018 | Rename `difficulty` → `complexity` across DB and codebase? | ✅ Done — migration 008, all templates and routes updated (May 2026) |