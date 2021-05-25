from typing import List

import attr
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient

from .document import Document
from ... import Helper, Conversation, Message
from ...abc import DataStore


class Mongo(DataStore):
    def __init__(self, connection_string):
        self.db = AsyncIOMotorClient(connection_string).stats

        self.conversations = Document(self.db, "conversations")
        self.helpers = Document(self.db, "helpers")

    async def create_indexes(self):
        """Creates indexes for faster lookup"""
        await self.conversations.create_index("identifier", pymongo.ASCENDING)
        await self.helpers.create_index("identifier", pymongo.ASCENDING)

    async def save_conversation(self, conversation: Conversation) -> None:
        as_dict = attr.asdict(conversation, recurse=True)
        as_dict.pop("identifier")

        filter_dict = {"identifier": conversation.identifier}
        await self.conversations.upsert(filter_dict, as_dict)

    async def fetch_conversation(self, identifier: int) -> Conversation:
        convo = await self.conversations.find({"identifier": identifier})
        messages = []
        for message in convo["messages"]:
            messages.append(Message(**message))

        convo["messages"] = messages

        convo.pop("_id")

        return Conversation(**convo)

    async def fetch_current_conversation_count(self) -> int:
        return await self.conversations.get_document_count()

    async def fetch_helpers(self) -> List[Helper]:
        raw_helpers = await self.helpers.get_all()
        helpers = []
        for helper in raw_helpers:
            helpers.append(
                Helper(
                    helper["identifier"],
                    helper["total_messages"],
                    helper["total_conversations"],
                    helper["messages_per_conversation"],
                )
            )

        return helpers

    async def fetch_helper(self, identifier: int) -> Helper:
        pass

    async def store_helper(self, helper: Helper) -> None:
        as_dict = attr.asdict(helper)
        as_dict.pop("identifier")

        filter_dict = {"identifier": helper.identifier}
        await self.helpers.upsert(filter_dict, as_dict)

    async def remove_helper(self, identifier: int) -> None:
        pass

    async def get_all_conversations(self) -> List[dict]:
        return await self.conversations.get_all()

    async def get_all_helpers(self) -> List[dict]:
        return await self.helpers.get_all()
