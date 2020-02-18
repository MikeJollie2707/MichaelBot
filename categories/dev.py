import discord
from discord.ext import commands

import asyncio

# Commands for developers to test things and stuffs.


def is_dev(ctx):
    return ctx.author.id in [472832990012243969, 462726152377860109, 481934034130174010]
                            #MikeJollie#1067     Stranger.com#4843   MJ2#8267

class Dev(commands.Cog, command_attrs = {"cooldown_after_parsing" : True, "hidden" : True}):
    '''Commands for developers to abuze power'''
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()
        elif not is_dev(ctx):
            raise commands.CheckFailure()
    
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("This command is reserved for bot developers only!")

    @commands.command()
    @commands.cooldown(1, 5.0, commands.BucketType.default)
    async def reload(self, ctx, name):
        '''
        Reload a module.
        Useful when you don't want to disconnect the bot but still update your change.
        **Usage:** <prefix>**{command_name}** <extension name>
        **Cooldown:** 5 seconds (global cooldown)
        **Example:** {prefix}{command_name} categories.templates.navigate

        **You need:** `dev status`.
        **I need:** `Send Messages`.
        '''
        self.bot.reload_extension(name)
        await ctx.send("Reloaded extension " + name)
        print("Reloaded extension " + name)
    @reload.error
    async def reload_error(self, ctx, error):
        if isinstance(error, commands.ExtensionNotFound):
            await ctx.send("I cannot find this extension. Check your typo or the repo again.")
    
    @commands.command()
    async def reset_all_cooldown(self, ctx):
        '''
        Self-explanatory.
        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        You need: `dev status`.
        I need: `Send Messages`.
        '''
        for command in self.bot.commands:
            if command.is_on_cooldown(ctx):
                command.reset_cooldown(ctx)
        await ctx.send("All cooldown reseted.")

    # I'm intending to move this command to a category called "Administrator" or something.
    @commands.command()
    @commands.is_owner()
    async def leave_guild(self, ctx):
        '''
        Leave the current guild.
        Note: This does not delete the server's config file yet.

        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        **You need:** `Owner of the server` OR `dev status`.
        **I need:** `Send Messages`.
        '''
        await ctx.send("Are you sure for me to leave this guild?")
        def check(msg):
            return msg.author == ctx.author
        
        try:
            confirm = self.bot.wait_for("message", check = check, timeout = 30.0)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. I'll stay still.")
            return
        else:
            confirm_str = confirm.content.upper()
            if confirm_str[0] == "Y":
                try:
                    await ctx.send("Bye! :wave:")
                    await ctx.guild.leave()
                except discord.HTTPException:
                    await ctx.send("Leaving the guild failed. Guess you'll stick with me for a while :smile:")
    
    @commands.command(aliases = ["suggest_response"])
    @commands.cooldown(1, 60.0, commands.BucketType.default)
    async def report_response(self, ctx, message_ID : int, *, response : str):
        '''
        Response to a report/suggest.
        Note that the command will look over the last 100 messages in the report channel.

        **Aliases:** `suggest_response`
        **Usage:** <prefix>**{command_name}** <message ID> <response>
        **Cooldown:** 60 seconds per 1 use (global)
        **Examples:** {prefix}{command_name} 670493266629886002 I like this idea, but the library doesn't allow so.

        **You need:** `dev status`.
        **I need:** `Send Messages`.
        '''

        report_chan = 644339079164723201 # Do not change
        channel = self.bot.get_channel(report_chan)
        if channel == None:
            await ctx.send("Seems like I can't find the report channel. You can check again and edit the channel ID.")
            return
        
        messages = await channel.history(limit = 100).flatten()
        for message in messages:
            if message_ID == message.id:
                if len(message.embeds) == 0:
                    await ctx.send("This message is not a report/suggest type. Please check again.")
                else:
                    report = message.embeds[0]

                    response_embed = discord.Embed().from_dict(report.to_dict()) # Create a new embed using the old's dictionary form. This will make it work fast.

                    response_embed.add_field(
                        name = "**Developer Response:**",
                        value = response,
                        inline = False
                    )
                    response_embed.set_footer(
                        text = str(ctx.author),
                        icon_url = ctx.author.avatar_url
                    )

                    await message.edit(embed = response_embed)


def setup(bot):
    bot.add_cog(Dev(bot))