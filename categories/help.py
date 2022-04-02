import lightbulb
import hikari

import datetime as dt
import typing as t
from textwrap import dedent

from utilities.navigator import MenuComponent, MenuInteractionWrapper, ButtonPages
import utilities.helpers as helpers

__PREFIX_COMMAND_TYPES__ = (
    lightbulb.PrefixCommand, 
    lightbulb.PrefixCommandGroup, 
    lightbulb.PrefixSubGroup,
    lightbulb.PrefixSubCommand,
)
__SLASH_COMMAND_TYPES__ = (
    lightbulb.SlashCommand,
    lightbulb.SlashCommandGroup,
    lightbulb.SlashSubGroup,
    lightbulb.SlashSubCommand,
)

def get_slash_command(bot: lightbulb.BotApp, name: str) -> t.Optional[lightbulb.SlashCommand]:
    '''
    Get the slash command with the given name, or `None` if none was found.

    Unlike the default behavior in `lightbulb.BotApp`, this also searches for subcommands.
    '''
    # Reference: https://hikari-lightbulb.readthedocs.io/en/latest/_modules/lightbulb/app.html#BotApp.get_prefix_command
    
    parts = name.split()
    if len(parts) == 1:
        return bot._slash_commands.get(name)

    maybe_group = bot._slash_commands.get(parts.pop(0))
    if not isinstance(maybe_group, lightbulb.SlashCommandGroup):
        return None

    this: t.Optional[
        t.Union[
            lightbulb.SlashCommandGroup, lightbulb.SlashSubGroup, lightbulb.SlashSubCommand
        ]
    ] = maybe_group
    for part in parts:
        if this is None or isinstance(this, lightbulb.SlashSubCommand):
            return None
        this = this.get_subcommand(part)

    return this

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

    types = __PREFIX_COMMAND_TYPES__
    if isinstance(ctx, lightbulb.SlashContext):
        types = __SLASH_COMMAND_TYPES__
    
    commands: t.List[lightbulb.Command] = filter_command_type(plugin.all_commands, types, True)
    commands.sort(key = lambda command: command.name)
    for index, command in enumerate(commands):
        # Signature includes command name.
        command_title = command.signature.replace('=', ' = ')
        
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
    embed_title = command.signature.replace('=', ' = ')
    embed_description = "*No help provided*"
    if command.description != "":
        embed_description = command.description + '\n'

    embed = helpers.get_default_embed(
        title = embed_title,
        description = embed_description,
        timestamp = dt.datetime.now().astimezone(),
        author = ctx.author
    )
    if command.get_help(ctx) != "":
        embed.add_field(
            name = "Note",
            value = dedent(command.get_help(ctx))
        )

    command_type = []
    p_cmd = ctx.bot.get_prefix_command(command.qualname)
    s_cmd = get_slash_command(ctx.bot, command.qualname)
    m_cmd = ctx.bot.get_message_command(command.qualname)
    u_cmd = ctx.bot.get_user_command(command.qualname)

    if p_cmd is not None:
        command_type.append("`Prefix Command`")
    if s_cmd is not None and not isinstance(s_cmd, (lightbulb.SlashCommandGroup, lightbulb.SlashSubGroup)):
        command_type.append("`Slash Command`")
    if m_cmd is not None:
        command_type.append("`Message Command`")
    if u_cmd is not None:
        command_type.append("`User Command`")
    
    embed.add_field(
        name = "Type",
        value = ' '.join(command_type)
    )

    if len(command.options) > 0:
        option_field = ""
        for option_name in command.options:
            option_field += f"- `{option_name}`: {command.options[option_name].description}\n"
        embed.add_field(
            name = "Parameters",
            value = option_field
        )
    if len(command.aliases) > 0 and isinstance(command, __PREFIX_COMMAND_TYPES__):
        embed.add_field(
            name = "Aliases (Prefix Command only)",
            value = "- " + ', '.join(f"`{alias}`" for alias in command.aliases)
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

class MenuLikeHelp(lightbulb.DefaultHelpCommand):
    async def send_help(self, ctx: lightbulb.Context, obj: t.Optional[str]) -> None:
        '''
        The main logic for the help command.
        '''
        # Reference: https://github.com/tandemdude/hikari-lightbulb/blob/development/lightbulb/help_command.py#L100
        if obj is None:
            await self.send_bot_help(ctx)
            return
        
        # Prioritize searching command based on context.
        if isinstance(ctx, lightbulb.PrefixContext):
            cmd = self.bot.get_prefix_command(obj)
            if cmd is not None:
                if isinstance(cmd, (lightbulb.PrefixCommandGroup, lightbulb.PrefixSubGroup)):
                    return await self.send_group_help(ctx, cmd)
                else:
                    return await self.send_command_help(ctx, cmd)
        if isinstance(ctx, lightbulb.SlashContext):
            #cmd = self.bot.get_slash_command(obj)
            cmd = get_slash_command(self.bot, obj)
            if cmd is not None:
                if isinstance(cmd, (lightbulb.SlashCommandGroup, lightbulb.SlashSubGroup)):
                    return await self.send_group_help(ctx, cmd)
                else:
                    return await self.send_command_help(ctx, cmd)
        
        # We don't have user/message commands yet.

        await super().send_help(ctx, obj)

    async def send_bot_help(self, ctx: lightbulb.Context) -> None:
        '''
        Send a generic help message.
        '''

        if isinstance(ctx, lightbulb.PrefixCommand):
            await ctx.event.message.delete()

        main_page = helpers.get_default_embed(
            title = "Help",
            description = "",
            timestamp = dt.datetime.now().astimezone(),
            author = ctx.author
        )

        plugins = ctx.bot.plugins
        plugin_info: t.Dict[str, int] = {}
        for plugin in plugins.values():
            public_commands = filter_command_type(plugin.all_commands, __PREFIX_COMMAND_TYPES__, True)
            public_commands_len = len(public_commands)

            if public_commands_len > 0:
                embed_name = f"{plugin.d.emote} {plugin.name} ({public_commands_len} commands)"
                embed_description = "*No description provided*"
                if not not plugin.description:
                    embed_description = plugin.description
                main_page.add_field(
                    name = embed_name,
                    value = embed_description,
                    inline = False
                )
                
                plugin_info[plugin.name] = public_commands_len
        
        menu_root = MenuComponent(main_page)
        for name in plugin_info:
            menu_root.add_list_options(plugins[name].d.emote, plugin_help_format(ctx, plugins[name]))
        
        await MenuInteractionWrapper(menu_root).run(ctx)
    
    async def send_plugin_help(self, ctx: lightbulb.Context, plugin: lightbulb.Plugin) -> None:
        '''
        Send a plugin help that contains all commands.
        '''
        
        embeds = []
        types = __PREFIX_COMMAND_TYPES__
        if isinstance(ctx, lightbulb.SlashContext):
            types = __SLASH_COMMAND_TYPES__
        
        public_commands = filter_command_type(plugin.all_commands, types, True)
        for command in sorted(public_commands, key = lambda cmd: cmd.name):
            page = command_help_format(ctx, command)
            if page is not None:
                embeds.append(page)
        
        await ButtonPages(embeds).run(ctx)
    
    async def send_command_help(self, ctx: lightbulb.Context, command: lightbulb.Command) -> None:
        '''
        Send a command help.
        '''
        await ctx.respond(embed = command_help_format(ctx, command))
    async def send_group_help(self, ctx: lightbulb.Context, group: t.Union[lightbulb.commands.PrefixCommandGroup, lightbulb.commands.PrefixSubGroup]) -> None:
        '''
        Send a group help.

        Internally, this does the same as `send_command_help()`.
        '''
        await ctx.respond(embed = command_help_format(ctx, group))

def load(bot):
    bot.d.old_help_command = bot.help_command
    bot.help_command = MenuLikeHelp(bot)
def unload(bot):
    bot.help_command = bot.d.old_help_command
    del bot.d.old_help_command
