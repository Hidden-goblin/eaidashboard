# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-

class ProjectNotRegistered(Exception):
    pass


class VersionNotFound(Exception):
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


class CampaignNotFound(Exception):
    pass

class TicketNotFound(Exception):
    pass

class NonUniqueError(Exception):
    pass


class NotConnected(Exception):
    pass


class NotAuthorized(Exception):
    pass


class IncorrectFieldsRequest(Exception):
    pass
