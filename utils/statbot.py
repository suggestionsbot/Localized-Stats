import re
from typing import Union

import discord
import motor.motor_asyncio
from discord.ext import commands
from discord.ext.commands import MinimalHelpCommand

from .document import Document


class StatBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            command_prefix=self.get_prefix,
            help_command=None,
        )

        self.PREFIX = "$"
        self.mention = re.compile(r"^<@!?(?P<id>\d+)>$")

        self.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(kwargs.pop("mongo")))
        self.db = self.mongo["localized_stats"]
        self.command_usage = Document(self.db, "command_usage")

    async def get_prefix(self, message):
        prefix = self.PREFIX
        if message.content.casefold().startswith(prefix.casefold()):
            # The prefix matches, now return the one the user used
            # such that dpy will dispatch the given command
            prefix_length = len(prefix)
            prefix = message.content[:prefix_length]

        return commands.when_mentioned_or(prefix)(self, message)

    async def on_ready(self):
        print(f"{self.__class__.__name__}: Ready")

    async def on_message(self, message):
        # Ignore messages sent by bots
        if message.author.bot:
            return

        if match := self.mention.match(message.content):
            if int(match.group("id")) == self.user.id:
                await message.channel.send(
                    f"My prefix here is `{self.PREFIX}`", delete_after=15
                )

        await self.process_commands(message)

    async def on_command_completion(self, ctx):
        if ctx.command.qualified_name == "logout":
            return

        if await self.command_usage.find(ctx.command.qualified_name) is None:
            await self.command_usage.upsert(
                {"_id": ctx.command.qualified_name, "usage_count": 1}
            )
        else:
            await self.command_usage.increment(
                ctx.command.qualified_name, 1, "usage_count"
            )

    @staticmethod
    def clean_code(content):
        """Automatically removes code blocks from the code."""
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:])[:-3]
        else:
            return content

    @staticmethod
    async def send_attachment_in_embed(
        channel: Union[discord.TextChannel, discord.ext.commands.Context],
        embed: discord.Embed,
        file: discord.File,
        file_name: str = None,
    ):
        """
        Since dpy is fucky with regard to image naming
        and the ability to send attachments within embeds
        this functions as an in-between to facilitate it.

        Parameters
        ----------
        channel : discord.TextChannel
            Where to send said embed with file
        embed : discord.Embed
            The embed to send
        file : discord.File
            The file we want embedded
        file_name : str
            An optional alphanumeric name to use as filename
        """
        file.filename = file_name
        embed.set_image(url=f"attachment://{file_name}")

        await channel.send(embed=embed, file=file)
