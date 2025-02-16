# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import dpath


class Context:
    """Simple context manager for tests"""

    __context: dict = {}

    def __str__(self) -> str:
        return f"{self.__context}"

    def set_context(
        self: "Context",
        path: str,
        content: int | str | bool | dict | list,
    ) -> None:
        """

        Args:
            path: the target path to set the content
            content: any data to store

        Returns: None
        """
        res = dpath.set(self.__context, path, content)
        if res == 0:
            dpath.new(self.__context, path, content)

    def get_context(self: "Context", path: str) -> int | str | bool | dict | list:
        """Retrieve a value from context"""
        return dpath.get(self.__context, path, default=None)
