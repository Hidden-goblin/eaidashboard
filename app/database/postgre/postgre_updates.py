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
    }

]
