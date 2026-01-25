# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from logging import getLogger
from typing import Dict, Optional

from fastapi import Request
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2

logger = getLogger(__name__)


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self: "OAuth2PasswordBearerWithCookie",
        token_url: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ) -> None:
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": token_url, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        if request.headers.get("Authorization"):
            authorization: str = request.headers.get("Authorization")
        else:
            authorization: str = request.cookies.get("access_token")
        logger.debug(f"access_token is {authorization}")

        return authorization
