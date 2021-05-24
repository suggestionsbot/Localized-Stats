import re

import discord
from discord.ext import commands


class StatBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, command_prefix=self.get_prefix)

        self.PREFIX = "$"
        self.mention = re.compile(r"^<@!?(?P<id>\d+)>$")

    async def get_prefix(self, message):
        prefix = self.PREFIX
        if message.content.casefold().startswith(prefix.casefold()):
            # The prefix matches, now return the one the user used
            # such that dpy will dispatch the given command
            prefix_length = len(prefix)
            prefix = message.content[:prefix_length]

        return commands.when_mentioned_or(prefix)(self, message)

    async def on_ready(self):
        print(f"{self.__class__.__name__} is up & ready to go")

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

    def clean_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:])[:-3]
        else:
            return content
