import datetime
from typing import List, Union

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
            try:
                timestamps = [
                    datetime.timedelta(seconds=seconds)
                    for seconds in helper["conversation_length"]
                ]
            except KeyError:
                timestamps = []
            helpers.append(
                Helper(
                    helper["identifier"],
                    helper["total_messages"],
                    helper["total_conversations"],
                    helper["messages_per_conversation"],
                    timestamps,
                )
            )

        return helpers

    async def fetch_helper(self, identifier: int) -> Union[Helper, None]:
        # try:
        helper = await self.helpers.find_by_custom({"identifier": identifier})
        helper.pop("_id")
        return Helper(**helper)
        # except:
        #   return None

    async def store_helper(self, helper: Helper) -> None:
        as_dict = attr.asdict(helper)
        as_dict.pop("identifier")
        as_dict["conversation_length"] = [
            item.total_seconds() for item in as_dict["conversation_length"]
        ]

        filter_dict = {"identifier": helper.identifier}
        await self.helpers.upsert(filter_dict, as_dict)

    async def remove_helper(self, identifier: int) -> None:
        pass

    async def fetch_all_conversations(self) -> List[Conversation]:
        values = await self.conversations.get_all()
        conversations = []
        for convo in values:
            messages = []
            for message in convo["messages"]:
                messages.append(Message(**message))

            convo["messages"] = messages
            convo.pop("_id")

            conversations.append(Conversation(**convo))

        return conversations

    async def fetch_all_helpers(self) -> List[Helper]:
        values = await self.helpers.get_all()
        helpers = []
        for helper in values:
            helper.pop("_id")
            helpers.append(Helper(**helper))

        return helpers
