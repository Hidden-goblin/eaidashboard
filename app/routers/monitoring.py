# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import os
import platform

import psutil
from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

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


cpu_gauge = Gauge("app_cpu_percent", "CPU usage in percent")
memory_gauge = Gauge("app_memory_percent", "Memory usage in percent")
pg_conn_gauge = Gauge("pg_connections", "Number of Postgres connections")
pg_recovery_gauge = Gauge("pg_in_recovery", "Is Postgres in recovery mode (0/1)")
redis_ping_gauge = Gauge("redis_ping", "Redis ping status (0=fail,1=ok)")


@router.get("/metrics")
def metrics():
    _pg_health = pg_health()
    # Update values
    cpu_gauge.set(psutil.cpu_percent(0.1))
    memory_gauge.set(psutil.virtual_memory().percent)
    # tes fonctions _pg_health et rs_health() mises à jour ici :
    pg_conn_gauge.set(int(_pg_health["connections"]))
    pg_recovery_gauge.set(1 if _pg_health["in_recovery"] else 0)
    redis_ping_gauge.set(1 if rs_health() else 0)

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
