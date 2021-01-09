import discord
from discord.ext import commands

from datetime import datetime
import textwrap

from categories.utilities.method_cog import Facility

class Moderation(commands.Cog, command_attrs = {"cooldown_after_parsing" : True}):
    '''Commands related to moderate actions such as kick, ban, etc.'''
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '🔨'
    
    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()
        
        return True

    @commands.command()
    @commands.has_guild_permissions(ban_members = True)
    @commands.bot_has_permissions(send_messages = True)
    @commands.bot_has_guild_permissions(ban_members = True)
    @commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
    async def ban(self, ctx, user : discord.Member, *, reason = None):
        '''
        Ban a member __in__ the server.

        **Usage:** <prefix>**{command_name}** <name/ID/nickname/mention> [reason]
        **Cooldown:** 5 seconds per 2 uses (guild).
        **Example 1:** {prefix}{command_name} MikeJollie Spam too much
        **Example 2:** {prefix}{command_name} @MikeJollie Stop spamming!
        
        **You need:** `Ban Members`.
        **I need:** `Ban Members`, `Send Messages`.
        '''

        guild = ctx.guild
        victim_name = str(user)
        if reason == None:
            reason = "`None provided`"
        try:
            await guild.ban(user, reason = reason)
        except discord.Forbidden:
            await ctx.send("I cannot ban someone that's higher than me!")
        else:
            embed = Facility.get_default_embed(
                title = "Member Banned",
                description = '''
                        **User `%s` has been banned from this server.** :hammer:
                        **Reason:** %s
                ''' % (victim_name, reason),
                color = 0x000000,
                timestamp = datetime.utcnow()
            ).set_footer(
                text = f"Banned by {ctx.author.name}",
                icon_url = ctx.author.avatar_url
            )

            await ctx.reply(embed = embed, mention_author = False)
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("I cannot ban someone that's not in the guild normally. I need the power of `%shackban` to ban." % ctx.prefix)

    @commands.command()
    @commands.has_guild_permissions(ban_members = True)
    @commands.bot_has_permissions(send_messages = True)
    @commands.bot_has_guild_permissions(ban_members = True)
    @commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
    async def hackban(self, ctx, user_id : int, *, reason = None):
        '''
        Ban a user __outside__ the server.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 2 uses (guild).
        **Example:** {prefix}{command_name} 472832990012243969 Develope a bot

        **You need:** `Ban Members`.
        **I need:** `Ban Members`, `Send Messages`.
        '''

        guild = ctx.guild
        if reason == None:
            reason = "`None provided`"
        
        try:
            await guild.ban(discord.Object(id = id), reason = reason)
        except discord.HTTPException:
            await ctx.send("I can't ban this person. The most common one would be your id is wrong.")
            return
        else:
            embed = Facility.get_default_embed(
                title = "User Banned",
                description = '''
                        **User `%d` has been banned from this server.** :hammer:
                        **Reason:** %s
                ''' % (id, reason),
                color = 0x000000,
                timestamp = datetime.utcnow()
            ).set_footer(
                text = f"Banned by {ctx.author.name}",
                icon_url = ctx.author.avatar_url
            )

            await ctx.reply(embed = embed, mention_author = False)

    @commands.command()
    @commands.has_guild_permissions(kick_members = True)
    @commands.bot_has_permissions(send_messages = True)
    @commands.bot_has_guild_permissions(kick_members = True)
    @commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
    async def kick(self, ctx, member : discord.Member, *, reason = None):
        '''
        Kick a member.

        **Usage:** <prefix>**{command_name}** <ID/mention/name/nickname> [reason]
        **Cooldown:** 5 seconds per 2 uses (guild).
        **Example 1:** {prefix}{command_name} MikeJollie Dumb
        **Example 2:** {prefix}{command_name} <@472832990012243969> Still dumb
        **Example 3:** {prefix}{command_name} 472832990012243969

        **You need:** `Kick Members`.
        **I need:** `Kick Members`, `Send Messages`.
        '''

        guild = ctx.guild
        victim_name = str(member)
        if reason == None:
            reason = "`None provided`"

        try:
            await guild.kick(member, reason = reason)
        except discord.Forbidden as f:
            await ctx.send("I cannot kick someone that's higher than me!")
        else:
            embed = Facility.get_default_embed(
                title = "Member Kicked",
                description = '''
                        **User `%s` has been kicked out from this server.**
                        **Reason:** %s
                ''' % (victim_name, reason),
                color = 0x000000,
                timestamp = datetime.utcnow()
            ).set_footer(
                text = f"Kicked by {ctx.author.name}",
                icon_url = ctx.author.avatar_url
            )
            
            await ctx.reply(embed = embed, mention_author = False)
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("I cannot kick someone that's not in the guild! If you want someone not to join your guild, use `%shackban`." % ctx.prefix)
    
    @commands.command(hidden = True, enabled = True)
    @commands.has_permissions(kick_members = True)
    @commands.bot_has_guild_permissions(kick_members = True)
    @commands.cooldown(1, 5.0, commands.BucketType.guild)
    async def mute(self, ctx, member : discord.Member, *, reason = None):
        '''
        Mute a member.
        Note: this command will find a role named `Muted` in the guild and use it as the mute role.
        If not existed, one will be created which will deny `Send Messages`, `Send TTS Messages`, `Add Reactions` and `Speak` by default.

        **Usage:** <prefix>**{command_name}** <member> [reason]
        **Cooldown:** 5 seconds per 1 use (guild).
        **Example:** {prefix}{command_name} MikeJollie stop boasting about lolis.

        **You need:** `Kick Members`.
        **I need:** `Manage Roles`, `Manage Permissions`.
        '''
        
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

            # TODO: overwrites overwrite old permissions.
            failed_channels = []
            for channel in guild.channels:
                try:
                    if channel.type == discord.ChannelType.category:
                        await channel.edit(
                            overwrites = {
                                member: discord.PermissionOverwrite(
                                    send_messages = False,
                                    send_tts_messages = False,
                                    add_reactions = False,
                                    speak = False
                                )
                            }
                        )
                    elif channel.type == discord.ChannelType.text:
                        await channel.edit(
                            overwrites = {
                                member: discord.PermissionOverwrite(
                                    send_messages = False,
                                    send_tts_messages = False,
                                    add_reactions = False
                                )
                            }
                        )
                    elif channel.type == discord.ChannelType.voice:
                        await channel.edit(
                            overwrites = {
                                member: discord.PermissionOverwrite(
                                    speak = False
                                )
                            }
                        )
                except discord.Forbidden:
                    failed_channels.append(channel.name)

        await member.add_roles(mute_role, reason = f"{member} is muted by {ctx.author} for {reason}.")
        if len(failed_channels) != 0:
            await ctx.send("Failed channels: %s" % failed_channels)

        # Perform DB actions here

    @commands.command()
    @commands.has_guild_permissions(ban_members = True)
    @commands.bot_has_permissions(send_messages = True)
    @commands.bot_has_guild_permissions(ban_members = True)
    @commands.cooldown(rate = 2, per = 5.0, type = commands.BucketType.guild)
    async def unban(self, ctx, id : int, *, reason = None):
        '''
        Unban a user.

        **Usage:** <prefix>**{command_name}** {command_signature}
        **Cooldown:** 5 seconds per 2 uses (guild).
        **Example:** {prefix}{command_name} 472832990012243969 You've redeemed your goodness.

        **You need:** `Ban Members`.
        **I need:** `Ban Members`, `Send Messages`.
        '''

        guild = ctx.guild

        try:
            await guild.unban(discord.Object(id = id), reason = reason)
        except discord.HTTPException:
            await ctx.send("The ban hammer is too heavy! Make sure the id is correct, and that the user is already banned.")
            return
        else:
            embed = Facility.get_default_embed(
                title = "Member Unbanned",
                description = '''
                        **User `%d` has been banned from this server.** :hammer:
                        **Reason:** %s
                ''' % (id, reason),
                color = 0x000000,
                timestamp = datetime.utcnow()
            ).set_footer(
                text = f"Unbanned by {ctx.author.name}",
                icon_url = ctx.author.avatar_url
            )
            
            await ctx.reply(embed = embed, mention_author = False)


def setup(bot):
    bot.add_cog(Moderation(bot))