import discord
import traceback
import sys
from discord.ext import commands


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, "on_error"):
            return

        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound,)
        sending_err_errors = (commands.BadArgument, commands.ArgumentParsingError)

        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(f"`{ctx.command}` has been disabled.")

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(
                    f"`{ctx.command}` can not be used in Private Messages."
                )
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send("This command can only be used in Private Messages.")

        elif isinstance(error, sending_err_errors):
            await ctx.send(embed=discord.Embed(description=error))

        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(
                f"`{perm.replace('_', ' ').title()}`" for perm in error.missing_perms
            )

            await ctx.send(f"You're missing the permissions: {perms}")

        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(
                f"`{perm.replace('_', ' ').title()}`" for perm in error.missing_perms
            )

            await ctx.send(f"I'm missing the permissions: {perms}")

        elif isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send(
                f"`{ctx.command.qualified_name}` can only be "
                f"used {error.number} command(s) at a time under {str(error.per)}"
            )

        print("Ignoring exception in command {}:".format(ctx.command), file=sys.stderr)
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr
        )


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
