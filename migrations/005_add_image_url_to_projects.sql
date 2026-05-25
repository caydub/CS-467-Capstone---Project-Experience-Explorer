-- Add image_url column to projects table for storing scraped thumbnail URLs
ALTER TABLE projects ADD COLUMN image_url VARCHAR(500);
