from discord.ext import commands

from utils.util import Pag


class Help(commands.Cog, name="Help command"):
    def __init__(self, bot):
        self.bot = bot
        self.cmds_per_page = 10

    @staticmethod
    def get_command_signature(command: commands.Command, ctx: commands.Context):
        aliases = "|".join(command.aliases)
        cmd_invoke = f"[{command.name}|{aliases}]" if command.aliases else command.name

        full_invoke = command.qualified_name.replace(command.name, "")

        signature = f"{ctx.prefix}{full_invoke}{cmd_invoke} {command.signature}"
        return signature

    async def return_filtered_commands(self, walkable, ctx, hide_hidden=True):
        filtered = []

        for c in walkable.walk_commands():
            try:
                if hide_hidden and c.hidden:
                    # command is hidden
                    continue

                # elif c.parent:
                #    # Command is a subcommand
                #    continue

                await c.can_run(ctx)
                filtered.append(c)
            except commands.CommandError:
                continue

        return self.return_sorted_commands(filtered)

    @staticmethod
    def return_sorted_commands(commandList):
        return sorted(commandList, key=lambda x: x.qualified_name)

    async def setup_help_pag(self, ctx, entity=None, title=None):
        entity = entity or self.bot
        title = title or self.bot.description

        pages = []

        if isinstance(entity, commands.Command):
            filtered_commands = (
                list(set(entity.all_commands.values()))
                if hasattr(entity, "all_commands")
                else []
            )
            filtered_commands.insert(0, entity)

        else:
            hide_hidden = (
                True
                if ctx.author.id not in (271612318947868673, 158063324699951104)
                else False
            )
            filtered_commands = await self.return_filtered_commands(
                entity, ctx, hide_hidden
            )

        for i in range(0, len(filtered_commands), self.cmds_per_page):

            next_commands = filtered_commands[i : i + self.cmds_per_page]
            command_entry = ""

            for cmd in next_commands:

                desc = cmd.short_doc or cmd.description
                signature = self.get_command_signature(cmd, ctx)
                extra = [
                    "Has subcommands" if hasattr(cmd, "all_commands") else None,
                    "Marked as hidden" if cmd.hidden else None,
                ]
                extra = list(filter(lambda x: x is not None, extra))
                aliases = "|".join(cmd.aliases)

                if isinstance(entity, commands.Command):
                    entry = f"• **__{cmd.name}__**\n```\n{signature}\n```\n"
                    if desc:
                        entry += f"{desc}\n"

                else:
                    entry = f"• **{cmd.qualified_name}**"
                    if aliases:
                        entry += f" -`{aliases}`"
                    entry += "\n"

                    if desc:
                        entry += f"{desc}\n"
                    if extra:
                        entry += f"    {' | '.join(extra)}\n"

                entry += "\n"

                command_entry += entry

            pages.append(command_entry)

        await Pag(
            title=title,
            colour=0xDD9323,
            entries=pages,
            length=1,
        ).start(ctx)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__}: Ready")

    @commands.command(name="help", aliases=["commands"])
    async def help_command(self, ctx, *, entity=None):
        """
        Sends a paginated help command or help for an existing entity.
        """

        if not entity:
            await self.setup_help_pag(ctx)

        else:
            cog = self.bot.get_cog(entity)
            if cog:
                await self.setup_help_pag(ctx, cog, f"{cog.qualified_name}'s commands")

            else:
                command = self.bot.get_command(entity)
                if command:
                    await self.setup_help_pag(ctx, command, command.name)

                else:
                    await ctx.send("Entity not found.")


def setup(bot):
    bot.add_cog(Help(bot))
