import discord
from discord.ext import commands

import datetime

from categories.templates.navigate import Pages
from categories.templates.menu import Menu
from categories.utilities.method_cog import Facility

def cog_help_format(ctx, cog):
    display = ""
    for command in cog.get_commands():
        if command.hidden != True:
            command_title = command.name
            if command.signature != "":
                command_title += ' ' + command.signature.replace("__", '/').replace("_", ' ')
            
            display += f"`{command_title}`:\n"
            short_desc = command.short_doc
            if command.short_doc is None or command.short_doc == "":
                short_desc = "*No help provided*"
            
            display += '- ' + short_desc + '\n\n'
            #display += ctx.bot.__divider__
    
    title_str = f"{cog.qualified_name} ({len(cog.get_commands())} commands): "
    
    content = Facility.get_default_embed(
        title = title_str,
        description = display,
        color = discord.Color.green(),
        timestamp = datetime.datetime.utcnow(),
        author = ctx.author
    ).set_thumbnail(
        url = ctx.bot.user.avatar_url
    )

    #for command in cog.get_commands():
    #    if not command.hidden:
    #        content.add_field(
    #            name = f"{command.name} {command.signature}",
    #            value = command.short_doc,
    #            inline = False
    #        )

    return content

def command_help_format(ctx, command):
    # Gotta add the supercommand to the command.
    embed_title = command.full_parent_name + \
                  ' ' if command.full_parent_name != "" else '' + \
                  command.name
    

    command_signature = command.signature
    command_signature = command_signature.replace('__', '/').replace('_', ' ')

    content = Facility.get_default_embed(
        title = embed_title,
        description = "*No help provided*" if command.help is None else
            command.help.format(
                prefix = ctx.prefix,
                command_name = embed_title,
                command_signature = command_signature
            ),
        
        color = discord.Color.green(),
        timestamp = datetime.datetime.utcnow(),
        author = ctx.author
    )

    # Handle if it's a Group.
    # This is also the reason why group_help_format() doesn't exist.
    if isinstance(command, commands.Group):
        field_value = ""
        for subcommand in command.commands:
            field_value += f"`{subcommand.name}`: {subcommand.short_doc}\n"
        
        if len(command.commands) > 0:
            content.add_field(
                name = "**Subcommands:**",
                value = field_value,
                inline = False
            )

    return content

class BigHelp(commands.HelpCommand):
    def __init__(self):
        docstring = '''Show help about the bot, a command, or a category.
                       Note: command name and category name is case sensitive; Core is different from core.

                       **Usage:** <prefix>**{command_name}** [command/category]
                       **Example 1:** {prefix}{command_name}
                       **Example 2:** {prefix}{command_name} info
                       **Example 3:** {prefix}{command_name} Core
                       **Example 4:** {prefix}{command_name} changelog
                       
                       **You need:** None.
                       **I need:** `Send Messages`.'''
        super().__init__(command_attrs = {
            "help": docstring,
            "name": "help-all"
        })
    
    async def send_bot_help(self, mapping):
        note = '''
        `<argument>` is required, `[argument]` is optional (refer to `note` for more details).
        If you need additional help, join the [support server](https://discordapp.com/jeMeyNw).
        '''
        content = Facility.get_default_embed(
            title = "Help",
            description = note,
            color = discord.Color.green(),
            timestamp = datetime.datetime.utcnow(),
            author = self.context.author
        )

        # List of categories.
        cog = self.context.bot.cogs
        for category in cog:
            num_of_commands = 0
            display_str = ""
            commands = cog[category].get_commands() # List of commands in one category

            actual_commands = [f"`{command.name}`" for command in commands if not command.hidden]
            display_str += ' '.join(actual_commands)
            num_of_commands = len(actual_commands)

            if num_of_commands != 0:
                field_name = "%s (%d commands): " % (category, num_of_commands)
                content.add_field(
                    name = field_name, 
                    value = display_str, 
                    inline = False
                )

        await self.context.send(embed = content)

    async def send_cog_help(self, cog):
        content = cog_help_format(self.context, cog)
        await self.context.send(embed = content)
    
    async def send_group_help(self, group):
        content = command_help_format(self.context, group)
        await self.context.send(embed = content)

    async def send_command_help(self, command):
        content = command_help_format(self.context, command)
        await self.context.send(embed = content)

class SmallHelp():
    def __init__(self, ctx):
        self.ctx = ctx

    async def send_bot_help(self):
        note = '''
        Use `%shelp [CommandOrCategory]` to get more info on a command/category.
        If you need help, join the [support server](https://discordapp.com/jeMeyNw).
        ''' % self.ctx.prefix

        main_page = Facility.get_default_embed(
            title = "Help",
            description = note,
            timestamp = datetime.datetime.utcnow(),
            author = self.ctx.author
        )

        #main_page.add_field(name = "Note:", value = note)

        cogs = self.ctx.bot.cogs
        # dict(category_name, category_actual_size)
        cog_info = {}
        for category in cogs:
            num_of_commands = 0
            commands = cogs[category].get_commands()

            actual_commands = [f"`{command.name}`" for command in commands if not command.hidden]
            num_of_commands = len(actual_commands)
            
            if num_of_commands != 0:
                embed_name = "%s %s (%d commands): " % (cogs[category].emoji, category, num_of_commands)
                main_page.add_field(
                    name = embed_name, 
                    value = cogs[category].description if cogs[category].description is not None else "*No description provided*", 
                    inline = False
                )
            
            cog_info[category] = num_of_commands
        
        menu = Menu(main_page, '✖️', '🔼')
        for category in cogs:
            if cog_info[category] > 0:
                menu.add_page(cogs[category].emoji, cog_help_format(self.ctx, cogs[category]))
        
        await menu.event(self.ctx, interupt = False)
    
    async def send_cog_help(self, cog):
        paginate = Pages()
        for command in cog.get_commands():
            if command.hidden:
                continue

            page = command_help_format(self.ctx, command)
            paginate.add_page(page)
        
        await paginate.event(self.ctx, interupt = False)
    
    async def send_command_help(self, command):
        await self.ctx.send(embed = command_help_format(self.ctx, command))

        