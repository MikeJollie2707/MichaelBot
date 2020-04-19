import discord
from discord.ext import commands

from datetime import datetime
import textwrap

class Moderation(commands.Cog, command_attrs = {"cooldown_after_parsing" : True}):
    '''Commands related to moderate actions such as kick, ban, etc.'''
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '🔨'
    
    @commands.command()
    @commands.has_permissions(kick_members = True)
    @commands.bot_has_permissions(kick_members = True, send_messages = True)
    @commands.cooldown(2, 5.0, commands.BucketType.guild)
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
            embed = discord.Embed(
                title = "Member Kicked",
                description = textwrap.dedent(
                    '''
                    **User `%s` has been kicked out from this server.**.
                    **Reason:** %s
                    ''' % (victim_name, reason)
                ),
                color = 0x000000,
                timestamp = datetime.utcnow()
            )
            
            await ctx.send(embed = embed)
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("I cannot kick someone that's not in the guild! If you want someone not to join your guild, use `%shackban`." % ctx.prefix)

    @commands.command()
    @commands.has_permissions(ban_members = True)
    @commands.bot_has_permissions(ban_members = True, send_messages = True)
    @commands.cooldown(2, 5.0, commands.BucketType.guild)
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
        except discord.Forbidden as f:
            await ctx.send("I cannot ban someone that's higher than me!")
        else:
            embed = discord.Embed(
                title = "Member Banned",
                description = textwrap.dedent(
                    '''
                    **User `%s` has been banned from this server.**
                    **Reason:** %s
                    ''' % (victim_name, reason)
                ),
                color = 0x000000,
                timestamp = datetime.utcnow()
            )

            await ctx.send(embed = embed)
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("I cannot ban someone that's not in the guild normally. I need the power of `%shackban` to ban." % ctx.prefix)
    
    @commands.command()
    @commands.has_permissions(ban_members = True)
    @commands.bot_has_permissions(ban_members = True)
    @commands.cooldown(2, 5.0, commands.BucketType.guild)
    async def hackban(self, ctx, id : int, *, reason = None):
        '''
        Ban a user __outside__ the server.

        **Usage:** <prefix>**{command_name}** <ID> [reason]
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
        except discord.HTTPException as httperr:
            await ctx.send("I can't ban this person. The most common one would be your id is wrong.")
            return
        else:
            embed = discord.Embed(
                title = "User Banned",
                description = textwrap.dedent(
                    '''
                    **User `%d` has been banned from this server.**
                    **Reason:** %s
                    ''' % (id, reason)
                ),
                color = 0x000000,
                timestamp = datetime.utcnow()
            )

            await ctx.send(embed = embed)

    @commands.command()
    @commands.has_permissions(ban_members = True)
    @commands.bot_has_permissions(ban_members = True)
    @commands.cooldown(2, 5.0, commands.BucketType.guild)
    async def unban(self, ctx, id : int, *, reason = None):
        '''
        Unban a user.

        **Usage:** <prefix>**{command_name}** <ID> [reason]
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
            embed = discord.Embed(
                title = "Member Unbanned",
                description = textwrap.dedent(
                    '''
                    **User `%d` has been unbanned from this server.**
                    **Reason:** %s
                    ''' % (id, reason)
                ),
                color = 0x000000,
                timestamp = datetime.utcnow()
            )
            
            await ctx.send(embed = embed)

    @commands.command(hidden = True, disabled = True)
    @commands.has_permissions(kick_members = True)
    @commands.bot_has_permissions(kick_members = True)
    @commands.cooldown(1, 5.0, commands.BucketType.guild)
    async def mute(self, ctx, id : int, *, reason = None):
        pass

def setup(bot):
    bot.add_cog(Moderation(bot))