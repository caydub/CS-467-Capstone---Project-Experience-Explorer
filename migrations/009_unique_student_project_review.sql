-- Enforce one review per student per project.
ALTER TABLE reviews ADD UNIQUE KEY uq_student_project (student_id, project_id);
