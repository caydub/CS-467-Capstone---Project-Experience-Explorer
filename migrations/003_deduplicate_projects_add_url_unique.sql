-- 003_deduplicate_projects_add_url_unique.sql
-- The scraper's ON DUPLICATE KEY UPDATE on url never fired because url had no
-- UNIQUE constraint. This left 28 stale description-less rows (IDs 2-29) alongside
-- 28 correct rows (IDs 30-57) inserted on the second scraper run.
-- Steps: re-point any reviews off the stale IDs, delete stale rows, add the constraint.

-- Re-point reviews from stale project rows to their canonical replacements.
UPDATE reviews r
JOIN projects old ON r.project_id = old.project_id
JOIN projects new ON old.title = new.title
    AND new.description IS NOT NULL
    AND old.description IS NULL
SET r.project_id = new.project_id;

-- Delete stale description-less duplicates (seed row 1 has no duplicate, keep it).
DELETE FROM projects
WHERE description IS NULL
  AND project_id != 1;

-- Prevent this from happening again.
ALTER TABLE projects
    ADD UNIQUE KEY uq_projects_url (url);
