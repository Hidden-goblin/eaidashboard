# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.schema.base_schema import ExtendedBaseModel
from app.schema.project_schema import DashboardProject


class Dashboard(ExtendedBaseModel):
    projects: list[DashboardProject]
