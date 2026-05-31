# Database Plan

**Project Experience Explorer — CS 467 Spring 2026**
Caleb Richter, Henry Thong, Benjamin Joseph

This is a living document. Update it as the schema evolves.

---

## Migration Strategy

### Background

In CS 340, the standard approach was a single DDL file with `DROP TABLE IF EXISTS` before every `CREATE TABLE`. This works perfectly for class projects where:
- The schema is designed once and never changes
- You don't care about preserving data
- Everyone starts fresh by just re-running the file

For a live application with real users, this approach breaks down. You can't drop a table to add a column without deleting all the data in it.

### Our Approach

We use **numbered migration files** in a `/migrations` folder. Each file represents one change to the schema, applied in order.

```
/migrations
    001_initial_schema.sql
    002_add_something.sql
    003_change_something_else.sql
```

**Rules:**
- Never edit an existing migration file after it has been run by the team
- New changes always get a new numbered file
- Everyone runs new migration files when they pull them from the repo
- The live Cloud SQL database gets the same migrations applied manually before deploying

### During Early Development

While the app has no real user data, schema changes can be made freely by updating `001_initial_schema.sql` and re-running it. Once real users start submitting reviews, switch to additive-only migrations:
- `ALTER TABLE` to add columns
- `CREATE TABLE` for new tables
- Never `DROP TABLE` on a table with real data

### When to Write a New Migration File

| Change | File needed? |
|--------|-------------|
| Add a new table | Yes — `CREATE TABLE` |
| Add a column to existing table | Yes — `ALTER TABLE ADD COLUMN` |
| Rename a column | Yes — `ALTER TABLE RENAME COLUMN` |
| Change a column type | Yes — `ALTER TABLE MODIFY COLUMN` |
| Add an index | Yes |
| Fix a typo in the schema | Yes — `ALTER TABLE` |
| Seed data | Optional — separate seed files |

---

## Schema

> **Status: Current as of May 2026**

### Design Decisions

- **Ratings as columns on reviews** (not a separate table) — simpler queries, criteria are fixed for the project scope. Criteria: difficulty, workload, team_dynamics, would_recommend.
- **ai_use on reviews** — optional VARCHAR(50) column. Populated from a fixed dropdown; not free-text.
- **students table stores onid_hash and pseudonym** — no raw ONID stored, no password stored. Pseudonym is generated on first login.
- **term on reviews** — stores when the experience happened (e.g. "Spring 2026"), not when the review was submitted. Selected from a generated dropdown (`generate_terms()`) — free-text entry is no longer allowed.

---

### Tables

**projects**
| Column | Type | Notes |
|--------|------|-------|
| project_id | int unsigned PK | auto_increment |
| url | varchar(255) | Capstone portal link, unique |
| title | varchar(255) | not null |
| description | varchar(8000) | |
| details | varchar(4000) | |
| image_url | varchar(500) | thumbnail from Capstone portal (migration 005) |
| last_scraped | timestamp | default current_timestamp |
| updated_at | timestamp | auto-updated on change (migration 002) |

---

**students**
| Column | Type | Notes |
|--------|------|-------|
| student_id | int unsigned PK | auto_increment |
| onid_hash | varchar(255) | not null, unique — hashed ONID, never raw |
| pseudonym | varchar(100) | not null, unique |
| created_at | timestamp | default current_timestamp |

---

**reviews**
| Column | Type | Notes |
|--------|------|-------|
| review_id | int unsigned PK | auto_increment |
| project_id | int unsigned FK | references projects |
| student_id | int unsigned FK | references students |
| term | varchar(50) | e.g. "Spring 2026" — when experience happened |
| review_text | varchar(4000) | qualitative feedback |
| ai_use | varchar(50) | nullable — how AI was used during the project (migration 006) |
| difficulty | int | 1-5 |
| workload | int | 1-5 |
| team_dynamics | int | 1-5 |
| would_recommend | int | 1-5 |
| created_at | timestamp | default current_timestamp |
| updated_at | timestamp | auto-updated on change (migration 004) |

---

**helpfulness**
| Column | Type | Notes |
|--------|------|-------|
| helpfulness_id | int unsigned PK | auto_increment |
| review_id | int unsigned FK | references reviews |
| student_id | int unsigned FK | references students |
| value | tinyint | 1 = helpful, -1 = not helpful |

Unique constraint on (student_id, review_id) — one vote per student per review.

---

**comments**
| Column | Type | Notes |
|--------|------|-------|
| comment_id | int unsigned PK | auto_increment |
| review_id | int unsigned FK | references reviews |
| student_id | int unsigned FK | references students |
| comment_text | varchar(2000) | not null |
| created_at | timestamp | default current_timestamp |

---

### Relationships

| Relationship | Type |
|-------------|------|
| projects → reviews | one to many |
| students → reviews | one to many |
| reviews → helpfulness | one to many |
| students → helpfulness | one to many |
| reviews → comments | one to many |
| students → comments | one to many |

---

### Open Questions

- [x] How do we handle pseudonyms before ONID auth is built? — Resolved: generated on first OAuth login
- [x] Should comments be flat only (replies to reviews) or nested (replies to comments)? — Resolved: flat only (replies to reviews)
- [ ] Do we need a way to flag reviews as inappropriate? — Deferred post-course

---

## Migration Files

| File | Description | Author | Date |
|------|-------------|--------|------|
| 001_initial_schema.sql | Initial schema — projects, students, reviews, helpfulness, comments | Henry Thong | April 2026 |
| 002_rename_last_scraped_add_updated_at.sql | Add updated_at to projects | Henry Thong | April 2026 |
| 003_deduplicate_projects_add_url_unique.sql | Add unique constraint on projects.url | Henry Thong | April 2026 |
| 004_reviews_comments_add_updated_at.sql | Add updated_at to reviews and comments | Henry Thong | April 2026 |
| 005_add_image_url_to_projects.sql | Add image_url column to projects | Caleb Richter | May 2026 |
| 006_add_ai_use_to_reviews.sql | Add ai_use column to reviews | Caleb Richter | May 2026 |

---

## How to Apply Migrations Locally

When a new migration file is added to `/migrations`, run it against your local database:

```bash
mysql -u root -p project_explorer < migrations/001_initial_schema.sql
```

Or open it in MySQL Workbench / Cloud SQL Studio and run it manually.

---

## How to Apply Migrations to Production (Cloud SQL)

1. Open Cloud SQL Studio in the GCP Console
2. Connect as flask_user
3. Paste and run the migration SQL
4. Confirm the change before deploying the new app version that depends on it