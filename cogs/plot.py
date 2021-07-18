import discord
from discord.ext import commands

from conversations import Plots


class Plot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__}: Ready")

    @commands.group()
    async def plot(self, ctx):
        """The entry point for all plot commands"""
        await ctx.invoke(self.bot.get_command("help"), entity="plot")

    @plot.command(aliases=["hcl"])
    @commands.cooldown(1, 30)
    async def helper_convos_vs_convo_length(self, ctx):
        """Builds a plot of helper conversation times vs lengths"""
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

    @plot.command(aliases=["htl"])
    @commands.cooldown(1, 30)
    async def helper_time_vs_length_convos(self, ctx):
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

    @plot.command(aliases=["srt"])
    @commands.cooldown(1, 30)
    async def average_support_response_time(self, ctx):
        """Builds a histogram plotting average support response time"""
        async with ctx.typing():
            plot = await self.bot.manager.build_average_support_response_time()
            enum = Plots.AVERAGE_SUPPORT_RESPONSE_TIME
            self.bot.manager.save_plot(plot, enum)

            file: discord.File = self.bot.manager.get_plot_image(enum)
            embed = discord.Embed(
                title="Average Support Response Time",
                description="Values over 100 minutes are considered to be outliers and are discarded.",
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
    bot.add_cog(Plot(bot))
