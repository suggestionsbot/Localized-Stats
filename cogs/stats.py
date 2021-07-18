import cProfile
import pstats
import timeit

import discord
from discord.ext import commands


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__}: Ready")

    @commands.command(aliases=["bps", "buildpaststats"])
    @commands.has_role(603803993562677258)
    async def build_past_stats(self, ctx, channel: discord.TextChannel = None):
        """Builds stats for the given channel using all of the currently stored messages"""
        start_time = timeit.default_timer()
        async with ctx.typing():
            with cProfile.Profile() as pr:
                convos = await self.bot.manager.build_past_conversations(channel)

            stats = pstats.Stats(pr)
            stats.sort_stats(pstats.SortKey.TIME)
            stats.dump_stats(filename="profile.prof")

        total_messages = 0
        for convo in convos:
            total_messages += len(convo.messages)

        elapsed = timeit.default_timer() - start_time

        await ctx.send(
            f"Total conversations: `{len(convos)}`\nTotal messages:`{total_messages}`\nElapsed seconds: {elapsed}"
        )

    @commands.command(aliases=["ms"])
    @commands.is_owner()
    async def message_stats(self, ctx):
        """Shows stats for all messages"""
        embed = await self.bot.manager.get_message_stats()
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Stats(bot))
