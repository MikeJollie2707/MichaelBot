import discord
from discord.ext import commands, tasks

import datetime as dt
import textwrap

import utilities.facility as Facility
import utilities.db as DB
from utilities.checks import has_database
from utilities.converters import IntervalConverter

# For every tempmute, it is added into the db as an entry.
# We can't do 15 minutes, because, say a tempmute 5 minutes follow by another 15 minutes.
# Then the bot will locally wait 5 minutes and then remove the role, while the 15 minutes mute, which is saved on DB, is still pending.
# So we have to do to the minimum.
TEMPMUTE_CHECK_INTERVAL = 60 * 1

class Moderation(commands.Cog, command_attrs = {"cooldown_after_parsing" : True}):
    '''Commands related to moderate actions such as kick, ban, etc.'''
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '🔨'
        
        self.scan_tempmute.start()
    
    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()
        
        return True
    
    def cog_unload(self):
        self.scan_tempmute.cancel()
        return super().cog_unload()
    
    async def remove_mute(self, member : discord.Member, expire : dt.datetime.utcnow() = None):
        if expire is not None:
            await discord.utils.sleep_until(expire)
        
        async with self.bot.pool.acquire() as conn:
            async with conn.transaction():
                await DB.Member.TempMute.remove_entry(conn, member.id, member.guild.id)
        
        for role in member.roles:
            if role.name == "Muted":
                await member.remove_roles(role, reason = f"Timed mute expired.")

    @commands.command()
    @commands.has_guild_permissions(ban_members = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.bot_has_guild_permissions(ban_members = True)
    @commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
    async def ban(self, ctx, user : discord.Member, *, reason = None):
        '''
        Ban a member __in__ the server.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 2 uses (guild).
        **Example 1:** {prefix}{command_name} MikeJollie Spam too much
        **Example 2:** {prefix}{command_name} @MikeJollie Stop spamming!
        
        **You need:** `Ban Members`.
        **I need:** `Ban Members`, `Read Message History`, `Send Messages`.
        '''

        guild = ctx.guild
        victim_name = str(user)
        if reason == None:
            reason = "`None provided`"
        try:
            await guild.ban(user, reason = reason)
        except discord.Forbidden:
            await ctx.reply("I cannot ban someone that's higher than me!", mention_author = False)
        else:
            embed = Facility.get_default_embed(
                title = "Member Banned",
                description = '''
                        **User `%s` has been banned from this server.** :hammer:
                        **Reason:** %s
                ''' % (victim_name, reason),
                color = 0x000000,
                timestamp = dt.datetime.utcnow()
            ).set_footer(
                text = f"Banned by {ctx.author.name}",
                icon_url = ctx.author.avatar_url
            )

            await ctx.reply(embed = embed, mention_author = False)
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.reply("I cannot ban someone that's not in the guild normally. I need the power of `%shackban` to ban." % ctx.prefix, mention_author = False)

    @commands.command()
    @commands.has_guild_permissions(ban_members = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.bot_has_guild_permissions(ban_members = True)
    @commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
    async def hackban(self, ctx, user_id : int, *, reason = None):
        '''
        Ban a user __outside__ the server.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 2 uses (guild).
        **Example:** {prefix}{command_name} 472832990012243969 Develope a bot

        **You need:** `Ban Members`.
        **I need:** `Ban Members`, `Read Message History`, `Send Messages`.
        '''

        guild = ctx.guild
        if reason == None:
            reason = "`None provided`"
        
        try:
            await guild.ban(discord.Object(id = user_id), reason = reason)
        except discord.HTTPException:
            await ctx.reply("I can't ban this person. The most common one would be your id is wrong.", mention_author = False)
            return
        else:
            embed = Facility.get_default_embed(
                title = "User Banned",
                description = '''
                        **User `%d` has been banned from this server.** :hammer:
                        **Reason:** %s
                ''' % (user_id, reason),
                color = 0x000000,
                timestamp = dt.datetime.utcnow()
            ).set_footer(
                text = f"Banned by {ctx.author.name}",
                icon_url = ctx.author.avatar_url
            )

            await ctx.reply(embed = embed, mention_author = False)

    @commands.command()
    @commands.has_guild_permissions(kick_members = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.bot_has_guild_permissions(kick_members = True)
    @commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
    async def kick(self, ctx, member : discord.Member, *, reason = None):
        '''
        Kick a member.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 2 uses (guild).
        **Example 1:** {prefix}{command_name} MikeJollie Dumb
        **Example 2:** {prefix}{command_name} <@472832990012243969> Still dumb
        **Example 3:** {prefix}{command_name} 472832990012243969

        **You need:** `Kick Members`.
        **I need:** `Kick Members`, `Read Message History`, `Send Messages`.
        '''

        guild = ctx.guild
        victim_name = str(member)
        if reason == None:
            reason = "`None provided`"

        try:
            await guild.kick(member, reason = reason)
        except discord.Forbidden:
            await ctx.reply("I cannot kick someone that's higher than me!", mention_author = False)
        else:
            embed = Facility.get_default_embed(
                title = "Member Kicked",
                description = '''
                        **User `%s` has been kicked out from this server.**
                        **Reason:** %s
                ''' % (victim_name, reason),
                color = 0x000000,
                timestamp = dt.datetime.utcnow()
            ).set_footer(
                text = f"Kicked by {ctx.author.name}",
                icon_url = ctx.author.avatar_url
            )
            
            await ctx.reply(embed = embed, mention_author = False)
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.reply("I cannot kick someone that's not in the guild! If you want someone not to join your guild, use `%shackban`." % ctx.prefix, mention_author = False)
    
    @commands.command()
    @commands.check(has_database)
    @commands.has_permissions(kick_members = True)
    @commands.bot_has_permissions(manage_permissions = True, read_message_history = True, send_messages = True)
    @commands.bot_has_guild_permissions(manage_roles = True)
    @commands.cooldown(1, 5.0, commands.BucketType.guild)
    async def mute(self, ctx, member : discord.Member, *, reason = None):
        '''
        Mute a member.
        Note: this command will find a role named `Muted` in the guild and use it as the mute role.
        If not existed, one will be created which will deny `Send Messages`, `Send TTS Messages`, `Add Reactions` and `Speak` by default.
        This is extremely spammy, especially if there are many channels.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 1 use (guild).
        **Example:** {prefix}{command_name} MikeJollie stop boasting about lolis.

        **You need:** `Kick Members`.
        **I need:** `Manage Roles`, `Manage Permissions`, `Read Message History`, `Send Messages`.
        '''
        
        if reason is None:
            reason = "Not provided."
        guild = ctx.guild
        mute_role = discord.utils.find(lambda role: role.name == "Muted", guild.roles)
        if mute_role is None:
            mute_role = await guild.create_role(
                name = "Muted",
                permissions = discord.Permissions(
                    send_messages = False,
                    send_tts_messages = False,
                    add_reactions = False,
                    speak = False
                ),
                color = discord.Color.red(),
                reason = f"Created Muted role for {self.bot.user.name} to use."
            )

            failed_channels = []
            for channel in guild.channels:
                try:
                    if channel.type == discord.ChannelType.category:
                        await channel.set_permissions(mute_role,
                            send_messages = False,
                            send_tts_messages = False,
                            add_reactions = False,
                            speak = False
                        )
                    elif channel.type == discord.ChannelType.text:
                        await channel.set_permissions(mute_role,
                            send_messages = False,
                            send_tts_messages = False,
                            add_reactions = False
                        )
                    elif channel.type == discord.ChannelType.voice:
                        await channel.set_permissions(mute_role,
                            speak = False
                        )
                except discord.Forbidden:
                    failed_channels.append(f"`{channel.name}`")

            if len(failed_channels) != 0:
                await ctx.send("Failed channels: %s" % Facility.striplist(failed_channels))

        await member.add_roles(mute_role, reason = f"{member} is muted by {ctx.author} for {reason}.")    
        embed = Facility.get_default_embed(
            title = "Member Muted",
            description = f"{member} is muted by {ctx.author} because {reason}.",
            color = 0x000000,
            timestamp = dt.datetime.utcnow(),
            author = ctx.author
        )    
        await ctx.reply(embed = embed, mention_author = False)

        # Perform DB actions here

    @commands.command()
    @commands.check(has_database)
    @commands.has_permissions(kick_members = True)
    @commands.bot_has_permissions(manage_permissions = True, read_message_history = True, send_messages = True)
    @commands.bot_has_guild_permissions(manage_roles = True)
    async def tempmute(self, ctx, member : discord.Member, duration : IntervalConverter, *, reason = None):
        '''
        Temporarily muted a member. The member will be unmuted after the interval provided.
        Note: Similar to `unmute`, the unmute behavior is naive: It'll remove a single `Muted` role from the member.

        The `duration` must be in between 1 minute and 30 days.

        **Usage:** {usage}
        **Example 1:** {prefix}{command_name} MikeJollie 1d Chill
        **Example 2:** {prefix}{command_name} "Hamza Khattab" 1m believed the earth is flat

        **You need:** `Kick Members`.
        **I need:** `Manage Roles`, `Manage Permissions`, `Read Message History`, `Send Messages`.
        '''

        end = dt.datetime.utcnow() + duration
        if duration.total_seconds() < 60:
            await ctx.reply("There's no meaning for such a short mute.", mention_author = False)
            return
        elif duration.total_seconds() > 2592000:
            await ctx.reply("Too long mute.", mention_author = False)
            return
        else:
            async with self.bot.pool.acquire() as conn:
                entry_existed = await DB.Member.TempMute.get_entry(conn, member.id, member.guild.id)
                # This is unfortunate, but I can't really think of a way to 'overwrite' the duration once the `remove_mute()` is fired.
                # So to avoid such cases, we're doing this.
                if entry_existed is not None:
                    import humanize
                    await ctx.reply("This member is already on a timed mute. Wait %s for it to expire." % humanize.precisedelta(entry_existed["expire"] - (end - duration), format = '%0.0f'), mention_author = False)
                    return
                await DB.Member.TempMute.add_entry(conn, member.id, member.guild.id, end)
                await self.mute(ctx, member, reason = reason)
    @tasks.loop(seconds = TEMPMUTE_CHECK_INTERVAL)
    async def scan_tempmute(self):
        current = dt.datetime.utcnow()
        future = dt.datetime.utcnow() + dt.timedelta(seconds = TEMPMUTE_CHECK_INTERVAL)
        async with self.bot.pool.acquire() as conn:
            passed = await DB.Member.TempMute.get_missed_mute(conn, current)
            upcoming = await DB.Member.TempMute.get_mutes(conn, current, future)

        for missed_mute in passed:
            guild = self.bot.get_guild(missed_mute["guild_id"])
            member = guild.get_member(missed_mute["user_id"])
            self.bot.loop.create_task(self.remove_mute(member))
        
        for upcoming_mute in upcoming:
            guild = self.bot.get_guild(upcoming_mute["guild_id"])
            user = guild.get_member(upcoming_mute["user_id"])
            self.bot.loop.create_task(self.remove_mute(user, upcoming_mute["expire"]))
    @scan_tempmute.before_loop
    async def before_tempmute(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @commands.has_permissions(kick_members = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.bot_has_guild_permissions(manage_roles = True)
    @commands.cooldown(1, 5.0, commands.BucketType.guild)
    async def unmute(self, ctx, member : discord.Member, *, reason = None):
        '''
        Unmute a member.
        This will just simply remove a role called `Muted` from the member, thus it is *not* recommended to use with another bot.

        **Usage:** {usage}
        **Example:** {prefix}{command_name} MikeJollie you're good now

        **You need:** `Kick Members`.
        **I need:** `Manage Roles`, `Read Message History`, `Send Messages`.
        '''

        for role in member.roles:
            # Simple implementation for now.
            if role.name == "Muted":
                await member.remove_roles(role, reason = f"{member} is unmuted by {ctx.author} because {reason}.")
                embed = Facility.get_default_embed(
                    title = "Member Muted",
                    description = f"{member} is unmuted by {ctx.author} because {reason}.",
                    color = 0x000000,
                    timestamp = dt.datetime.utcnow(),
                    author = ctx.author
                )    
                await ctx.reply(embed = embed, mention_author = False)
                return
        
        await ctx.reply(f"{member} is not previously muted.", mention_author = False)

    @commands.command()
    @commands.has_guild_permissions(ban_members = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.bot_has_guild_permissions(ban_members = True)
    @commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
    async def unban(self, ctx, id : int, *, reason = None):
        '''
        Unban a user.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 2 uses (guild).
        **Example:** {prefix}{command_name} 472832990012243969 You've redeemed your goodness.

        **You need:** `Ban Members`.
        **I need:** `Ban Members`, `Read Message History`, `Send Messages`.
        '''

        guild = ctx.guild

        try:
            await guild.unban(discord.Object(id = id), reason = reason)
        except discord.HTTPException:
            await ctx.reply("The ban hammer is too heavy! Make sure the id is correct, and that the user is already banned.", mention_author = False)
            return
        else:
            embed = Facility.get_default_embed(
                title = "Member Unbanned",
                description = '''
                        **User `%d` has been unbanned from this server.** :hammer:
                        **Reason:** %s
                ''' % (id, reason),
                color = 0x000000,
                timestamp = dt.datetime.utcnow()
            ).set_footer(
                text = f"Unbanned by {ctx.author.name}",
                icon_url = ctx.author.avatar_url
            )
            
            await ctx.reply(embed = embed, mention_author = False)


def setup(bot):
    bot.add_cog(Moderation(bot))