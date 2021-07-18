import discord
import humanize
from discord.ext import commands


class Helper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__}: Ready")

    @commands.group(invoke_without_command=True, aliases=["h"])
    async def helper(self, ctx):
        """The entry point for all helper commands."""
        await ctx.invoke(self.bot.get_command("help"), entity="helper")

    @helper.command(name="stats")
    @commands.cooldown(1, 5)
    async def stats(self, ctx, helper: discord.Member = None):
        """Get the stats of a helper!"""
        user = helper or ctx.author
        helper = await self.bot.manager.datastore.fetch_helper(user.id)
        if not helper:
            return await ctx.send("This person is not a registered helper.")

        embed = discord.Embed(
            title=f"Stats for `{user.display_name}`",
            description=f"""Total Messages: `{humanize.intcomma(helper.total_messages)}`
            Total Conversations: `{humanize.intcomma(helper.total_conversations)}`
            Average Messages Per Convo: `{helper.get_average_messages_per_convo()}`
            Average Time Per Convo: `{helper.get_average_time_per_convo()}` minutes
            """,
            timestamp=ctx.message.created_at,
        )
        embed.set_footer(text="Valid as at")

        await ctx.send(embed=embed)

    @commands.command(name="add")
    @commands.has_role(603803993562677258)
    async def add(self, ctx, member: discord.Member):
        """Registers a helper internally"""
        await self.bot.datastore.store_helper(Helper(member.id))
        await ctx.send(f"Added `{member.display_name}` as a helper internally")


def setup(bot):
    bot.add_cog(Helper(bot))
