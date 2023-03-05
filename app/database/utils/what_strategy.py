# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import abc
from abc import ABC
from psycopg.rows import tuple_row
from app.utils.pgdb import pool

from app.database.postgre.pg_campaigns_management import retrieve_campaign_id


class WhatStrategy(ABC):
    @staticmethod
    @abc.abstractmethod
    async def gather(project_name: str,
                     version: str = None,
                     campaign_occurrence: str = None):
        pass


class EpicStaked(WhatStrategy):
    @staticmethod
    async def gather(project_name: str,
                     version: str = None,
                     campaign_occurrence: str = None):
        with pool.connection() as connection:
            connection.row_factory = tuple_row
            if version is None and campaign_occurrence is None:
                result = connection.execute("select run_date, "
                                            "count(epic_id) filter (where status = %s) as passed, "
                                            "count(epic_id) filter (where status = %s) as skipped, "
                                            "count(epic_id) filter (where status = %s) as failed "
                                            "from test_epic_results "
                                            "where project_id = %s "
                                            "and is_partial = false "
                                            "group by run_date "
                                            "order by run_date;", ("passed", "skipped", "failed",
                                                                   project_name))
            elif campaign_occurrence is None:
                result = connection.execute("select run_date, "
                                            "count(epic_id) filter (where status = %s) as passed, "
                                            "count(epic_id) filter (where status = %s) as skipped, "
                                            "count(epic_id) filter (where status = %s) as failed "
                                            "from test_epic_results "
                                            "where project_id = %s "
                                            "and version = %s "
                                            "and is_partial = false "
                                            "group by run_date "
                                            "order by run_date;",
                                            ("passed",
                                             "skipped",
                                             "failed", project_name, version))
            else:
                campaign_id = await retrieve_campaign_id(project_name, version, campaign_occurrence)
                campaign_id = campaign_id[0]
                result = connection.execute("select run_date, "
                                            "count(epic_id) filter (where status = %s) as passed, "
                                            "count(epic_id) filter (where status = %s) as skipped, "
                                            "count(epic_id) filter (where status = %s) as failed "
                                            "from test_epic_results "
                                            "where campaign_id = %s "
                                            "group by run_date "
                                            "order by run_date;",
                                            ("passed",
                                             "skipped",
                                             "failed", campaign_id))
        return list(result.fetchall())


class EpicMap(WhatStrategy):
    @staticmethod
    async def gather(project_name: str,
                     version: str = None,
                     campaign_occurrence: str = None):
        with pool.connection() as connection:
            connection.row_factory = tuple_row
            if version is None and campaign_occurrence is None:
                result = connection.execute("select ter.run_date, ter.epic_id, ter.status, ep.name "
                                            "from test_epic_results as ter "
                                            "join epics as ep on ep.id = ter.epic_id "
                                            "where ter.project_id = %s "
                                            "and ter.is_partial = false "
                                            "order by ter.run_date, ter.epic_id;", (project_name,))
            elif campaign_occurrence is None:
                result = connection.execute("select ter.run_date, ter.epic_id, ter.status, ep.name "
                                            "from test_epic_results as ter "
                                            "join epics as ep on ep.id = ter.epic_id "
                                            "where ter.project_id = %s "
                                            "and ter.is_partial = false "
                                            "and ter.version = %s "
                                            "order by ter.run_date, ter.epic_id;",
                                            (project_name, version))
            else:
                campaign_id = await retrieve_campaign_id(project_name, version, campaign_occurrence)
                campaign_id = campaign_id[0]
                result = connection.execute("select ter.run_date, ter.epic_id, ter.status, ep.name "
                                            "from test_epic_results as ter "
                                            "join epics as ep on ep.id = ter.epic_id "
                                            "where ter.campaign_id = %s "
                                            "order by ter.run_date, ter.epic_id;",
                                            (campaign_id,))
        return list(result.fetchall())


