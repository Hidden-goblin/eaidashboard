# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Any

from behave.runner import Context
from pydantic import BaseModel

from helpers.models.dashboard import Dashboard


class MockContext(Context):
    model: Dashboard
    environment: dict
    pre_requisites: dict
    post_conditions: dict


