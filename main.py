import io
import os
import logging
import random
import string
import textwrap
import contextlib
from traceback import format_exception

import discord
from discord.ext import commands

from conversations import Manager, Mongo, Helper, Plots
from conversations.datastore import Sqlite, ApiStore
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


intents = discord.Intents.all()

bot = StatBot(
    case_insensitive=True,
    intents=intents,
    activity=discord.Game(name="Playing with statistics"),
    mongo=MONGO_URL,
)

bot.datastore = ApiStore()
# bot.datastore = Mongo(MONGO_URL)
# bot.datastore = Sqlite()
bot.manager = Manager(bot.datastore)

bot.internal_helpers = (
    203104843479515136,
    289546108751839232,
    456174857034661888,
    726531923131891782,
    221091847412383754,
    158063324699951104,
    271612318947868673,
    651386805043593237,
)
bot.internal_helpers = set(bot.internal_helpers)
bot.leadership = (271612318947868673, 158063324699951104)
bot.leadership = set(bot.leadership)


def get_random_string():
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(8))


@bot.command(enabled=False)
@commands.is_owner()
async def setup_helpers(ctx):
    stuff = {}
    for user_id in bot.internal_helpers:
        member = ctx.guild.get_member(user_id)
        password = get_random_string()

        if user_id == 289546108751839232:
            name = "InteriorHood"
        else:
            name = member.name

        stuff[name] = password

        await bot.datastore.store_helper(Helper(member.id), name, password, True)

    print(stuff)
    await ctx.send(stuff)


@bot.command()
@commands.is_owner()
async def logout(ctx):
    """Log's the bot out of discord"""
    await ctx.send("Cya :wave:")
    await bot.logout()


@bot.command(aliases=["gh"], enabled=False)
@commands.is_owner()
async def get_helpers(ctx):
    """Mongo Helpers -> SQlite"""
    mongo = Mongo("MONGO_URL")
    x = await mongo.fetch_helpers()
    helpers = [x.identifier for x in x]
    for h in helpers:
        await bot.datastore.store_helper(Helper(identifier=h))
    await ctx.send(helpers)


@bot.command(name="eval", aliases=["exec"], hidden=True)
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
            exec(f"async def func():\n{textwrap.indent(code, '    ')}", local_variables)

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
    for ext in os.listdir("./cogs/"):
        if ext.endswith(".py") and not ext.startswith("_"):
            try:
                bot.load_extension(f"cogs.{ext[:-3]}")
            except Exception as e:
                print(
                    "An error occurred while loading ext cogs.{}: {}".format(
                        ext[:-3], e
                    )
                )

    bot.run(TOKEN)