class FeatureStaked(WhatStrategy):
    @staticmethod
    async def gather(project_name: str,
                     version: str = None,
                     campaign_occurrence: str = None):
        with pool.connection() as connection:
            connection.row_factory = tuple_row
            if version is None and campaign_occurrence is None:
                result = connection.execute("select run_date, "
                                            "count(feature_id) filter (where status = %s) as "
                                            "passed, "
                                            "count(feature_id) filter (where status = %s) as "
                                            "skipped, "
                                            "count(feature_id) filter (where status = %s) as "
                                            "failed "
                                            "from test_feature_results "
                                            "where project_id = %s "
                                            "and is_partial = false "
                                            "group by run_date "
                                            "order by run_date;", ("passed", "skipped", "failed",
                                                                   project_name))
            elif campaign_occurrence is None:
                result = connection.execute("select run_date, "
                                            "count(feature_id) filter (where status = %s) as "
                                            "passed, "
                                            "count(feature_id) filter (where status = %s) as "
                                            "skipped, "
                                            "count(feature_id) filter (where status = %s) as "
                                            "failed "
                                            "from test_feature_results "
                                            "where project_id = %s "
                                            "and version = %s "
                                            "and is_partial = false "
                                            "group by run_date "
                                            "order by run_date;",
                                            ("passed",
                                             "skipped",
                                             "failed", project_name, version))
            else:
                campaign_id = await retrieve_campaign_id(project_name, version, campaign_occurrence)
                campaign_id = campaign_id[0]
                result = connection.execute("select run_date, "
                                            "count(feature_id) filter (where status = %s) as "
                                            "passed, "
                                            "count(feature_id) filter (where status = %s) as "
                                            "skipped, "
                                            "count(feature_id) filter (where status = %s) as "
                                            "failed "
                                            "from test_feature_results "
                                            "where campaign_id = %s "
                                            "group by run_date "
                                            "order by run_date;",
                                            ("passed",
                                             "skipped",
                                             "failed", campaign_id))
        return list(result.fetchall())


class FeatureMap(WhatStrategy):
    @staticmethod
    async def gather(project_name: str,
                     version: str = None,
                     campaign_occurrence: str = None):
        with pool.connection() as connection:
            connection.row_factory = tuple_row
            if version is None and campaign_occurrence is None:
                result = connection.execute(
                    "select ter.run_date, ter.feature_id, ter.status, ep.name "
                    "from test_feature_results as ter "
                    "join features as ep on ep.id = ter.feature_id "
                    "where ter.project_id = %s "
                    "and ter.is_partial = false "
                    "order by ter.run_date, ter.feature_id;", (project_name,))
            elif campaign_occurrence is None:
                result = connection.execute(
                    "select ter.run_date, ter.feature_id, ter.status, ep.name "
                    "from test_feature_results as ter "
                    "join features as ep on ep.id = ter.feature_id "
                    "where ter.project_id = %s "
                    "and ter.is_partial = false "
                    "and ter.version = %s "
                    "order by ter.run_date, ter.feature_id;",
                    (project_name, version))
            else:
                campaign_id = await retrieve_campaign_id(project_name, version, campaign_occurrence)
                campaign_id = campaign_id[0]
                result = connection.execute(
                    "select ter.run_date, ter.feature_id, ter.status, ep.name "
                    "from test_feature_results as ter "
                    "join features as ep on ep.id = ter.feature_id "
                    "where ter.campaign_id = %s "
                    "order by ter.run_date, ter.feature_id;",
                    (campaign_id,))
        return list(result.fetchall())


