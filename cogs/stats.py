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

    @commands.command(aliases=["ms"])
    @commands.is_owner()
    async def message_stats(self, ctx):
        """Shows stats for all messages"""
        embed = await self.bot.manager.get_message_stats()
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Stats(bot))
