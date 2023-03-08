# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
POSTGRE_UPDATES = [
    {"request": """create table if not exists campaigns (
    id serial primary key,
    project_id varchar (50) not null,
    version varchar (50) not null,
    occurrence serial,
    description text,
    status text,
    unique (project_id, version, occurrence)
    );""",
     "description": "Add campaigns table to schema"},
    {
        "request": """create table if not exists campaign_tickets_scenarios (
        id serial primary key,
        campaign_id int not null,
        scenario_id int not null,
        ticket_name text not null,
        foreign key (campaign_id) references campaigns (id),
        foreign key (scenario_id) references scenarios (id),
        unique (campaign_id, scenario_id, ticket_name));        
        """,
        "description": "Add campaign-tickets-scenarios relationship table schema"
    },
    {
        "request": """alter table campaign_tickets_scenarios
         rename column ticket_name 
         to ticket_reference;""",
        "description": "Rename column in campaign-tickets-scenarios from ticket_name"
                       " to ticket_reference"
    },
    {
        "request": """alter table campaign_tickets_scenarios
         add column status text;
        """,
        "description": "Add column 'status' to campaign_tickets_scenarios."
    },
    {
        "request": """drop table if exists campaign_tickets_scenarios;
        """,
        "description": "drop campaign_tickets_scenarios"
    },
    {
        "request": """create table if not exists campaign_tickets (
        id serial primary key,
        campaign_id int not null,
        ticket_reference text not null);""",
        "description": "Create table campaign_tickets"},
    {
        "request": """alter table campaign_tickets
        add constraint unique_campaign_ticket unique (campaign_id, ticket_reference),
        add constraint campaign_id_fkey foreign key (campaign_id) references campaigns(id) match full;
        """,
        "description": "Add constraints to campaign_tickets"
    },
    {
        "request": """create table if not exists campaign_ticket_scenarios (
        id serial primary key,
        campaign_id int not null,
        scenario_id int not null,
        status text);
        """,
        "description": "Create table campaign_ticket_scenarios"
    },
    {
        "request": """alter table campaign_ticket_scenarios 
        add constraint unique_campaign_ticket_scenario unique (campaign_id, scenario_id),
        add constraint campaign_ticket_id_fkey foreign key (campaign_id) references campaign_tickets(id) match full, 
        add constraint scenario_id_fkey foreign key (scenario_id) references scenarios(id) match full;""",
        "description": "Add constraints to campaign_ticket_scenarios"
    },
    {
        "request": """create table if not exists test_scenario_results (
        id serial primary key,
        run_date timestamp not null,
        project_id varchar (50) not null,
        version varchar (50) not null,
        campaign_id int not null,
        epic_id int not null,
        feature_id int not null,
        scenario_id int not null,
        status varchar (50) not null,
        is_partial boolean default false);
        """,
        "description": "Create table test_scenario_results"
    },
    {
        "request": """alter table test_scenario_results 
        add constraint campaign_id_fkey foreign key (campaign_id) references campaigns(id) match full,
        add constraint epic_id_fkey foreign key (epic_id) references epics(id) match full,
        add constraint feature_id_fkey foreign key (feature_id) references features(id) match full,
        add constraint scenario_id_fkey foreign key (scenario_id) references scenarios(id) match full;""",
        "description": "Add foreign key constraints on test_scenario_results table."
    },
{
        "request": """create table if not exists test_feature_results (
        id serial primary key,
        run_date timestamp not null,
        project_id varchar (50) not null,
        version varchar (50) not null,
        campaign_id int not null,
        epic_id int not null,
        feature_id int not null,
        status varchar (50) not null,
        is_partial boolean default false);
        """,
        "description": "Create table test_feature_results"
    },
    {
        "request": """alter table test_feature_results 
        add constraint campaign_id_fkey foreign key (campaign_id) references campaigns(id) match full,
        add constraint epic_id_fkey foreign key (epic_id) references epics(id) match full,
        add constraint feature_id_fkey foreign key (feature_id) references features(id) match full;""",
        "description": "Add foreign key constraints on test_feature_results table."
    },
{
        "request": """create table if not exists test_epic_results (
        id serial primary key,
        run_date timestamp not null,
        project_id varchar (50) not null,
        version varchar (50) not null,
        campaign_id int not null,
        epic_id int not null,
        status varchar (50) not null,
        is_partial boolean default false);
        """,
        "description": "Create table test_epic_results"
    },
    {
        "request": """alter table test_epic_results 
        add constraint campaign_id_fkey foreign key (campaign_id) references campaigns(id) match full,
        add constraint epic_id_fkey foreign key (epic_id) references epics(id) match full;""",
        "description": "Add foreign key constraints on test_epic_results table."
    },
    {
        "request": """create table if not exists projects (
        id serial primary key,
        name varchar (64) not null,
        alias varchar (64) not null);
        """,
        "description": "Create table projects"
    },
    {
        "request": """alter table projects
         add constraint unique_name unique (name); 
         """,
        "description": "Add uniqueness constraint on projects"
    },
    {
        "request": """create table if not exists versions (
        id serial primary key,
        project_id int not null,
        version varchar (50) not null,
        created timestamp not null default CURRENT_TIMESTAMP,
        updated timestamp not null default CURRENT_TIMESTAMP,
        started timestamp,
        end_forecast timestamp,
        status varchar(50) default 'recorded',
        open int default 0,
        cancelled int default 0,
        blocked int default 0,
        in_progress int default 0,
        done int default 0,
        open_blocking int default 0,
        open_major int default 0,
        open_minor int default 0,
        closed_blocking int default 0,
        closed_major int default 0,
        closed_minor int default 0);
        """,
        "description": "Create table versions"
    },
    {
        "request": """alter table versions 
        add constraint project_id_fkey foreign key (project_id) references projects(id) match full,
        add constraint unique_project_version unique (project_id, version);
        """,
        "description": "Add fk and unique constraint on versions"
    },
    {
        "request": """create table if not exists tickets ( 
        id serial primary key,
        reference varchar(50) not null,
        description varchar,
        status varchar(50) default 'open',
        created timestamp not null default CURRENT_TIMESTAMP,
        updated timestamp not null default CURRENT_TIMESTAMP,
        current_version int not null,
        past_versions varchar(50) [],
        delivery_date timestamp,
        project_id int not null);
        """,
        "description": "Create tickets table"
    },
    {
        "request": """alter table tickets 
        add constraint tickets_project_fkey foreign key (project_id) references projects(id) match full,
        add constraint tickets_current_version_fkey foreign key (current_version) references versions(id) match full,
        add constraint unique_ticket_project unique (project_id, reference);
        """,
        "description": "Add fk and unique constraints on tickets"
    },
    {
        "request": """create table if not exists users (
        id serial primary key,
        username varchar(50) not null,
        password varchar not null,
        scopes varchar(20) []);
        """,
        "description": "Create users table"
    },
    {
        "request": """alter table users
        add constraint unique_username_user unique (username);
        """,
        "description": "Add unique constraint on users"
    },
    {
        "request": """alter table campaign_tickets 
        add column ticket_id int,
        add constraint campaign_tickets_ticket_id_fk foreign key (ticket_id) references tickets(id)
         match simple on update no action
         on delete set null
         not valid;""",
        "description": "Add ticket_id column to campaign_tickets and add fk constraint"
    },
    {
        "request": """create table if not exists bugs (
        id serial primary key,
        title varchar not null,
        url varchar,
        description varchar,
        project_id int not null,
        version_id int not null,
        fix_version_id int,
        criticality varchar(20) not null,
        status varchar(20) not null,
        created timestamp default CURRENT_TIMESTAMP,
        updated timestamp default CURRENT_TIMESTAMP);""",
        "description": "Create bugs table"
    },
    {
        "request": """alter table bugs 
        add constraint bugs_project_id_fk foreign key (project_id) references projects(id) match full,
        add constraint bugs_version_id_fk foreign key (version_id) references versions(id) match full,
        add constraint unique_title_project_id unique (project_id, version_id, title);""",
        "description": "Add fk and unique constraint on bugs"
    },
    {
        "request": """alter table campaign_ticket_scenarios
        rename column campaign_id 
         to campaign_ticket_id;
        """,
        "description": "Rename campaign_id to campaign_ticket_id in campaign_ticket_scenarios"
    },
    {
        "request": """update versions
         set open_blocking = 0
         where open_blocking is NULL""",
        "description": "Fix null value in versions"
    },
{
        "request": """update versions
         set open_major = 0
         where open_major is NULL""",
        "description": "Fix null value in versions"
    },
{
        "request": """update versions
         set open_minor = 0
         where open_minor is NULL""",
        "description": "Fix null value in versions"
    },
{
        "request": """update versions
         set closed_blocking = 0
         where closed_blocking is NULL""",
        "description": "Fix null value in versions"
    },
{
        "request": """update versions
         set closed_major = 0
         where closed_major is NULL""",
        "description": "Fix null value in versions"
    },
{
        "request": """update versions
         set closed_minor = 0
         where closed_minor is NULL""",
        "description": "Fix null value in versions"
    }
]
