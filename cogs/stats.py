import timeit

import discord
from discord.ext import commands

from conversations import Helper, Plots


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
            convos = await self.bot.manager.build_past_conversations(channel)

        total_messages = 0
        for convo in convos:
            total_messages += len(convo.messages)

        elapsed = timeit.default_timer() - start_time

        await ctx.send(
            f"Total conversations: `{len(convos)}`\nTotal messages:`{total_messages}`\nElapsed seconds: {elapsed}"
        )

    @commands.command(aliases=["ah"])
    @commands.has_role(603803993562677258)
    async def add_helper(self, ctx, member: discord.Member):
        """Registers a helper internally"""
        await self.bot.datastore.store_helper(Helper(member.id, 0, 0, []))
        await ctx.send(f"Added `{member.display_name}` as a helper internally")

    @commands.command(aliases=["bhcl"])
    # @commands.cooldown(1, 60)
    @commands.is_owner()
    async def build_helper_convos_vs_convo_length_plot(
        self,
        ctx: discord.ext.commands.Context,
    ):
        """Builds a scatter plot of Time x Messages"""
        async with ctx.typing():
            plot = await self.bot.manager.build_helper_convos_vs_convo_length_plot(
                ctx.guild
            )
            enum = Plots.HELPER_CONVOS_VS_CONVO_LENGTH
            self.bot.manager.save_plot(plot, enum)

            file: discord.File = self.bot.manager.get_plot_image(enum)
            embed = discord.Embed(
                title="Support Team\nConversations vs Average Conversation Length",
                timestamp=ctx.message.created_at,
            )
            embed.set_footer(text="Valid as at")

        await self.bot.send_attachment_in_embed(
            ctx,
            embed,
            file,
            file_name=enum.value.lower(),
        )

    @commands.command(aliases=["bhtl"])
    @commands.cooldown(1, 60)
    @commands.is_owner()
    async def build_helper_time_vs_length_convos(self, ctx):
        """Builds a plot of helper convo times vs lengths"""
        async with ctx.typing():
            plot = await self.bot.manager.build_helper_convo_time_vs_total_convo_plot(
                ctx.guild
            )
            enum = Plots.HELPER_CONVO_TIME_VS_CONVO_LENGTH
            self.bot.manager.save_plot(plot, enum)

            file: discord.File = self.bot.manager.get_plot_image(enum)
            embed = discord.Embed(
                title="Support Team\nAverage Conversation Time vs Average Conversation Length",
                timestamp=ctx.message.created_at,
            )
            embed.set_footer(text="Valid as at")

        await self.bot.send_attachment_in_embed(
            ctx,
            embed,
            file,
            file_name=enum.value.lower(),
        )


def setup(bot):
    bot.add_cog(Stats(bot))
