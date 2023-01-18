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
        campaign_ticket_id int not null,
        scenario_id int not null,
        status text);
        """,
        "description": "Create table campaign_ticket_scenarios"
    },
    {
        "request": """alter table campaign_ticket_scenarios 
        add constraint unique_campaign_ticket_scenario unique (campaign_ticket_id, scenario_id),
        add constraint campaign_ticket_id_fkey foreign key (campaign_ticket_id) references campaign_tickets(id) match full, 
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
    }


]
