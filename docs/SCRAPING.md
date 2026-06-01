# Capstone Portal Scraping

**OSU Capstone Explorer — CS 467 Spring 2026**

> **Status: Complete — initial seed done April 23, 2026**

---

## Overview

The project list is seeded from the OSU Capstone portal so reviewers can select their project from a dropdown rather than typing the name freeform. This prevents duplicate and misspelled project names in the database.

**Source:** https://eecs.engineering.oregonstate.edu/capstone/submission/pages/browseProjects.php

---

## Approach

Web scraping with BeautifulSoup and requests. The scraper filters the Capstone portal browse page for CS467 projects specifically, then visits each project's individual detail page to extract the title and URL.

**Script location:** `migrations/project_scraper.py`

**Built by:** Henry Thong (scraping logic), Caleb Richter (DB insert logic)

**Initial seed:** 28 CS467 projects loaded on April 23, 2026.

---

## How to Re-run the Seeder

Make sure the Cloud SQL Auth Proxy is running first, then:

```bash
python migrations/project_scraper.py
```

The script uses `ON DUPLICATE KEY UPDATE` so it's safe to run multiple times — existing projects won't be duplicated.

Re-run when:
- New projects are added to the Capstone portal mid-term
- The database is reset and needs to be repopulated
- A new term starts

---

## Script Location

```
/migrations
    001_initial_schema.sql
    project_scraper.py
```

---

## Handling New Projects Mid-Term

If a new project is added to the Capstone portal after the initial seed, re-run the full scraper — it's idempotent and won't create duplicates. Alternatively, insert manually via Cloud SQL Studio:

```sql
INSERT INTO projects (title, url) VALUES ('Project Name', 'https://portal-url');
```

---

## What the Scraper Pulls

For each project the scraper extracts and stores:

| Field | Notes |
|-------|-------|
| `title` | Project name |
| `url` | Link to the Capstone portal detail page |
| `description` | Full project description (stored as HTML, rendered with BeautifulSoup) |
| `details` | Team/tech metadata block |
| `image_url` | Thumbnail image from the portal (migration 005) |

The scraper uses `ON DUPLICATE KEY UPDATE` on `url` so re-running it only updates rows where content has actually changed.

---

## Resolved Questions

- **Additional metadata** — Yes, description, details, and image_url are all scraped and stored (migrations 002 and 005).
- **Re-scrape frequency** — Re-run at the start of each new term when the portal updates with new projects. The scraper is idempotent so there is no risk in running it multiple times.
- **Admin route for manual inserts** — Not implemented. Use Cloud SQL Studio to insert manually if needed, or just re-run the scraper.