# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from logging import getLogger

import dpath
from behave import given, then, when

from helpers.mock_models import MockContext
from helpers.models.api_dashboard import ApiDashboard

log = getLogger(__name__)


@given("the following projects exist")
def project_exits(context: MockContext) -> None:
    try:
        _api_dashboard = ApiDashboard(**context.model.composer())
        _api_dashboard.user = dpath.get(context.pre_requisites, "user")
        project_list = _api_dashboard.list_of_projects()
        expected_projects = [item["project_name"] for item in context.table.rows]
        for expected in expected_projects:
            if expected not in project_list:
                print(f"Create {expected}")
                _api_dashboard.create_project(expected)
        project_list = _api_dashboard.list_of_projects()
        context.model.push_event(f"Existing projects: {','.join(project_list)}")
    except Exception as exception:
        log.exception(exception)
        context.model.take_screenshot()
        raise


@when('"{user}" lists projects')
def list_project(context: MockContext, user: str) -> None:
    pass


@when('"{user}" registers "{project_name}"')
def register_project(context: MockContext, user: str, project_name: str) -> None:
    pass


@then('"{user}" retrieves the projects')
def retrieve_projects(context: MockContext, user: str) -> None:
    pass


@then('"{user}" "{action_status}"')
def check_action(context: MockContext, user: str, action_status: str) -> None:
    pass
