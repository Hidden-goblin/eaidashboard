# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging


def log_error(message: str) -> None:
    log = logging.getLogger("uvicorn.error")
    log.error(message)


def log_message(message: str) -> None:
    log = logging.getLogger("uvicorn.error")
    log.info(message)
