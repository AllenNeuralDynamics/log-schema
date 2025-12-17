from typing import Protocol, runtime_checkable


@runtime_checkable
class LogStructure(Protocol):
    @staticmethod
    def patch(record): ...
