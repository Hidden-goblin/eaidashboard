# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import re

PROJECT_ALIAS = {}


def _compute_alias(project_name: str) -> str:
    _alias = re.sub(r"[/\\\. \"\$\*\<\>\:\|\?]",
                    "",
                    project_name.casefold())
    if len(_alias) > 63:
        _alias = _alias[:62]
    return _alias


def register(project_name: str, alias: str = None)->None:
    forbidden_char = ['/', '\\', '.', ' ', '"', '$', '*', '<', '>', ':', '|', '?']
    has_forbidden_char = any(char in project_name for char in forbidden_char)

    if has_forbidden_char and alias is None:
        _alias = _compute_alias(project_name)
        PROJECT_ALIAS[project_name.casefold()] = _alias
        PROJECT_ALIAS[_alias] = _alias

    elif has_forbidden_char and alias:
        PROJECT_ALIAS[project_name.casefold()] = alias.casefold()
        PROJECT_ALIAS[alias.casefold()] = alias.casefold()
    else:
        PROJECT_ALIAS[project_name.casefold()] = project_name.casefold()


def provide(project_name: str) -> str | None:
    return PROJECT_ALIAS.get(project_name.casefold())


def contains(project_name: str) -> bool:
    return (project_name.casefold() in list(PROJECT_ALIAS.keys())
            or _compute_alias(project_name) in list(PROJECT_ALIAS.keys()))
