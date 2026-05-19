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

### 006 — Pre-populated project list via combination of scraping and manual entry

**Date:** April 12, 2026
**Decision:** Seed the project list from the OSU Capstone portal using a combination of scraping and manual entry.

**Why:**
- Prevents duplicate/misspelled project names from reviewers typing freeform
- Scraping gets the bulk of the list automatically
- Manual entry covers anything the scraper misses or new projects added mid-term

**Status:** Scraping approach TBD — Henry investigating on Wednesday April 16.

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
**Decision:** Rating criteria are columns directly on the reviews table: `difficulty`, `workload`, `team_dynamics`, `would_recommend` (all 1-5 integers). No separate criteria or review_ratings tables.

**Why:**
- Criteria are fixed for the project scope — no need for dynamic extensibility
- Simpler queries — `SELECT difficulty, workload FROM reviews` just works with no JOINs
- Maps directly to what Ben built in the templates
- Easier to explain and demo in Progress Reports

**Alternatives considered:**
- Separate `criteria` and `review_ratings` tables (Henry's original approach) — rejected for this project's scope. Technically superior for extensibility but adds unnecessary complexity for a fixed set of 4 criteria.

---

## Open Decisions

| # | Question | Status |
|---|----------|--------|
| 012 | Local MySQL for dev vs shared Cloud SQL? | Flagged — revisit when schema is ready |
| 013 | Pseudonym generation — how exactly? Random words, adjective+noun, etc? | Resolved — adjective+noun+number (e.g. FrostRaven42) |
| 014 | Capstone portal scraping approach | Henry investigating Wednesday April 16 |