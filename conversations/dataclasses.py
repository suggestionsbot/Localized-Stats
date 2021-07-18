import datetime
from enum import Enum
from typing import List

import attr


@attr.s(slots=True, frozen=True)
class Message:
    author_id: int = attr.ib()
    channel_id: int = attr.ib()
    content: str = attr.ib()
    guild_id: int = attr.ib()
    message_id: int = attr.ib()
    timestamp: datetime.datetime = attr.ib()

    is_helper: bool = attr.ib(default=False, kw_only=True)


@attr.s(slots=True)
class Conversation:
    # Things to set
    first_message_id: int = attr.ib()
    user_being_helped: int = attr.ib()
    start_time: datetime.datetime = attr.ib()

    # Things to set later
    last_message_id: int = attr.ib(default=None)
    end_time: datetime.datetime = attr.ib(default=None)
    messages: List[Message] = attr.ib(default=attr.Factory(list))

    # Things we want at init, but are iffy
    identifier: int = attr.ib(kw_only=True)
    guild_id: int = attr.ib(kw_only=True)
    channel_id: int = attr.ib(kw_only=True)

    # Fully optional items
    topic: str = attr.ib(default=None, kw_only=True)


@attr.s(slots=True)
class Helper:
    identifier: int = attr.ib(eq=True)
    total_messages: int = attr.ib(default=0, eq=False)
    total_conversations: int = attr.ib(default=0, eq=False)
    messages_per_conversation: List[int] = attr.ib(default=attr.Factory(list), eq=False)
    conversation_length: List[datetime.timedelta] = attr.ib(
        default=attr.Factory(list), eq=False
    )

    def get_average_messages_per_convo(self) -> int:
        """
        Returns the amount of messages this
        helper sends per conversation on average
        """
        return round(
            sum(self.messages_per_conversation) / len(self.messages_per_conversation)
        )

    def get_average_time_per_convo(self) -> int:
        """
        Returns the average amount of minutes
        spent per support conversation
        """
        time_in_seconds = sum(self.conversation_length) / len(self.conversation_length)
        return round(time_in_seconds / 60)


class Plots(Enum):
    HELPER_CONVOS_VS_CONVO_LENGTH = "helper_convos_vs_convo_length_plot.png"
    HELPER_CONVO_TIME_VS_CONVO_LENGTH = "helper_convo_time_vs_convo_length_plot.png"
    AVERAGE_SUPPORT_RESPONSE_TIME = "average_support_response_time.png"
