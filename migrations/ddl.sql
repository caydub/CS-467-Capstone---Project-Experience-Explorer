create schema if not exists project_explorer_db;
use project_explorer_db;

create table if not exists projects (
    project_id      int unsigned auto_increment primary key,
    url             varchar(255) unique,
    title           varchar(255),
    description     varchar(8000),
    details 		varchar(4000),
    created_at      timestamp default current_timestamp,
    updated_at      timestamp default current_timestamp,
    scraped_at      timestamp null
);

create table if not exists reviews (
    review_id       int unsigned auto_increment primary key,
    project_id      int unsigned not null,
    -- may change student_id into onid_hash
    student_id      int unsigned not null,
    body            varchar(4000),
    difficulty      int check (difficulty between 1 and 5),
    workload        int check (workload between 1 and 5),
    team_dynamics   int check (team_dynamics between 1 and 5),
    would_recommend int check (would_recommend between 1 and 5),
    created_at      timestamp default current_timestamp,
    updated_at      timestamp default current_timestamp on update current_timestamp,

    constraint fk_reviews_projects
        foreign key (project_id) references projects(project_id)
        on delete cascade

    constraint fk_reviews_students
        foreign key (student_id) references students(student_id)
        on delete cascade
);

create table if not exists comments (
    comment_id      int unsigned auto_increment primary key,
    review_id       int unsigned null,
    parent_id       int unsigned null,
    -- may change student_id into onid_hash
    student_id      int unsigned not null,
    body            varchar(4000),
    created_at      timestamp default current_timestamp,
    updated_at      timestamp default current_timestamp on update current_timestamp,

    constraint fk_comments_reviews
        foreign key (review_id) references reviews(review_id)
        on delete cascade,

    constraint fk_comments_parent
        foreign key (parent_id) references comments(comment_id)
        on delete cascade

    constraint fk_comments_students
        foreign key (student_id) references students(student_id)
        on delete cascade
);

create table if not exists students (
    student_id  int unsigned primary key,
    onid_hash   varchar(255) unique,
    pseudonym   varchar(255) unique,
    created_at  timestamp default current_timestamp
);
