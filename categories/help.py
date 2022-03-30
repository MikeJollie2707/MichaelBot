# The entire file will base on the assumption that there is no help slash command.
# This is because it's not certain `help <command>` will return slash command or prefix command.
# The main idea of a slash command is that it'll display all slash commands, an a prefix...
# ...help command will display all prefix commands. However, it's not really needed to do the former...
# ...because there's literally a menu on Discord for that.

import lightbulb
import hikari

import datetime as dt
import typing as t

from utilities.navigator import MenuComponent, MenuInteractionWrapper, ButtonPages
import utilities.helpers as helpers

__PREFIX_COMMAND_TYPES__ = (
    lightbulb.PrefixCommand, 
    lightbulb.PrefixCommandGroup, 
    lightbulb.PrefixSubGroup,
    lightbulb.PrefixSubCommand,
)
# Put it here just in case.
__SLASH_COMMAND_TYPES__ = (
    lightbulb.SlashCommand,
    lightbulb.SlashCommandGroup,
    lightbulb.SlashSubGroup,
    lightbulb.SlashSubCommand,
)

def filter_command_type(commands: t.Sequence[lightbulb.Command], types: t.Sequence[t.Type], remove_hidden: bool = False) -> t.List[lightbulb.Command]:
    '''
    Filter commands with one of the type mentioned in `types`.

    Parameter:
    - `commands`: A sequence of commands.
    - `types`: A sequence of command's types to filter. Example: `(lightbulb.PrefixCommand, lightbulb.SlashCommand)`.
    - `remove_hidden`: Whether or not to remove hidden commands. Default to `False`.
    '''
    
    l = []
    for command in commands:
        if isinstance(command, types):
            if (not remove_hidden) or (remove_hidden and not command.hidden):
                l.append(command)
    return l

def plugin_help_format(ctx: lightbulb.Context, plugin: lightbulb.Plugin) -> t.List[hikari.Embed]:
    MAX_COMMANDS = 10
    display = ""
    plugins = []
    
    commands: t.List[lightbulb.Command] = filter_command_type(plugin.all_commands, __PREFIX_COMMAND_TYPES__, True)
    commands.sort(key = lambda command: command.name)
    for index, command in enumerate(commands):
        # Signature includes command name.
        command_title = command.signature
        
        display += f"**{command_title}:**\n"
        description = command.description
        if description is None or description == "":
            description = "*No help provided*"    
        display += f"- {description}\n\n"

        if index == MAX_COMMANDS - 1 or index == len(commands) - 1:
            title = f"{plugin.name} ({len(commands)} commands):"

            embed = helpers.get_default_embed(
                title = title,
                description = display,
                timestamp = dt.datetime.now().astimezone(),
                author = ctx.author
            ).set_thumbnail(
                ctx.bot.get_me().avatar_url
            )
            plugins.append(embed)
            display = ""
    
    return plugins

def command_help_format(ctx: lightbulb.Context, command: lightbulb.Command) -> hikari.Embed:
    # Signature includes full command name.
    embed_title = command.signature
    embed_description = "*No help provided*"
    if command.description != "":
        embed_description = command.description + '\n'
    #if command.get_help(ctx) is not None and command.get_help(ctx) != "":
    #    embed_description += command.get_help(ctx)
    #command_signature = command.signature

    # Usage here.

    embed = helpers.get_default_embed(
        title = embed_title,
        description = embed_description,
        timestamp = dt.datetime.now().astimezone(),
        author = ctx.author
    )

    if isinstance(command, lightbulb.PrefixCommandGroup) or isinstance(command, lightbulb.PrefixSubGroup):
        field_value = ""
        # I swear this part looks so dumb just because Python refuses to easily sort the dictionary.
        subcommands_list = [command.subcommands[name] for name in command.subcommands]
        for subcommand in sorted(subcommands_list, key = lambda cmd: cmd.name):
            field_value += f"- `{subcommand.name}`: {subcommand.description}\n"
        
        if len(command.subcommands) > 0:
            embed.add_field(
                name = "**Subcommands:**",
                value = field_value,
                inline = False
            )
    
    return embed

class SmallHelp(lightbulb.DefaultHelpCommand):
    async def send_bot_help(self, ctx: lightbulb.context.base.Context) -> None:
        main_page: hikari.Embed = helpers.get_default_embed(
            title = "Help",
            description = "",
            timestamp = dt.datetime.now().astimezone(),
            author = ctx.author
        )

        plugins = ctx.bot.plugins
        plugin_info: t.Dict[str, int] = {}
        for name in plugins:
            public_commands = filter_command_type(plugins[name].all_commands, __PREFIX_COMMAND_TYPES__, True)
            public_commands_len = len(public_commands)

            if public_commands_len != 0:
                embed_name = f"{plugins[name].d.emote} {name} ({public_commands_len} commands):"
                embed_description = "*No description provided*"
                if plugins[name].description is not None and plugins[name].description != "":
                    embed_description = plugins[name].description
                main_page.add_field(
                    name = embed_name,
                    value = embed_description,
                    inline = False
                )
                
                plugin_info[name] = public_commands_len
        
        menu_root = MenuComponent(main_page)
        for name in plugin_info:
            menu_root.add_list_options(plugins[name].d.emote, plugin_help_format(ctx, plugins[name]))
        menu = MenuInteractionWrapper(menu_root)
        await menu.run(ctx)
    
    async def send_plugin_help(self, ctx: lightbulb.Context, plugin: lightbulb.Plugin) -> None:
        embeds = []
        public_commands = filter_command_type(plugin.all_commands, __PREFIX_COMMAND_TYPES__, True)
        for command in sorted(public_commands, key = lambda cmd: cmd.name):
            page = command_help_format(ctx, command)
            embeds.append(page)
        
        page = ButtonPages(embeds)
        await page.run(ctx)
    
    async def send_command_help(self, ctx: lightbulb.Context, command: lightbulb.Command) -> None:
        await ctx.respond(command_help_format(ctx, command))
    async def send_group_help(self, ctx: lightbulb.Context, group: t.Union[lightbulb.commands.PrefixCommandGroup, lightbulb.commands.PrefixSubGroup]) -> None:
        await ctx.respond(command_help_format(ctx, group))

def load(bot):
    bot.d.old_help_command = bot.help_command
    bot.help_command = SmallHelp(bot)
def unload(bot):
    bot.help_command = bot.d.old_help_command
    del bot.d.old_help_command
