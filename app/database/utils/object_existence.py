# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.app_exception import ProjectNotRegistered, VersionNotFound
from app.database.postgre.pg_versions import version_exists
from app.utils.project_alias import provide


async def project_version_exists(project_name: str, version: str = None):
    if provide(project_name) is None:
        raise ProjectNotRegistered(f"'{project_name}' is not registered")
    if version is not None and not await version_exists(project_name, version):
        raise VersionNotFound(f"Version '{version}' is not found")
