# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

from logging import getLogger

import dpath
from behave import given, when

from helpers.mock_models import MockContext
from helpers.models.models import UserModel

log = getLogger(__name__)


@given('"{user}" is logged in')
def user_logged_in(context: MockContext, user: str):
    try:
        log.info(f"{user} log in")
        _user = UserModel(**context.retrieve_data(f"users/{user}"))
        context.pre_requisites["user"] = _user
        context.model.log_in(context.pre_requisites["user"])
    except Exception as exception:
        log.exception(exception)
        context.model.take_screenshot()
        raise


@when('"{user}" creates "{new_user}"')
def create_user(context: MockContext, user: str, new_user: str):
    try:
        _user = dpath.get(context.pre_requisites, "user", default=None)
        if _user is None:
            raise Exception(f"Actor {user} has not been set")
        _new_user = UserModel(**context.retrieve_data(f"users/{new_user}"))
        context.model.create_user(_new_user)
        log.info("Record for removal")
    except Exception as exception:
        log.exception(exception)
        context.model.take_screenshot()
        raise


@when('"{user}" adds "{user_to_add}" to "{project_name}" as "{right}"')
def add_user_to_project(context, user: str, user_to_add: str, project_name: str, right: str):
    pass
