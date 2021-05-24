from typing import List

import attr


@attr.s(slots=True)
class Message:
    author_id: int = attr.ib()
    channel_id: int = attr.ib()
    content: str = attr.ib()
    guild_id: int = attr.ib()
    message_id: int = attr.ib()

    is_helper: bool = attr.ib(default=False, kw_only=True)


@attr.s(slots=True)
class Conversation:
    # Things to set
    first_message_id: int = attr.ib()

    # Things to set later
    total_messages: int = attr.ib(default=0)
    last_message_id: int = attr.ib(default=None)
    messages: List[Message] = attr.ib(default=list)

    # Things we want at init, but are iffy
    identifier: int = attr.ib(kw_only=True)
    guild_id: int = attr.ib(kw_only=True)
    channel_id: int = attr.ib(kw_only=True)

    # Fully optional items
    topic: str = attr.ib(default=None, kw_only=True)


@attr.s(slots=True)
class Helper:
    identifier: int = attr.ib()
    total_messages: int = attr.ib(default=0)
    total_conversations: int = attr.ib(default=0)
    messages_per_conversation: List[int] = attr.ib(default=list)
