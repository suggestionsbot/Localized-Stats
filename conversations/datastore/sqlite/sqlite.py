import functools
import json
import os
from datetime import timedelta
from pathlib import Path
from typing import List

import aiosqlite as aiosqlite
from attr import asdict

from conversations import Helper, Conversation, Message
from conversations.abc import DataStore


def ensure_struct(func):
    @functools.wraps(func)
    async def wrapped(*args, **kwargs):
        await Sqlite._initialize(args[0].db)
        return await func(*args, **kwargs)

    return wrapped


class Sqlite(DataStore):
    _initialized = False

    def __init__(self):
        self.cwd = self._get_path()

        self.db = os.path.join(self.cwd, "datastore.db")

    @ensure_struct
    async def save_conversation(self, conversation: Conversation) -> None:
        with open("text.json", "w") as file:
            x = asdict(conversation)
            x["end_time"] = x["end_time"].strftime(
                        "%f:%S:%M:%H:%d:%m:%Y"
                    )
            x["start_time"] = x["start_time"].strftime(
                        "%f:%S:%M:%H:%d:%m:%Y"
                    )

            for m in x["messages"]:
                m["timestamp"] = m["timestamp"].strftime(
                        "%f:%S:%M:%H:%d:%m:%Y"
                    )

            json.dump(x, file, indent=4)

        async with aiosqlite.connect(self.db) as db:
            await db.execute(
                "INSERT INTO Conversation "
                "   VALUES ("
                "   :identifier, "
                "   :first_message_id, "
                "   :last_message_id, "
                "   :user_being_helped,"
                "   datetime(:start_time),"
                "   datetime(:end_time),"
                "   :guild_id,"
                "   :channel_id,"
                "   :topic"
                ") ON CONFLICT DO NOTHING ",
                {
                    "identifier": conversation.identifier,
                    "first_message_id": conversation.first_message_id,
                    "last_message_id": conversation.last_message_id,
                    "user_being_helped": conversation.user_being_helped,
                    "start_time": conversation.start_time,
                    "end_time": conversation.end_time,
                    "guild_id": conversation.guild_id,
                    "channel_id": conversation.channel_id,
                    "topic": conversation.topic,
                },
            )
            await db.commit()
            await self._store_all_messages(
                conversation.messages, conversation.identifier
            )

    @ensure_struct
    async def fetch_conversation(self, identifier: int) -> Conversation:
        async with aiosqlite.connect(self.db) as db:
            async with db.execute(
                "SELECT "
                "   first_message_id, last_message_id, "
                "   user_being_helped, datetime(start_time), "
                "   datetime(end_time), guild_id, channel_id, topic "
                "FROM Conversation "
                "WHERE"
                "   identifier=:identifier",
                {"identifier": identifier},
            ) as cursor:
                value = await cursor.fetchone()
                if not value:
                    raise ValueError("Couldnt find em aye")

                messages = await self._get_all_messages(identifier=identifier)

                return Conversation(
                    identifier=identifier,
                    first_message_id=value[0],
                    last_message_id=value[1],
                    user_being_helped=value[2],
                    start_time=value[3],
                    end_time=value[4],
                    guild_id=value[5],
                    channel_id=value[6],
                    topic=value[7],
                    messages=messages,
                )

    @ensure_struct
    async def fetch_current_conversation_count(self) -> int:
        async with aiosqlite.connect(self.db) as db:
            async with db.execute(
                "SELECT COUNT(identifier) FROM Conversation"
            ) as cursor:
                val = await cursor.fetchone()
                return val[0]

    @ensure_struct
    async def fetch_helpers(self) -> List[Helper]:
        async with aiosqlite.connect(self.db) as db:
            async with db.execute(
                "SELECT "
                "   H.identifier, H.total_messages, "
                "   H.total_conversations "  # , Hmp.amount, Hcl.time "
                "FROM Helper H "
                "LEFT JOIN Helper_messages_per Hmp"
                "   ON Hmp.helper_id = H.identifier "
                "LEFT JOIN Helper_convo_length Hcl "
                "   ON H.identifier = Hcl.helper_id"
            ) as cursor:
                # INNER JOIN will ignore helpers without values in both tables
                helpers = []
                helpers_raw = await cursor.fetchall()
                for val in helpers_raw:
                    if len(val) == 3:
                        val = (val[0], val[1], val[2], 0, 0)
                    elif len(val) == 4:
                        val = (val[0], val[1], val[2], val[3], 0)
                    per_convo_messages = [] # [item[3] for item in val]
                    convos = [] #[timedelta(seconds=s[4]) for s in val]

                    helpers.append(
                        Helper(
                            identifier=val[0],
                            total_messages=val[1],
                            total_conversations=val[2],
                            messages_per_conversation=per_convo_messages,
                            conversation_length=convos,
                        )
                    )

        return helpers

    @ensure_struct
    async def fetch_helper(self, identifier: int) -> Helper:
        async with aiosqlite.connect(self.db) as db:
            async with db.execute(
                "SELECT "
                "   H.identifier, H.total_messages, "
                "   H.total_conversations, Hmp.amount, Hcl.time "
                "FROM Helper H "
                "LEFT JOIN Helper_messages_per Hmp"
                "   ON Hmp.helper_id = H.identifier "
                "LEFT JOIN Helper_convo_length Hcl "
                "   ON H.identifier = Hcl.helper_id "
                "WHERE "
                "   H.identifier=:identifier ",
                {"identifier": identifier}
                # TODO Add args here
            ) as cursor:
                val = await cursor.fetchone()
                x = await cursor.fetchall()

                per_convo_messages = [item[3] for item in x]
                convos = [timedelta(seconds=s[4]) for s in x]

                """
                try:
                    per_convo_messages = val[3]
                except IndexError:
                    per_convo_messages = []
                try:
                    print(val[4])
                    convos = [timedelta(seconds=s) for s in val[4]]
                except IndexError:
                    convos = []
                """

                return Helper(
                    identifier=val[0],
                    total_messages=val[1],
                    total_conversations=val[2],
                    messages_per_conversation=per_convo_messages,
                    conversation_length=convos,
                )

    @ensure_struct
    async def store_helper(self, helper: Helper) -> None:
        async with aiosqlite.connect(self.db) as db:
            # Insert each conversation counter, ignoring existing rows
            for item in helper.messages_per_conversation:
                await db.execute(
                    "INSERT INTO Helper_messages_per VALUES (:helper_id, :amount) ON CONFLICT DO NOTHING ",
                    {"helper_id": helper.identifier, "amount": item},
                )

            # Insert each conversation length, ignoring existing rows
            for item in helper.conversation_length:
                await db.execute(
                    "INSERT INTO Helper_convo_length VALUES (:helper_id, :time) ON CONFLICT DO NOTHING ",
                    {"helper_id": helper.identifier, "time": item.total_seconds()},
                )

            await db.execute(
                "INSERT INTO Helper VALUES (:identifier, :total_messages, :total_conversations) "
                "ON CONFLICT (identifier) DO UPDATE SET "
                "   total_messages=:total_messages, total_conversations=:total_conversations",
                {
                    "identifier": helper.identifier,
                    "total_messages": helper.total_messages,
                    "total_conversations": helper.total_conversations,
                },
            )
            await db.commit()

    @ensure_struct
    async def remove_helper(self, identifier: int) -> None:
        async with aiosqlite.connect(self.db) as db:
            args = {"identifier": identifier}
            await db.execute("DELETE FROM Helper WHERE identifier=:identifier", args)
            await db.execute(
                "DELETE FROM Helper_messages_per WHERE helper_id=:identifier", args
            )
            await db.execute(
                "DELETE FROM Helper_convo_length WHERE helper_id=:identifier", args
            )
            await db.commit()

    @ensure_struct
    async def fetch_all_conversations(self) -> List[Conversation]:
        async with aiosqlite.connect(self.db) as db:
            async with db.execute(
                "SELECT "
                "   first_message_id, last_message_id, "
                "   user_being_helped, datetime(start_time), "
                "   datetime(end_time), guild_id, channel_id, topic, identifier "
                "FROM Conversation"
            ) as cursor:
                conversations = []
                conversations_raw = await cursor.fetchall()
                for convo in conversations_raw:
                    messages = await self._get_all_messages(convo[8])
                    conversations.append(
                        Conversation(
                            identifier=convo[8],
                            first_message_id=convo[0],
                            last_message_id=convo[1],
                            user_being_helped=convo[2],
                            start_time=convo[3],
                            end_time=convo[4],
                            guild_id=convo[5],
                            channel_id=convo[6],
                            topic=convo[7],
                            messages=messages,
                        )
                    )

        return conversations

    @ensure_struct
    async def fetch_all_helpers(self) -> List[Helper]:
        async with aiosqlite.connect(self.db) as db:
            async with db.execute(
                "SELECT "
                "   H.identifier, H.total_messages, "
                "   H.total_conversations, Hmp.amount, Hcl.time "
                "FROM Helper H "
                "LEFT JOIN Helper_messages_per Hmp"
                "   ON Hmp.helper_id = H.identifier "
                "LEFT JOIN Helper_convo_length Hcl "
                "   ON H.identifier = Hcl.helper_id "
            ) as cursor:
                helpers = []
                helpers_raw = await cursor.fetchall()
                for val in helpers_raw:
                    per_convo_messages = [item[3] for item in val]
                    convos = [timedelta(seconds=s[4]) for s in val]
                    helpers.append(
                        Helper(
                            identifier=val[0],
                            total_messages=val[1],
                            total_conversations=val[2],
                            messages_per_conversation=per_convo_messages,
                            conversation_length=convos,
                        )
                    )
        return helpers

    @ensure_struct
    async def create_indexes(self) -> None:
        pass

    async def _store_all_messages(
        self, messages: List[Message], conversation_id: int
    ) -> None:
        async with aiosqlite.connect(self.db) as db:
            for msg in messages:
                is_helper = 1 if msg.is_helper else 0
                await db.execute(
                    "INSERT INTO Message VALUES ("
                    "   :message_id, :author_id, :channel_id, "
                    "   :guild_id, :is_helper, :content, "
                    "   datetime(:timestamp), :conversation_id"
                    ") ON CONFLICT DO NOTHING ",
                    {
                        "message_id": msg.message_id,
                        "author_id": msg.author_id,
                        "channel_id": msg.channel_id,
                        "guild_id": msg.guild_id,
                        "is_helper": is_helper,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                        "conversation_id": conversation_id,
                    },
                )
            await db.commit()

    async def _get_all_messages(self, identifier: int) -> List[Message]:
        async with aiosqlite.connect(self.db) as db:
            async with db.execute(
                "SELECT "
                "   author_id, channel_id, content,"
                "   guild_id, message_id, datetime(timestamp), is_helper "
                "FROM Message "
                "WHERE"
                "   conversation_id=:identifier",
                {"identifier": identifier},
            ) as messages_cursor:
                messages = []
                messages_raw = await messages_cursor.fetchall()
                for val in messages_raw:
                    messages.append(
                        Message(
                            author_id=val[0],
                            channel_id=val[1],
                            content=val[2],
                            guild_id=val[3],
                            message_id=val[4],
                            timestamp=val[5],
                            is_helper=True if val[6] else False,
                        )
                    )

        return messages

    @staticmethod
    async def _initialize(db):
        """A static method used to make sure the relevant tables exist"""
        if Sqlite._initialized:
            # We are initialized
            return

        async with aiosqlite.connect(db) as db:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='Message'"
            ) as cursor:
                if not await cursor.fetchone():
                    await db.execute(
                        "CREATE TABLE Message ("
                        "   message_id INTEGER NOT NULL PRIMARY KEY, "
                        "   author_id INTEGER NOT NULL,"
                        "   channel_id INTEGER NOT NULL,"
                        "   guild_id INTEGER NOT NULL,"
                        "   is_helper INTEGER NOT NULL,"
                        "   content TEXT NOT NULL,"
                        "   timestamp TEXT NOT NULL,"
                        "   conversation_id INTEGER,"
                        "   FOREIGN KEY (conversation_id) REFERENCES Conversation (identifier)"
                        ")"
                    )
                    await db.commit()

            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='Conversation'"
            ) as cursor:
                if not await cursor.fetchone():
                    await db.execute(
                        "CREATE TABLE Conversation ("
                        "    identifier INTEGER PRIMARY KEY,"
                        "    first_message_id INTEGER NOT NULL,"
                        "    last_message_id INTEGER NOT NULL,"
                        "    user_being_helped INTEGER NOT NULL,"
                        "    start_time TEXT NOT NULL,"
                        "    end_time TEXT NOT NULL,"
                        "    guild_id INTEGER NOT NULL,"
                        "    channel_id INTEGER NOT NULL,"
                        "    topic TEXT"
                        ")"
                    )
                    await db.commit()

            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='Helper'"
            ) as cursor:
                if not await cursor.fetchone():
                    await db.execute(
                        "CREATE TABLE Helper ("
                        "   identifier number NOT NULL PRIMARY KEY, "
                        "   total_messages number NOT NULL,"
                        "   total_conversations number NOT NULL"
                        ")"
                    )
                    await db.commit()

            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='Helper_messages_per'"
            ) as cursor:
                if not await cursor.fetchone():
                    await db.execute(
                        "CREATE TABLE Helper_messages_per ("
                        "   helper_id number NOT NULL, "
                        "   amount INTEGER NOT NULL,"
                        "   PRIMARY KEY (helper_id, amount),"
                        "   FOREIGN KEY (helper_id) REFERENCES Helper(identifier)"
                        ")"
                    )
                    await db.commit()

            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='Helper_convo_length'"
            ) as cursor:
                if not await cursor.fetchone():
                    await db.execute(
                        "CREATE TABLE Helper_convo_length ("
                        "   helper_id number NOT NULL, "
                        "   time INTEGER NOT NULL,"
                        "   PRIMARY KEY (helper_id, time),"
                        "   FOREIGN KEY (helper_id) REFERENCES Helper(identifier)"
                        ")"
                    )
                    await db.commit()

        Sqlite._initialized = True

    @staticmethod
    def _get_path() -> str:
        return str(Path(__file__).parents[0])
