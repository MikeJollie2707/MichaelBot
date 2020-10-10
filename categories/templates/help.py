import discord
from discord.ext import commands

import datetime

from categories.templates.navigate import Pages
from categories.templates.menu import Menu
from categories.utilities.method_cog import Facility

def cog_help_format(ctx, cog):
    # TODO: Might need to format this a bit more pretty.

    display = ""
    for command in cog.get_commands():
        if command.hidden != True:
            display += f"`{command.name}`: {command.short_doc}\n-----------------------------------------\n"
    
    title_str = f"{cog.qualified_name} ({len(cog.get_commands())} commands): "
    
    content = Facility.get_default_embed(
        title = title_str,
        description = display,
        color = discord.Color.green(),
        timestamp = datetime.datetime.utcnow(),
        author = ctx.author
    )

    return content

def command_help_format(ctx, command):
    content = Facility.get_default_embed(
        title = command.name,
        description = command.help.format(prefix = ctx.prefix, command_name = command.name),
        color = discord.Color.green(),
        timestamp = datetime.datetime.utcnow(),
        author = ctx.author
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
                       
                       You need: None.
                       I need: send_messages.'''
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

        cog = self.context.bot.cogs # List of categories
        for category in cog:
            num_of_commands = 0
            context = ""
            commands = cog[category].get_commands() # List of commands in one category
            for command in commands:
                if not command.hidden:
                    context += f"`{command.name}` " # Highlight the commands
                    num_of_commands += 1
            if num_of_commands != 0:
                embed_name = "%s (%s commands): " % (category, str(num_of_commands))
                content.add_field(
                    name = embed_name, 
                    value = context, 
                    inline = False
                )

        await self.context.send(embed = content)

    async def send_cog_help(self, cog):
        content = cog_help_format(self.context, cog)
        await self.context.channel.send(embed = content)
        
    async def send_command_help(self, command):
        content = command_help_format(self.context, command)
        await self.context.send(embed = content)

class SmallHelp():
    def __init__(self, ctx):
        self.ctx = ctx

    async def send_bot_help(self):
        main_page = discord.Embed(color = discord.Color.green())
        note = '''
        Use `%shelp [CommandOrCategory]` to get more info on a command/category.
        If you need help, join the [support server](https://discordapp.com/jeMeyNw).
        ''' % self.ctx.prefix
        main_page.add_field(name = "Note:", value = note)

        cog = self.ctx.bot.cogs
        cog_info = {}
        for category in cog:
            num_of_commands = 0
            commands = cog[category].get_commands()
            for command in commands:
                if not command.hidden:
                    num_of_commands += 1
            if num_of_commands != 0:
                embed_name = "%s %s (%s commands): " % (cog[category].emoji, category, str(num_of_commands))
                main_page.add_field(name = embed_name, value = cog[category].description, inline = False)
            
            cog_info[category] = num_of_commands
        menu = Menu(main_page, '✖️', '🔼')
        for category in cog:
            if cog_info[category] > 0:
                menu.add_page(cog[category].emoji, cog_help_format(self.ctx, cog[category]))
        
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
        #if command.hidden:
        #    return
        await self.ctx.send(embed = command_help_format(self.ctx, command))

        