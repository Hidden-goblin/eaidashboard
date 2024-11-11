# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from pydantic import BaseModel


class HealthCheck(BaseModel):
    app_status: str
    container_status: str
    cpu: float
    memory: float
    os: str
    pg_in_recovery: bool
    pg_connections: int
    redis_ping: bool
