create schema if not exists project_explorer_db;
use project_explorer_db;

create table if not exists projects (
    project_id      int unsigned auto_increment primary key,
    url             varchar(255),
    title           varchar(255) not null,
    description     varchar(8000),
    details         varchar(4000),
    last_scraped    timestamp default current_timestamp
);

create table if not exists students (
    student_id      int unsigned auto_increment primary key,
    onid_hash       varchar(255) not null unique,
    pseudonym       varchar(100) not null unique,
    created_at      timestamp default current_timestamp
);

create table if not exists reviews (
    review_id           int unsigned auto_increment primary key,
    project_id          int unsigned not null,
    student_id          int unsigned not null,
    term                varchar(50) not null,
    review_text         varchar(4000),
    difficulty          int check (difficulty between 1 and 5),
    workload            int check (workload between 1 and 5),
    team_dynamics       int check (team_dynamics between 1 and 5),
    would_recommend     int check (would_recommend between 1 and 5),
    created_at          timestamp default current_timestamp,

    foreign key (project_id)
        references projects(project_id)
        on delete cascade,

    foreign key (student_id)
        references students(student_id)
        on delete cascade
);

create table if not exists helpfulness (
    helpfulness_id  int unsigned auto_increment primary key,
    review_id       int unsigned not null,
    student_id      int unsigned not null,
    value           tinyint not null check (value in (1, -1)),

    foreign key (review_id)
        references reviews(review_id)
        on delete cascade,

    foreign key (student_id)
        references students(student_id)
        on delete cascade,

    unique key unique_student_review (student_id, review_id)
);

create table if not exists comments (
    comment_id      int unsigned auto_increment primary key,
    review_id       int unsigned not null,
    student_id      int unsigned not null,
    comment_text    varchar(2000) not null,
    created_at      timestamp default current_timestamp,

    foreign key (review_id)
        references reviews(review_id)
        on delete cascade,

    foreign key (student_id)
        references students(student_id)
        on delete cascade
);

-- seed test project
insert into projects (title, url)
values ('Test Project', 'https://eecs.engineering.oregonstate.edu/capstone/submission/')
on duplicate key update title = title;