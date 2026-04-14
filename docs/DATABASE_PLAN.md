# Database Plan

**Project Experience Explorer — CS 467 Spring 2026**
Caleb Richter, Henry Thong, Benjamin Joseph

This is a living document. Fill in the schema sections as the team finalizes decisions.

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

### During Early Development (now)

While the app has no real user data, `001_initial_schema.sql` can still use `DROP TABLE IF EXISTS` — this lets us iterate on the schema freely without worrying about data loss.

Once real users start submitting reviews, we switch to additive-only migrations:
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
| Seed data (test data) | Optional — separate seed files |

---

## Schema

> **Status: In progress — to be finalized by the team**
> Henry is working on the initial schema. Use this section to document decisions.

### Entities (draft — open for edits)

**Projects**
- project_id (PK)
- name
- description
- sponsor
- portal_url
- created_at

> Team discussion: what other metadata do we want from the Capstone portal?

---

**Users** (pseudonym mapping)
- user_id (PK)
- onid_hash (hashed ONID — never store raw ONID)
- pseudonym
- created_at

> Team discussion: how do we handle pseudonyms in the MVP without ONID auth? Generate on first review submission?

---

**Reviews**
- review_id (PK)
- project_id (FK → Projects)
- user_id (FK → Users)
- term (e.g. "Spring 2026" — when the experience happened, not when submitted)
- body (written qualitative feedback)
- created_at

---

**Ratings**
- rating_id (PK)
- review_id (FK → Reviews)
- criteria (e.g. "complexity", "time_commitment", "team_dynamics")
- score (1-5)

> Team discussion: separate ratings table (flexible, easy to add criteria) vs rating columns directly on reviews (simpler queries)? TBD.

---

**Helpfulness**
- helpfulness_id (PK)
- review_id (FK → Reviews)
- user_id (FK → Users)
- value (1 = helpful, -1 = not helpful)

---

**Comments**
- comment_id (PK)
- review_id (FK → Reviews)
- user_id (FK → Users)
- body
- created_at

---

### Relationships

> Fill this in once entities are finalized.

| Relationship | Type |
|-------------|------|
| Projects → Reviews | one to many |
| Users → Reviews | one to many |
| Reviews → Ratings | one to many |
| Reviews → Comments | one to many |
| Reviews → Helpfulness | one to many |
| Users → Helpfulness | one to many |
| Users → Comments | one to many |

---

### Open Questions for Team Discussion

- [ ] What metadata do we want on projects beyond name, description, and portal link?
- [ ] How many rating criteria and what are they? (complexity, time commitment, team dynamics, ...)
- [ ] Ratings as rows in a separate table vs columns on the reviews table?
- [ ] How do we handle pseudonyms in the MVP before ONID auth is built?
- [ ] Do we need a way to flag reviews as inappropriate?
- [ ] Should comments be nested (replies to comments) or flat (replies to reviews only)?

---

## Migration Files

> Add entries here as migration files are created.

| File | Description | Author | Date |
|------|-------------|--------|------|
| 001_initial_schema.sql | Initial schema — all tables | TBD | TBD |

---

## How to Apply Migrations Locally

When a new migration file is added to `/migrations`, run it against your local database:

```bash
mysql -u root -p your_local_database < migrations/002_example.sql
```

Or open it in MySQL Workbench / Cloud SQL Studio and run it manually.

---

## How to Apply Migrations to Production (Cloud SQL)

1. Open Cloud SQL Studio in the GCP Console
2. Connect as flask_user
3. Paste and run the migration SQL
4. Confirm the change before deploying the new app version that depends on it
