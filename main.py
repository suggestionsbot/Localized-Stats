import io
import os
import re
import logging
import textwrap
import contextlib
from traceback import format_exception

import discord
from discord.ext import commands

from conversations import Manager, Mongo, Helper, Plots
from utils import StatBot
from utils.util import Pag

MONGO_URL = os.getenv("MONGO")
TOKEN = os.getenv("TOKEN")

logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(module)s | %(message)s",
    datefmt="%d/%m/%Y %I:%M:%S %p",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


intents = discord.Intents.default()

bot = StatBot(
    case_insensitive=True,
    intents=intents,
    activity=discord.Game(name="Playing with statistics"),
)

bot.datastore = Mongo(MONGO_URL)
bot.manager = Manager(bot.datastore)


@bot.command(aliases=["bs", "buildstats"])
@commands.has_role(603803993562677258)
async def build_stats(ctx, channel: discord.TextChannel = None):
    """Builds stats for the given channel"""
    async with ctx.typing():
        convos = await bot.manager.build_past_conversations(channel)

    total_messages = 0
    for convo in convos:
        total_messages += len(convo.messages)

    await ctx.send(
        f"Total conversations: `{len(convos)}`\nTotal messages:`{total_messages}`"
    )


@bot.command(aliases=["ah"])
@commands.has_role(603803993562677258)
async def add_helper(ctx, member: discord.Member):
    """Registers a helper internally"""
    await bot.datastore.store_helper(Helper(member.id, 0, 0, []))
    await ctx.send(f"Added `{member.display_name}` as a helper internally")


@bot.command()
@commands.is_owner()
async def logout(ctx):
    """Log's the bot out of discord"""
    await ctx.send("Cya :wave:")
    await bot.logout()


@bot.command()
@commands.is_owner()
async def create_indexes(ctx):
    """Log's the bot out of discord"""
    await bot.datastore.create_indexes()


@bot.command()
@commands.is_owner()
async def gen_scatter_timexmessages(ctx):
    """Builds a scatter plot of Time x Messages"""
    await bot.manager.build_timed_scatter_plot()


@bot.command(aliases=["bhcl", "helper_support_plot"])
@commands.is_owner()
async def build_helper_convos_vs_convo_length_plot(ctx: discord.ext.commands.Context):
    """Builds a scatter plot of Time x Messages"""
    async with ctx.typing():
        plot = await bot.manager.build_helper_convos_vs_convo_length_plot(ctx.guild)
        bot.manager.save_plot(plot, Plots.HELPER_CONVOS_VS_CONVO_LENGTH)

        file: discord.File = bot.manager.get_plot_image(
            Plots.HELPER_CONVOS_VS_CONVO_LENGTH
        )
        embed = discord.Embed(
            title="Support Team\nConversations vs Average Conversation Length",
            timestamp=ctx.message.created_at,
        )
        embed.set_image(url=f"attachment://{Plots.HELPER_CONVOS_VS_CONVO_LENGTH.value}")

        embed.set_footer(text="Valid as at")

    await ctx.send(embed=embed, file=file)


@bot.command(name="eval", aliases=["exec"])
@commands.is_owner()
async def _eval(ctx, *, code):
    """
    Evaluates given code.
    """
    code = bot.clean_code(code)

    local_variables = {
        "discord": discord,
        "commands": commands,
        "bot": bot,
        "ctx": ctx,
        "channel": ctx.channel,
        "author": ctx.author,
        "guild": ctx.guild,
        "message": ctx.message,
    }

    stdout = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout):
            exec(
                f"async def func():\n{textwrap.indent(code, '    ')}",
                local_variables,
            )

            obj = await local_variables["func"]()
            result = f"{stdout.getvalue()}\n-- {obj}\n"

    except Exception as e:
        result = "".join(format_exception(e, e, e.__traceback__))

    pager = Pag(
        entries=[result[i : i + 2000] for i in range(0, len(result), 2000)],
        length=1,
        prefix="```py\n",
        suffix="```",
    )

    await pager.start(ctx)


if __name__ == "__main__":
    bot.run(TOKEN)
