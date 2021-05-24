from typing import Protocol, List

from conversations import Conversation


class DataStore(Protocol):
    __slots__ = ()

    async def save_conversation(self, conversation: Conversation) -> None:
        raise NotImplementedError

    async def fetch_conversation(self, identifier: int) -> Conversation:
        raise NotImplementedError

    async def fetch_helpers(self) -> List[int]:
        raise NotImplementedError

    async def fetch_helper(self, identifier: int) -> Helper:
        raise NotImplementedError

    async def add_helper(self, identifier: int) -> None:
        raise NotImplementedError

    async def remove_helper(self, identifier: int) -> None:
        raise NotImplementedError
