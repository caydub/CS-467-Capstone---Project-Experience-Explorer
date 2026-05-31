CREATE TABLE IF NOT EXISTS comment_helpfulness (
    comment_helpfulness_id  int unsigned auto_increment primary key,
    comment_id              int unsigned not null,
    student_id              int unsigned not null,
    value                   tinyint not null check (value in (1, -1)),

    foreign key (comment_id)
        references comments(comment_id)
        on delete cascade,

    foreign key (student_id)
        references students(student_id)
        on delete cascade,

    unique key unique_student_comment (student_id, comment_id)
);
