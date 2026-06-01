-- Drop the check constraint on difficulty, rename the column, recreate constraint on complexity.
-- The constraint name 'reviews_chk_1' was auto-generated for the difficulty check in the initial schema.
ALTER TABLE reviews DROP CHECK reviews_chk_1;
ALTER TABLE reviews RENAME COLUMN difficulty TO complexity;
ALTER TABLE reviews ADD CONSTRAINT reviews_chk_1 CHECK (complexity BETWEEN 1 AND 5);
