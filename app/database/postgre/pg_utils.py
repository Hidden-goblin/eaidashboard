from typing import Any

from sqlalchemy.dialects import postgresql


def _compile(query: Any) -> tuple[str, dict]:  # noqa ANN401
    compiled = query.compile(dialect=postgresql.dialect(), compile_kwargs={"render_postcompile": True})
    return compiled.string, compiled.params
