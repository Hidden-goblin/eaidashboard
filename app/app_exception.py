# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

class ProjectNotRegistered(Exception):
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
