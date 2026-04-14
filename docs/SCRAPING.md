# Capstone Portal Scraping

**Project Experience Explorer — CS 467 Spring 2026**

> **Status: Placeholder — Henry investigating approach week of April 16**

---

## Overview

The project list is seeded from the OSU Capstone portal so reviewers can select their project from a dropdown rather than typing the name freeform. This prevents duplicate and misspelled project names in the database.

**Source:** https://eecs.engineering.oregonstate.edu/industry-relations/capstone-and-senior-design

---

## Approach

> **To be filled in by Henry after investigating on Wednesday April 16.**

Options being considered:
- Web scraping with BeautifulSoup / requests
- Manual export if the portal provides one
- Combination — scrape what's available, manually add anything missing

---

## Scraping Script

> **Document the script here once written.**

```bash
# placeholder — update when script exists
python migrations/seed_projects.py
```

---

## How to Re-run the Seeder

> **Fill in once the script exists.**

The project list should be re-seeded when:
- New projects are added to the Capstone portal mid-term
- The database is reset and needs to be repopulated
- A new term starts

---

## Script Location

> The seeding script will live in `/migrations` alongside the DDL files.

```
/migrations
    001_initial_schema.sql
    seed_projects.py        # or seed_projects.sql
```

---

## Handling New Projects Mid-Term

If a new project is added to the Capstone portal after the initial seed:

> Document the process here once decided. Options:
- Re-run the full scraper (safe if it checks for existing records before inserting)
- Manually insert the new project via Cloud SQL Studio
- Admin route in the app to add projects (future feature)

---

## Open Questions

- [ ] Does the Capstone portal have a structured/scrapable format or is it unstructured HTML?
- [ ] Are project names stable across terms or do they change?
- [ ] How often does the portal update — do we need to re-scrape periodically?
- [ ] Should the seeder be idempotent (safe to run multiple times without creating duplicates)?
- [ ] What metadata do we want to pull beyond project name? (sponsor, description, type, etc.)
