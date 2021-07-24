import datetime
import itertools
import os
from pathlib import Path
from typing import List

import aiosqlite
import discord
import seaborn as sns
from matplotlib import pyplot as plt, ticker

from conversations import Conversation, Message, Helper, Plots
from conversations.abc import DataStore
from conversations.datastore import Sqlite


class Manager:
    # TODO Let boosters see there own stats
    conversation_identifier = itertools.count().__next__

    def __init__(self, datastore: DataStore):
        self.datastore = datastore

        # A dict of Conversation,
        # such that users being helped maps to conversations
        self.current_conversation = {}

        self.helpers = None

        self.cwd = str(Path(__file__).parents[0])

        self.has_init = False

    async def _initialize(self):
        """
        An internal async method for ensuring
        things are setup before usage
        """
        if self.has_init:
            return

        if not self.helpers:
            helpers = await self.datastore.fetch_all_helpers()

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

        Path(os.path.join(self.cwd, "generated_plots", "old")).mkdir(
            parents=True, exist_ok=True
        )

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
                    self.helpers[helper_id].conversation_length.append(
                        conversation.end_time - conversation.start_time
                    )
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
                    message.created_at,
                    is_helper=True if message.author.id in self.helper_ids else False,
                )
            )

            conversation.last_message_id = message.id
            conversation.end_time = message.created_at

        # Finish the last convo and add it
        await self.datastore.save_conversation(conversation)
        finished.append(conversation)

        # for helper in self.helpers.values():
        # await self.datastore.store_helper(helper)

        return finished

    async def build_timed_scatter_plot(self):
        conversations: List[
            Conversation
        ] = await self.datastore.fetch_all_conversations()  # noqa
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
        """
        Builds a plot of 'helpers' vs the average
        length of there conversations

        """
        plt.clf()
        helpers: List[Helper] = await self.datastore.fetch_all_helpers()  # noqa
        total_conversations = [helper.total_conversations for helper in helpers]

        avg_messages = [helper.messages_per_conversation for helper in helpers]

        y = []
        for msg in avg_messages:
            y.append(sum(msg) / len(msg))

        plt.plot(total_conversations, y, "o", color="black")

        move_amount = self.get_one_point_five_percent(max(total_conversations))
        for i in range(len(total_conversations)):
            user = await guild.fetch_member(helpers[i].identifier)
            offset = total_conversations[i] + move_amount
            plt.annotate(user.display_name, (offset, y[i]))

        plt.xlabel("Total Support Conversations")
        plt.ylabel("Average Messages Per Conversation")
        plt.title("Total Support Conversations x Average Messages Per Convo")

        return plt

    async def build_helper_convo_time_vs_total_convo_plot(self, guild) -> plt:
        """
        Builds and returns a plot for the
        average conversation time of a helper
        plotted against total conversations
        """
        plt.clf()
        helpers: List[Helper] = await self.datastore.fetch_all_helpers()  # noqa
        total_conversations = [helper.total_conversations for helper in helpers]
        average_help_times_raw = [helper.conversation_length for helper in helpers]

        average_help_times = []
        for x in average_help_times_raw:
            time_in_seconds = sum(x, datetime.timedelta()) / len(x)
            time_in_minutes = round(time_in_seconds.total_seconds() / 60)
            average_help_times.append(time_in_minutes)

        plt.plot(total_conversations, average_help_times, "o", color="black")
        plt.ylabel("Average conversation length (Minutes)")
        plt.xlabel("Average Messages Per Conversation")
        plt.title("Total Support Conversations x Average convo length")

        move_amount = self.get_one_point_five_percent(max(total_conversations))
        for i in range(len(total_conversations)):
            user = await guild.fetch_member(helpers[i].identifier)
            offset = total_conversations[i] + move_amount
            plt.annotate(user.display_name, (offset, average_help_times[i]))

        return plt

    async def build_average_support_response_time(self) -> plt:
        """
        Builds and returns a plot showing the average
        support response time
        """
        plt.clf()
        conversations = await self.datastore.fetch_all_conversations()
        response_times = []
        for conversation in conversations:
            for message in conversation.messages:
                if message.is_helper:
                    offset = message.timestamp - conversation.start_time
                    time = offset.total_seconds() / 60  # Minutes
                    if time > 100:
                        # Fuck the outliers
                        continue
                    response_times.append(time)

        sns.set_style("whitegrid")
        ax = sns.histplot(data=response_times, bins=200)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(150))

        plt.xlabel("Average support response time (Minutes)")
        plt.ylabel("Conversations")
        plt.title("Average time taken to respond to support queries")

        return plt

    async def get_message_stats(self) -> discord.Embed:
        if not isinstance(self.datastore, Sqlite):
            # TODO Get this to work with API
            # can't call this on anything but sqlite datastore
            raise NotImplementedError

        # To run the sqlite decorator
        await self.datastore.fetch_current_conversation_count()

        messages = []
        async with aiosqlite.connect(self.datastore.db) as db:
            async with db.execute(
                "SELECT "
                "   author_id, channel_id, content,"
                "   guild_id, message_id, datetime(timestamp), is_helper "
                "FROM Message "
            ) as messages_cursor:
                all_msgs = await messages_cursor.fetchall()
                for val in all_msgs:
                    messages.append(
                        Message(
                            author_id=val[0],
                            channel_id=val[1],
                            content=val[2],
                            guild_id=val[3],
                            message_id=val[4],
                            timestamp=val[5],
                            is_helper=val[6],
                        )
                    )

        messages = set(messages)
        unique_authors = set(msg.author_id for msg in messages)
        total_authors = len(unique_authors)
        total_messages = len(messages)
        total_helper_messages = len([x for x in messages if x.is_helper])

        embed = discord.Embed(
            title="Message Stats",
            description=f"""
            Total authors: `{total_authors}`
            Total messages: `{total_messages}`
            
            Total helper messages: `{total_helper_messages}`
            Total helpee messages: `{total_messages - total_helper_messages}`
            """,
        )
        # TODO humanize this

        return embed

    @classmethod
    def get_next_conversation_id(cls) -> int:
        return cls.conversation_identifier()

    @staticmethod
    def get_one_point_five_percent(total) -> int:
        """
        A simple helper method to get 5 percent
        of a given number.
        Is useful for plots
        """
        return round(total * 0.015, 2)

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
        Path(os.path.join(self.cwd, "generated_plots", "old", dir_name.lower())).mkdir(
            parents=True, exist_ok=True
        )

        timestamp = datetime.datetime.now()
        new_file_name = f"replaced_at_{timestamp.strftime('%f_%S_%M_%H_%d_%m_%Y')}.png"
        new_file_name = os.path.join(to_save_dir, new_file_name)

        os.replace(old_plot_dir, new_file_name)
