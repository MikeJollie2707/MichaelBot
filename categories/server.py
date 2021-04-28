import discord
from discord.ext import commands

import datetime

from discord.ext.commands.help import Paginator

import utilities.facility as Facility
import utilities.db as DB
from templates.navigate import Pages
from utilities.checks import has_database

class Server(commands.Cog, name = "Settings", command_attrs = {"cooldown_after_parsing": True}):
    '''Commands related to the bot setting in the server.'''
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '🛠'
    
    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()
        
        return True
    
    @commands.command(aliases = ["log-enable"])
    @commands.check(has_database)
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.bot_has_guild_permissions(view_audit_log = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def log_enable(self, ctx):
        '''
        Enable logging in your server.

        **Aliases:** `log-enable`
        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `View Audit Log`, `Read Message History`, `Send Messages`.
        '''

        config = await Facility.get_config(self.bot, ctx.guild.id)
        if config["enable_log"] == True:
            await ctx.reply("Logging is already enabled for this server.", mention_author = False)
        else:
            config["enable_log"] = True
            await Facility.save_config(self.bot, config)
            await ctx.reply("Logging is enabled for this server. You should setup a log channel.", mention_author = False)

    @commands.command(aliases = ["log-setup"])
    @commands.check(has_database)
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.bot_has_guild_permissions(view_audit_log = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def log_setup(self, ctx, log : discord.TextChannel = None):
        '''
        Set or view a log channel in your server.
        If this command is invoked but you haven't enabled logging, it'll automatically be enabled.

        **Aliases:** `log-setup`
        **Usage:** <prefix>**{command_name}** [text channel mention/ID/name]
        **Example 1:** {prefix}{command_name} 649111117204815883
        **Example 2:** {prefix}{command_name} a-random-log-channel
        **Example 3:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `View Audit Log`, `Read Message History`, `Send Messages`.
        '''

        config = await Facility.get_config(self.bot, ctx.guild.id)
        if log is None:
            await ctx.reply("Current logging channel ID: `%d`" % config["log_channel"], mention_author = False)
        else:
            config["enable_log"] = True
            config["log_channel"] = log.id

            embed = Facility.get_default_embed(
                title = "Logging Enabled", 
                description = "This is now a logging channel.", 
                color = discord.Color.green(),
                timestamp = datetime.datetime.utcnow()
            ).set_author(
                name = self.bot.user.name, 
                icon_url = self.bot.user.avatar_url
            ).set_footer(
                text = "Set by %s" % ctx.author.name,
                icon_url = ctx.author.avatar_url
            )

            try:
                await log.send(embed = embed)
            except discord.Forbidden:
                await ctx.reply(f"I can't send message to {log.mention}!", mention_author = False)
            else:
                await Facility.save_config(self.bot, config)
                await ctx.reply("Channel %s is now a logging channel." % log.mention, mention_author = False)
    
    @commands.command(aliases = ["log-disable"])
    @commands.check(has_database)
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(read_message_history = True,send_messages = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def log_disable(self, ctx):
        '''
        Disable logging in your server.
        This doesn't remove the logging channel.


        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `Read Message History`, `Send Messages`.
        '''

        config = await Facility.get_config(self.bot, ctx.guild.id)
        config["enable_log"] = False
        await Facility.save_config(self.bot, config)

        await ctx.reply("Logging is disabled for this server.", mention_author = False)

    @commands.command(aliases = ["welcome-enable"])
    @commands.check(has_database)
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def welcome_enable(self, ctx):
        '''
        Enable welcoming new members in your server.
        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `Read Message History`, `Send Messages`.
        '''

        config = await Facility.get_config(self.bot, ctx.guild.id)
        if config["enable_welcome"]:
            await ctx.reply("Welcoming system is already enabled for this server.", mention_author = False)
        else:
            config["enable_welcome"] = True
            await Facility.save_config(self.bot, config)
            await ctx.reply("Welcoming is enabled for this server. You should setup the welcome channel and message.", mention_author = False)
    
    @commands.command(aliases = ["welcome-setup"])
    @commands.check(has_database)
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def welcome_setup(self, ctx, welcome_chan : discord.TextChannel = None, *, welcome_text : str = ""):
        '''
        Set or view the welcome channel and message in your server.
        - If this command is invoked but you haven't enabled welcoming, it'll automatically be enabled.
        - If you don't provide a welcome text, it is default to `Hello [user.mention]! Welcome to **[guild.name]**! You're the [guild.count]th member in this server! Enjoy the fun!!! :tada:`.

        **Aliases:** `welcome-setup`
        **Usage:** <prefix>**{command_name}** [text channel mention/ID/name] [welcome text]
        **Argument:** `[user.mention]`, `[user.name]`, `[guild.name]`, `[guild.count]`
        **Example 1:** {prefix}{command_name} 644336991135072261 Welcome [user.mention] to [guild.name]!
        **Example 2:** {prefix}{command_name} a-random-welcome-channel You are the [guild.count]th member!
        **Example 3:** {prefix}{command_name} #another-random-channel
        **Example 4:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `Read Message History`, `Send Messages`.
        '''

        config = await Facility.get_config(self.bot, ctx.guild.id)
        if welcome_chan is None:
            await ctx.reply(f"Current welcome channel ID: `{config['welcome_channel']}`\nCurrent welcome message: ", 
                embed = discord.Embed(description = config["welcome_text"]),
                mention_author = False
            )
        else:
            config["enable_welcome"] = True

            if welcome_text == "":
                welcome_text = "Hello [user.mention]! Welcome to **[guild.name]**! You're the [guild.count]th member in this server! Enjoy the fun!!! :tada:"
            config["welcome_text"] = welcome_text

            try:
                await welcome_chan.send("Your welcome message is: %s" % welcome_text)
            except discord.Forbidden:
                await ctx.reply(f"I can't send message to {welcome_chan.mention}!", mention_author = False)
            else:
                config["welcome_channel"] = welcome_chan.id
                await ctx.reply("Channel %s is now a welcome channel." % welcome_chan.mention, mention_author = False)

                await Facility.save_config(self.bot, config)
    @commands.Cog.listener("on_member_join")
    async def welcome_new_member(self, member):
        if self.bot.pool is not None:
            config = await Facility.get_config(self.bot, member.guild.id)
            if config["ERROR"] == 0 and config["enable_welcome"] == 1 and config["welcome_channel"] != 0:
                welcome_channel = self.bot.get_channel(config["welcome_channel"])
                welcome_text = config["welcome_text"]

                # We don't use f-string here because it'll raise attribute errors which are annoying.
                welcome_text = welcome_text.replace("[user.mention]", "<@%d>" % member.id)
                welcome_text = welcome_text.replace("[user.name]", str(member))
                welcome_text = welcome_text.replace("[guild.name]", str(member.guild))
                welcome_text = welcome_text.replace("[guild.count]", str(len(member.guild.members)))

                await welcome_channel.send(welcome_text)

                if not member.bot:
                    async with self.bot.pool.acquire() as conn:
                        async with conn.transaction():
                            user_existed = await DB.User.find_user(conn, member.id)
                            member_existed = await DB.Member.find_member(conn, member.id, member.guild.id)
                            if user_existed is None:
                                await DB.User.insert_user(conn, member)
                                await DB.Member.insert_member(conn, member)
                            elif member_existed is None:
                                await DB.Member.insert_member(conn, member)
            else:
                return

    @commands.command(aliases = ["welcome-disable"])
    @commands.check(has_database)
    @commands.has_guild_permissions(manage_guild = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
    async def welcome_disable(self, ctx):
        '''
        Disable welcoming in your server.
        This doesn't remove the welcome channel.

        **Aliases:** `welcome-disable`
        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        You need: `Manage Server`.
        I need: `Read Message History`, `Send Messages`.
        '''
        
        config = await Facility.get_config(self.bot, ctx.guild.id)
        config["enable_welcome"] = 0
        await Facility.save_config(self.bot, config)

        await ctx.reply("Welcoming is disabled for this server.", mention_author = False)
        
    @commands.group(aliases = ['giverole', 'assignrole'], invoke_without_command = True)
    @commands.check(has_database)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.cooldown(rate = 1, per = 2.0, type = commands.BucketType.guild)
    async def roleme(self, ctx, *, role : discord.Role = None):
        '''
        Display the self-assignable roles or self-assign a role.

        **Aliases:** `giverole`
        **Usage:** <prefix>**{command_name}** {command_name}
        **Example 1:** {prefix}{command_name}
        **Example 2:** {prefix}{command_name} Weeb

        **You need:** None.
        **I need:** `Manage Roles`.
        '''
        
        async with self.bot.pool.acquire() as conn:
            if role is not None:
                existed = await DB.Guild.Role.get_role(conn, ctx.guild.id, role.id)
                if existed is None:
                    await ctx.reply(f"This server did not add **{role}** into self-assign roles.", mention_author = False)
                    return
                # Toggle
                if role in ctx.author.roles:
                    await ctx.author.remove_roles(role, reason = "MichaelBot's self-assign role.")
                    await ctx.reply(f"Removed **{role}** from you.")
                else:
                    await ctx.author.add_roles(role, reason = "MichaelBot's freerole.")
                    await ctx.reply(f"You received **{role}**.")
            else:
                roles = await DB.Guild.Role.get_roles(conn, ctx.guild.id)
                if roles == [None] * len(roles):
                    await ctx.reply("*No self-assign roles available.*", mention_author = False)
                    return
                
                MAX_ENTRY = 4
                count = 0
                pages = Pages()
                embed = None
                for role in roles:
                    if embed is None:
                        embed = discord.Embed(
                            title = "**Self-Assignable Roles**",
                            color = discord.Color.green()
                        )
                    r_role = ctx.guild.get_role(role["role_id"])
                    # This means the role is most likely deleted
                    # So we do a manual delete here, in case the event fails to do it due to disconnect.
                    if r_role is None:
                        async with conn.transaction():
                            await DB.Guild.Role.remove_role(conn, r_role.guild.id, r_role.id)
                    embed.add_field(
                        name = r_role,
                        value = role["description"],
                        inline = False
                    )
                    count += 1
                    if count == MAX_ENTRY:
                        pages.add_page(embed)
                        count = 0
                        embed = None
                
                if embed is not None:
                    pages.add_page(embed)

                await pages.event(ctx, interupt = False)

    @roleme.command()
    @commands.check(has_database)
    @commands.has_guild_permissions(manage_roles = True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.cooldown(rate = 1, per = 2.0, type = commands.BucketType.guild)
    async def add(self, ctx, role : discord.Role, *, description : str = None):
        '''
        Add a role for self-assigning.
        This role cannot be the default `everyone` role, nor roles that are above the bot.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 2 seconds per 1 use (guild)
        **Example 1:** {prefix}{command_name} Weeb
        **Example 2:** {prefix}{command_name} "Weeb 2" Indicate you're a weeb. Lol.

        **You need:** `Manage Roles`.
        **I need:** `Manage Roles`.
        '''

        async with self.bot.pool.acquire() as conn:
            existed = await DB.Guild.Role.get_role(conn, ctx.guild.id, role.id)
            if existed is not None:
                await ctx.reply("This role is already added as self-assign roles.", mention_author = False)
                return
            if role == ctx.guild.default_role:
                await ctx.reply("You cannot add `everyone` role as a self-assign role.", mention_author = False)
                return
            if role >= ctx.guild.me.top_role:
                await ctx.reply("I cannot add this role because the role is higher than me.", mention_author = False)
                return
            async with conn.transaction():
                await DB.Guild.Role.add_role(conn, ctx.guild.id, role.id, description)
                await ctx.reply("Role added to self-assign roles.", mention_author = False)

    # I don't consume rest to make it consistent with roleme add.
    @roleme.command()
    @commands.check(has_database)
    @commands.has_guild_permissions(manage_roles = True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.cooldown(rate = 1, per = 2.0, type = commands.BucketType.guild)
    async def remove(self, ctx, role : discord.Role):
        '''
        Remove a role from self-assigning.
        
        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 2 seconds per 1 use (guild)
        **Example 1:** {prefix}{command_name} Weeb
        **Example 2:** {prefix}{command_name} "Weeb 2"

        **You need:** `Manage Roles`.
        **I need:** `Manage Roles`.
        '''

        async with self.bot.pool.acquire() as conn:
            existed = await DB.Guild.Role.get_role(conn, ctx.guild.id, role.id)
            if existed is not None:
                async with conn.transaction():
                    await DB.Guild.Role.remove_role(conn, ctx.guild.id, role.id)
                    await ctx.reply("Role removed from self-assign roles.", mention_author = False)
            else:
                await ctx.reply("This role is not added as self-assign roles.", mention_author = False)

    @commands.Cog.listener("on_guild_role_delete")
    async def _update_self_role(self, role : discord.Role):
        if self.bot.pool is not None:
            async with self.bot.pool.acquire() as conn:
                existed = await DB.Guild.Role.get_role(conn, role.guild.id, role.id)
                if existed is not None:
                    async with conn.transaction():
                        await DB.Guild.Role.remove_role(conn, role.guild.id, role.id)
                

def setup(bot):
    bot.add_cog(Server(bot))
