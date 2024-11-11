# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import os
import platform

import psutil
from fastapi import APIRouter

from app.database.postgre.pg_monitoring import pg_health
from app.database.redis.rs_monitoring import rs_health
from app.schema.monitoring_schema import HealthCheck

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """
    Returns: HealthCheck object
    """
    app_status = "running"
    container_status = "healthy" if os.path.exists("/.dockerenv") else "outside_container"
    _pg_health = pg_health()
    return HealthCheck(
        app_status=app_status,
        container_status=container_status,
        cpu=psutil.cpu_percent(5),
        os=f"{os.name}-{platform.machine()}-{platform.system()}-{platform.version()}",
        memory=psutil.virtual_memory()[2],
        pg_in_recovery=_pg_health["in_recovery"],
        pg_connections=int(_pg_health["connections"]),
        redis_ping=rs_health(),
    )
