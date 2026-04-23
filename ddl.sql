create schema if not exists project_explorer;

use project_explorer;
create table if not exists projects (
project_id 			int unsigned auto_increment primary key,
url 				varchar(255),
title 				varchar(255),
description 		varchar(8000),
details 			varchar(4000),
last_scraped 		timestamp default current_timestamp
);

create table if not exists reviews (
	review_id int unsigned primary key,
    project_id int unsigned not null,
    review_text varchar(4000),
    verified_student boolean default false,
    last_created timestamp default current_timestamp,
    
    foreign key (project_id)
		references projects(project_id)
		on delete cascade
);

create table if not exists criteria (
	criteria_id	int unsigned auto_increment primary key,
    name varchar(100) not null unique,
    description varchar (1000),
    is_active boolean default true
);

create table if not exists review_ratings (
	review_rating_id int unsigned primary key,
    review_id 		int unsigned not null,
    criteria_id 	int unsigned not null,
    rating_value int not null check (rating_value between 1 and 5),
    
    foreign key (review_id)
		references reviews(review_id)
        on delete cascade,
        
	foreign key (criteria_id)
		references criteria(criteria_id)
        on delete cascade,
        
	unique key unique_review_criteria (review_id, criteria_id)
);

create table if not exists students (
	student_id	int unsigned auto_increment primary key,
    school_email	varchar(255) not null unique,
    hashed_password varchar(255) not null,
    created_at		timestamp default current_timestamp
);

/*--------------------------------------------------*/
insert into projects (title)
value
('Test')
on duplicate key update title = title;

-- Examples of criterias students may use as part of their review
insert into criteria (name, description)
values
('Difficulty', 'How hard the project was'),
('Workload', 'Amount of time required'),
('Usefulness', 'How valueuble the project was')
on duplicate key update name = name;