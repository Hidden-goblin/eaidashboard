# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging


def log_error(message):
    log = logging.getLogger("uvicorn.error")
    log.error(message)


def log_message(message):
    log = logging.getLogger("uvicorn.error")
    log.info(message)
