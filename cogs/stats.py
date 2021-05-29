import discord
from discord.ext import commands
from discord.ext.commands import BucketType

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
        async with ctx.typing():
            convos = await self.bot.manager.build_past_conversations(channel)

        total_messages = 0
        for convo in convos:
            total_messages += len(convo.messages)

        await ctx.send(
            f"Total conversations: `{len(convos)}`\nTotal messages:`{total_messages}`"
        )

    @commands.command(aliases=["ah"])
    @commands.has_role(603803993562677258)
    async def add_helper(self, ctx, member: discord.Member):
        """Registers a helper internally"""
        await self.bot.datastore.store_helper(Helper(member.id, 0, 0, []))
        await ctx.send(f"Added `{member.display_name}` as a helper internally")

    @commands.command(aliases=["bhcl", "helper_support_plot"])
    @commands.cooldown(1, 60)
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
            self.bot.manager.save_plot(plot, Plots.HELPER_CONVOS_VS_CONVO_LENGTH)

            file: discord.File = self.bot.manager.get_plot_image(
                Plots.HELPER_CONVOS_VS_CONVO_LENGTH
            )
            embed = discord.Embed(
                title="Support Team\nConversations vs Average Conversation Length",
                timestamp=ctx.message.created_at,
            )
            embed.set_footer(text="Valid as at")

        await self.bot.send_attachment_in_embed(
            ctx,
            embed,
            file,
            file_name=Plots.HELPER_CONVOS_VS_CONVO_LENGTH.value.lower(),
        )


def setup(bot):
    bot.add_cog(Stats(bot))
