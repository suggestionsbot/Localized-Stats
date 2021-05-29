import datetime
import itertools
import os
from pathlib import Path
from typing import List

import discord
from matplotlib import pyplot as plt

from conversations import Conversation, Message, Helper, Plots
from conversations.abc import DataStore


class Manager:
    conversation_identifier = itertools.count().__next__

    def __init__(self, datastore: DataStore):
        self.datastore = datastore

        # A dict of Conversation,
        # such that users being helped maps to conversations
        self.current_conversation = {}

        self.helpers = None

        self.cwd = str(Path(__file__).parents[0])

    async def _initialize(self):
        """
        An internal async method for ensuring
        things are setup before usage
        """
        if not self.helpers:
            helpers = await self.datastore.fetch_helpers()

            self.helpers = {}
            for helper in helpers:
                self.helpers[helper.identifier] = helper

            self.helper_ids = list(self.helpers.keys())

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
        current_helpers = {}
        async for message in channel.history(limit=None, oldest_first=True):
            if not conversation and message.author.id not in self.helper_ids:
                # Start a new conversation
                conversation = Conversation(
                    message.id,
                    message.author.id,
                    start_time=message.created_at,
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
                for helper_id, msg_count in current_helpers.items():
                    self.helpers[helper_id].messages_per_conversation.append(msg_count)
                    self.helpers[helper_id].total_conversations += 1

                current_helpers = {}

                await self.datastore.save_conversation(conversation)
                finished.append(conversation)

                conversation = Conversation(
                    message.id,
                    message.author.id,
                    start_time=message.created_at,
                    channel_id=message.channel.id,
                    guild_id=message.guild.id,
                    identifier=self.get_next_conversation_id(),
                )

            if message.author.id in self.helper_ids:
                if message.author.id not in current_helpers:
                    current_helpers[message.author.id] = 0

                current_helpers[message.author.id] += 1

                helper = self.helpers[message.author.id]
                helper.total_messages += 1

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
            conversation.end_time = message.created_at

        # Finish the last convo and add it
        await self.datastore.save_conversation(conversation)
        finished.append(conversation)

        for helper in self.helpers.values():
            await self.datastore.store_helper(helper)

        return finished

    async def build_timed_scatter_plot(self):
        conversations = await self.fetch_all_conversations()
        messages = [len(convo.messages) for convo in conversations]
        time = [
            ((convo.end_time - convo.start_time).total_seconds() / 60)
            for convo in conversations
        ]

        plt.plot(time, messages, "o", color="black")
        plt.xlabel("Time (Minutes)")
        plt.ylabel("Messages (Per conversations)")
        plt.title("Time x Messages in #support")
        plt.show()

    async def build_helper_convos_vs_convo_length_plot(self, guild) -> plt:
        helpers = await self.fetch_all_helpers()

        total_conversations = [helper.total_conversations for helper in helpers]

        avg_messages = [helper.messages_per_conversation for helper in helpers]

        y = []
        for msg in avg_messages:
            y.append(sum(msg) / len(msg))

        plt.plot(total_conversations, y, "o", color="black")

        for i in range(len(total_conversations)):
            user = await guild.fetch_member(helpers[i].identifier)
            plt.annotate(user.display_name, ((total_conversations[i] + 50), y[i]))

        plt.xlabel("Total Support Conversations")
        plt.ylabel("Average Messages Per Conversation")
        plt.title("Total Support Conversations x Average Messages Per Convo")

        return plt

    async def fetch_all_helpers(self) -> List[Helper]:
        raw_helpers = await self.datastore.get_all_helpers()
        helpers = []
        for helper in raw_helpers:
            helper.pop("_id")
            helpers.append(Helper(**helper))

        return helpers

    async def fetch_all_conversations(self) -> List[Conversation]:
        """
        Fetchs all conversations and builds the
        relevant dataclasses before returning em

        Returns
        -------
        List[Conversation]
            It says it all
        """
        conversations = []
        raw_convos = await self.datastore.get_all_conversations()
        for convo in raw_convos:
            convo.pop("_id")
            messages = []
            for message in convo["messages"]:
                messages.append(Message(**message))

            convo["messages"] = messages
            conversations.append(Conversation(**convo))

        return conversations

    @classmethod
    def get_next_conversation_id(cls) -> int:
        return cls.conversation_identifier()

    def save_plot(self, plot: plt, name: Plots):
        """Saves a plot to disk"""
        save_location = os.path.join(self.cwd, "generated_plots", name.value)
        if os.path.isfile(save_location):
            self._preserve_plot(save_location, name.name)

        plot.savefig(save_location)

    def get_plot_image(self, name: Plots) -> discord.File:
        """Gets a plots image from disk and returns it for usage in discord"""
        saved_location = os.path.join(self.cwd, "generated_plots", name.value)
        file = discord.File(fp=saved_location, filename=name.value)
        return file

    def _preserve_plot(self, old_plot_dir: str, dir_name: str):
        """Preserves an old plot by moving it to a save directory"""
        to_save_dir = os.path.join(self.cwd, "generated_plots", "old", dir_name.lower())
        if not os.path.isdir(to_save_dir):
            os.mkdir(to_save_dir)

        timestamp = datetime.datetime.now()
        new_file_name = f"replaced_at_{timestamp.strftime('%f_%S_%M_%H_%d_%m_%Y')}.png"
        new_file_name = os.path.join(to_save_dir, new_file_name)

        os.replace(old_plot_dir, new_file_name)
