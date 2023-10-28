# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from starlette.requests import Request


def header_request(request: Request, requested: str) -> bool:
    return request.headers.get("eaid-request", "").casefold() == requested.casefold()
