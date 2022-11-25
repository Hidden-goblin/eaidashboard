# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import psycopg
from app.conf import postgre_string, postgre_setting_string, config
from app.database.postgre.postgre_updates import POSTGRE_UPDATES


def init_postgres():
    conn = psycopg.connect(postgre_setting_string, autocommit=True)
    cur = conn.cursor()
    cur.execute(f"select * from pg_database where datname = '{config['PG_DB']}'")
    if not cur.fetchall():
        cur.execute(f"create database {config['PG_DB']}")


def update_postgres():
    connexion = psycopg.connect(postgre_string)
    create_schema(connexion)
    cursor = connexion.cursor()
    cursor.execute("select op_order from operations "
                   "where type = 'database' "
                   "order by op_order desc "
                   "limit 1;")
    last_update = cursor.fetchone()[0]
    for index, update in enumerate(POSTGRE_UPDATES):
        if index + 1 > last_update:
            cursor.execute(update["request"])
            connexion.commit()
            cursor.execute("""insert into operations (type, op_user, op_order, content)
    values ('database', 'application', %s, %s)
     on conflict (type, op_order) do nothing; """, (index + 1, update["description"]))
            connexion.commit()


def create_schema(connexion):
    cursor = connexion.cursor()
    cursor.execute("""create table if not exists epics (
    id serial primary key,
    name varchar (50) not null,
    project_id varchar (50) not null,
    unique (name, project_id)
    );""")
    connexion.commit()
    cursor.execute("""create table if not exists features (
    id serial primary key,
    epic_id integer not null,
    name varchar not null,
    description text,
    filename text not null,
    tags text,
    project_id varchar (50) not null,
    foreign key (epic_id) references epics (id),
    unique (project_id, filename)
    );""")
    connexion.commit()
    cursor.execute("""create table if not exists scenarios (
    id serial primary key,
    scenario_id text not null,
    feature_id integer not null,
    name varchar not null,
    description text,
    steps text,
    tags text,
    isoutline boolean,
    project_id varchar (50) not null,
    foreign key (feature_id) references features (id),
    unique (scenario_id, feature_id, project_id)
    );""")
    connexion.commit()
    cursor.execute("""create table if not exists operations (
    id serial primary key,
    type varchar (20) not null,
    op_user varchar (100) not null,
    op_order integer not null,
    content varchar,
    unique (type, op_order)
    );
    """)
    connexion.commit()
    cursor.execute("""insert into operations (type, op_user, op_order, content)
    values ('database', 'application', 0, 'Init db schema')
     on conflict (type, op_order) do nothing; """)
    connexion.commit()
