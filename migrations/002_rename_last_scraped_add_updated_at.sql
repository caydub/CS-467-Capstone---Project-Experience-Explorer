-- 002_rename_last_scraped_add_updated_at.sql
-- Renames last_scraped to scraped_at to match the scraper's insert logic.
-- Adds updated_at with ON UPDATE trigger so it reflects the last time a row changed.

ALTER TABLE projects
    CHANGE COLUMN last_scraped scraped_at timestamp null,
    ADD COLUMN updated_at timestamp default current_timestamp on update current_timestamp;
