ALTER TABLE comments
    ADD COLUMN updated_at timestamp default current_timestamp on update current_timestamp AFTER created_at;

ALTER TABLE reviews
    ADD COLUMN updated_at timestamp default current_timestamp on update current_timestamp AFTER created_at;
