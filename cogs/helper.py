import discord
import humanize
from discord.ext import commands

import conversations.dataclasses as dc
from conversations.datastore import ApiStore


def is_donator_or_staff():
    async def wraps(ctx):
        guild = ctx.bot.get_guild(601219766258106399)
        member = guild.get_member(ctx.author.id)
        role = guild.get_role(780511444810596362)
        helpers = guild.get_role(602552702785945624)
        mods = guild.get_role(601235098502823947)
        check_one = role in member.roles
        check_two = helpers in member.roles
        check_three = mods in member.roles

        return check_one or check_two or check_three

    return commands.check(wraps)


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

    @helper.command()
    @is_donator_or_staff()
    async def create(self, ctx, member: discord.Member = None):
        """Registers a helper internally"""
        member = member or ctx.author

        if not isinstance(self.bot.datastore, ApiStore):
            raise NotImplementedError

        current_accounts = await self.bot.datastore.fetch_all_users()
        users = [x["username"] for x in current_accounts["all_users"]]
        user_ids = [x["discord_user_id"] for x in current_accounts["all_users"]]

        if member.id in user_ids:
            return await ctx.send("You already have an account")

        def check(m):
            return m.author.id == member.id

        while True:
            await member.send("What do you want your username to be?")
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            username = msg.content
            if username in users:
                formatted_users = "\n".join(users)
                await ctx.send(
                    f"This name is not unique. Please try again.\nCurrent Names: \n`{formatted_users}`"
                )
                continue

            break

        while True:
            await member.send("What do you want your password to be?")
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            password = msg.content
            break

        await self.bot.datastore.store_helper(
            dc.Helper(member.id),
            username,
            password,
            member.id in self.bot.internal_helpers,
        )
        await ctx.send("I have added your account.")


def setup(bot):
    bot.add_cog(Helper(bot))
