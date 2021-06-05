from typing import List

from conversations import Helper, Conversation
from conversations.abc import DataStore


class SQLiteDatstore(DataStore):
    async def save_conversation(self, conversation: Conversation) -> None:
        pass

    async def fetch_conversation(self, identifier: int) -> Conversation:
        pass

    async def fetch_current_conversation_count(self) -> int:
        pass

    async def fetch_helpers(self) -> List[Helper]:
        pass

    async def fetch_helper(self, identifier: int) -> Helper:
        pass

    async def store_helper(self, helper: Helper) -> None:
        pass

    async def remove_helper(self, identifier: int) -> None:
        pass

    async def get_all_conversations(self) -> List[dict]:
        pass

    async def get_all_helpers(self) -> List[dict]:
        pass