class ScenarioStaked(WhatStrategy):
    @staticmethod
    async def gather(project_name: str,
                     version: str = None,
                     campaign_occurrence: str = None):
        with pool.connection() as connection:
            connection.row_factory = tuple_row
            if version is None and campaign_occurrence is None:
                result = connection.execute("select run_date, "
                                            "count(scenario_id) filter (where status = %s) as "
                                            "passed, "
                                            "count(scenario_id) filter (where status = %s) as "
                                            "skipped, "
                                            "count(scenario_id) filter (where status = %s) as "
                                            "failed "
                                            "from test_scenario_results "
                                            "where project_id = %s "
                                            "and is_partial = false "
                                            "group by run_date "
                                            "order by run_date;", ("passed", "skipped", "failed",
                                                                   project_name))
            elif campaign_occurrence is None:
                result = connection.execute("select run_date, "
                                            "count(scenario_id) filter (where status = %s) as "
                                            "passed, "
                                            "count(scenario_id) filter (where status = %s) as "
                                            "skipped, "
                                            "count(scenario_id) filter (where status = %s) as "
                                            "failed "
                                            "from test_scenario_results "
                                            "where project_id = %s "
                                            "and version = %s "
                                            "and is_partial = false "
                                            "group by run_date "
                                            "order by run_date;",
                                            ("passed",
                                             "skipped",
                                             "failed", project_name, version))
            else:
                campaign_id = await retrieve_campaign_id(project_name, version, campaign_occurrence)
                campaign_id = campaign_id[0]
                result = connection.execute("select run_date, "
                                            "count(scenario_id) filter (where status = %s) as "
                                            "passed, "
                                            "count(scenario_id) filter (where status = %s) as "
                                            "skipped, "
                                            "count(scenario_id) filter (where status = %s) as "
                                            "failed "
                                            "from test_scenario_results "
                                            "where campaign_id = %s "
                                            "group by run_date "
                                            "order by run_date;",
                                            ("passed",
                                             "skipped",
                                             "failed", campaign_id))
        return list(result.fetchall())


class ScenarioMap(WhatStrategy):
    @staticmethod
    async def gather(project_name: str,
                     version: str = None,
                     campaign_occurrence: str = None):
        with pool.connection() as connection:
            connection.row_factory = tuple_row
            if version is None and campaign_occurrence is None:
                result = connection.execute(
                    "select ter.run_date, ter.scenario_id, ter.status, "
                    "concat (ft.name,'--', ep.scenario_id) "
                    "from test_scenario_results as ter "
                    "join scenarios as ep on ep.id = ter.scenario_id "
                    "join features as ft on ft.id =  ep.feature_id "
                    "where ter.project_id = %s "
                    "and ter.is_partial = false "
                    "order by ter.run_date, ter.scenario_id;", (project_name,))
            elif campaign_occurrence is None:
                result = connection.execute(
                    "select ter.run_date, ter.scenario_id, ter.status, "
                    "concat (ft.name,'--', ep.scenario_id) "
                    "from test_scenario_results as ter "
                    "join scenarios as ep on ep.id = ter.scenario_id "
                    "join features as ft on ft.id =  ep.feature_id "
                    "where ter.project_id = %s "
                    "and ter.is_partial = false "
                    "and ter.version = %s "
                    "order by ter.run_date, ter.scenario_id;",
                    (project_name, version))
            else:
                campaign_id = await retrieve_campaign_id(project_name, version, campaign_occurrence)
                campaign_id = campaign_id[0]
                result = connection.execute(
                    "select ter.run_date, ter.scenario_id, ter.status,"
                    " concat (ft.name,'--', ep.scenario_id)"
                    " from test_scenario_results as ter"
                    " join scenarios as ep on ep.id = ter.scenario_id"
                    " join features as ft on ft.id =  ep.feature_id"
                    " where ter.campaign_id = %s"
                    " and ter.is_partial = %s"
                    " order by ter.run_date, ter.scenario_id;",
                    (campaign_id,True))
        return list(result.fetchall())


REGISTERED_STRATEGY = {"epics": {
    "stacked": EpicStaked,
    "map": EpicMap},
"features": {
    "stacked": FeatureStaked,
    "map": FeatureMap},
"scenarios": {
    "stacked": ScenarioStaked,
    "map": ScenarioMap}
}
