from typing import Any

import behave.model


def string_to_bool(element: Any):
    if isinstance(element, int):
        return bool(element)
    if isinstance(element, str):
        in_true = element.casefold() in ("true", "yes")
        return True if in_true else False


def status_to_string(status: behave.model.Status) -> str:
    # print(status)
    # _status = {behave.model.Status.untested: "untested",
    #            behave.model.Status.skipped: "skipped",
    #            behave.model.Status.passed: "passed",
    #            behave.model.Status.failed: "failed",
    #            behave.model.Status.undefined: "undefined",
    #            behave.model.Status.executing: "executing"}
    # return _status[status]
    return str(status.name)
