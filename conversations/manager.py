import itertools

import discord

from conversations import Conversation, Message
from conversations.abc import DataStore


class Manager:
    conversation_identifier = itertools.count().__next__

    def __init__(self, datastore: DataStore):
        self.datastore = datastore

        # A dict of Conversation,
        # such that users being helped maps to conversations
        self.current_conversation = {}

        self.helpers = None

    async def _initialize(self):
        """
        An internal async method for ensuring
        things are setup before usage
        """
        if not self.helpers:
            self.helpers = await self.datastore.fetch_helpers()
            self.helper_ids = [helper.identifier for helper in self.helpers]

        if self.conversation_identifier() == 1:
            current_conversation_id = (
                await self.datastore.fetch_current_conversation_count()
            )
            self.conversation_identifier = itertools.count(
                start=current_conversation_id
            ).__next__

    async def build_past_conversations(self, channel: discord.TextChannel):
        """
        Builds & stores conversations from a given
        text channels history. Is non-interactive
        and works entirely on already sent messages
        """
        await self._initialize()

        conversation = None
        finished = []
        async for message in channel.history(limit=None, oldest_first=True):
            if not conversation and message.author.id not in self.helper_ids:
                # Start a new conversation
                conversation = Conversation(
                    message.id,
                    message.author.id,
                    channel_id=message.channel.id,
                    guild_id=message.guild.id,
                    identifier=self.get_next_conversation_id(),
                )

            elif (
                conversation
                and message.author.id != conversation.user_being_helped
                and message.author.id not in self.helper_ids
            ):
                # Start a new conversation
                finished.append(conversation)

                conversation = Conversation(
                    message.id,
                    message.author.id,
                    channel_id=message.channel.id,
                    guild_id=message.guild.id,
                    identifier=self.get_next_conversation_id(),
                )

            conversation.messages.append(
                Message(
                    message.author.id,
                    message.channel.id,
                    message.content,
                    message.guild.id,
                    message.id,
                    is_helper=True if message.author.id in self.helper_ids else False,
                )
            )

            conversation.last_message_id = message.id

        # Finish the last convo and add it
        finished.append(conversation)

        # pprint(finished)
        return finished

    @classmethod
    def get_next_conversation_id(cls) -> int:
        return cls.conversation_identifier()
