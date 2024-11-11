# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from app.utils.log_management import log_error


class InsertionError(Exception):
    pass


class DuplicateProject(Exception):
    pass


class DuplicateVersion(Exception):
    pass


class ProjectNotRegistered(Exception):
    pass


class ProjectNameInvalid(Exception):
    pass


class VersionNotFound(Exception):
    pass


class OccurrenceNotFound(Exception):
    pass


class UnknownStatusException(Exception):
    pass


class StatusTransitionForbidden(Exception):
    pass


class UpdateException(Exception):
    pass


class DuplicateArchivedVersion(Exception):
    pass


class DuplicateInProgressVersion(Exception):
    pass


class DuplicateFutureVersion(Exception):
    pass


class IncorrectTicketCount(Exception):
    pass


class UserNotFoundException(Exception):
    pass


class CampaignNotFound(Exception):
    pass


class TicketNotFound(Exception):
    pass


class ScenarioNotFound(Exception):
    pass


class IncorrectFieldsRequest(Exception):
    """To be raised when field is missing in the request"""

    pass


class MalformedCsvFile(Exception):
    """To be raised when csv misses header or field header"""

    pass


class DuplicateTestResults(Exception):
    """To be raised when an existing test campaign result is already in database"""

    pass


class InvalidDeletion(Exception):
    """Deletion does not match the business rules"""

    pass


def front_error_message(  # noqa: ANN201
    templates: Jinja2Templates,
    request: Request,
    exception: Exception,
    retarget: str = "#messageBox",
):
    log_error(repr(exception))
    return templates.TemplateResponse(
        "error_message.html",
        {
            "request": request,
            "highlight": "The server could not compute data",
            "sequel": " to perform this action.",
            "advise": f"Try to reload the page. \n Error message is {','.join(exception.args)}",
        },
        headers={"HX-Retarget": retarget, "HX-Reswap": "innerHTML"},
    )


def front_access_denied(  # noqa: ANN201
    templates: Jinja2Templates,
    request: Request,
):
    return templates.TemplateResponse(
        "error_message.html",
        {
            "request": request,
            "highlight": "You are not authorized",
            "sequel": " to perform this action.",
            "advise": "Try to log again.",
        },
        headers={"HX-Retarget": "#messageBox"},
    )
