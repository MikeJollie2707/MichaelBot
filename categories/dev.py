import discord
from discord.ext import commands

import asyncio

# Commands for developers to test things and stuffs.


def is_dev(ctx):
    return ctx.author.id in [472832990012243969, 462726152377860109, 481934034130174010]
                            #MikeJollie#1067     Stranger.com#4843   MJ2#8267

class Dev(commands.Cog):
    '''Commands for developers to abuze power'''
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(hidden = True)
    @commands.check(is_dev)
    @commands.cooldown(1, 5.0, commands.BucketType.default)
    async def reload(self, ctx, name):
        '''
        Reload a module.
        Useful when you don't want to disconnect the bot but still update your change.
        **Usage:** <prefix>**{command_name}** <extension name>
        **Cooldown:** 5 seconds (global cooldown)
        **Example:** {prefix}{command_name} categories.templates.navigate

        You need: dev status.
        I need: send_messages.
        '''
        self.bot.reload_extension(name)
        await ctx.send("Reloaded extension " + name)
        print("Reloaded extension " + name)
    @reload.error
    async def reload_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("This command is reserved for bot developers only!")
        elif isinstance(error, commands.ExtensionNotFound):
            await ctx.send("I cannot find this extension. Check your typo or the repo again.")
    
    @commands.command(hidden = True)
    @commands.check(is_dev)
    async def reset_all_cooldown(self, ctx):
        '''
        Self-explanatory.
        **Usage:** <prefix>**{command_name}**
        **Example:** {prefix}{command_name}

        You need: dev status.
        I need: send_messages.
        '''
        for command in self.bot.commands:
            if command.is_on_cooldown(ctx):
                command.reset_cooldown(ctx)
        await ctx.send("All cooldown reseted.")

    @commands.command(hidden = True)
    @commands.check(is_dev)
    @commands.cooldown(1, 10.0, commands.BucketType.default)
    async def diary(self, ctx, *, msg : str = ""):
        '''
        Act as a commit on GitHub, but personal.
        **Usage:** <prefix>**{command_name} <message>
        **Cooldown:** 10 seconds (global cooldown)
        **Example:** {prefix}{command_name} Created diary

        You need: dev status.
        I need: send_messages.
        '''
        fout = open("./diary.txt", 'a')
        fout.write("--------------------------------\n")
        fout.write("Writer: %s\n" % ctx.author.name)
        fout.write("Content: %s\n" % msg)
        fout.write("\n\n")
        fout.close()
        await ctx.send("Journal recorded.")

    @commands.command(hidden = True)
    @commands.check(is_dev)
    @commands.cooldown(1, 120.0, commands.BucketType.default)
    async def create_changelog(self, ctx):
        try:
            length = 0

            await ctx.send("Input version")
            msg = self.bot.wait_for("message", timeout = 60.0)
            version = "**__%s__**" % msg
            length += len(version)

            await ctx.send("Any bug fixes (Yes/No)?")
            msg = self.bot.wait_for("message", timeout = 60.0)
            if msg.content.upper() == "NO" or msg.content.upper() == "N":
                bugs = ""
            else:
                bugs = "**Bug Fixes:**\n"
            length += len(bugs)

            bug_list = []
            await ctx.send("Type all the bug fixed here. Type `Done` when you're finished.")
            
            content = ""
            while content.upper() != "DONE":
                msg = self.bot.wait_for("message", timeout = 60.0)

                content = msg.content
                if content.upper() == "DONE":
                    break
                
                bug_list.append(content)
                length += len("- %s\n" % content)
                if length > 2000:
                    bug_list.pop()
                    await ctx.send("Content exceeded 2000 characters.")
                    break
            
            


            if length > 2000:
                await ctx.send("Content exceeded 2000 characters.")
                return
            
            await ctx.send("Any changes (type NO to skip)")
            msg = self.bot.wait_for("message", timeout = 60.0)
            



        except asyncio.TimeoutError:
            pass

    @commands.command(hidden = True)
    @commands.is_owner()
    async def leave_guild(self, ctx):
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
                    await ctx.send("Leaving the guild failed.")

def setup(bot):
    bot.add_cog(Dev(bot))