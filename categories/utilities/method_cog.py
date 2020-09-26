import discord
from discord.ext import commands

import json
import datetime
import inspect
import textwrap
from py_expression_eval import Parser
import ast

class Facility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @classmethod
    def get_config(cls, guild_id) -> dict:
        """
        Get the configuration for the guild.
        Note: This function is deprecated and will be removed in near future.
        """
        config = {"ERROR": 0, "GUILD_ID": guild_id}
        file_name = str(guild_id) + ".json"
        try:
            fin = open("./data/" + file_name, 'r')
        except FileNotFoundError:
            config["ERROR"] = -1
        else:
            config = json.load(fin)

        return config

    @classmethod
    def save_config(cls, config) -> None:
        """
        Save the configuration for the guild.
        Note: This function is deprecated and will be removed in near future.
        """
        if isinstance(config, dict):
            fin = open("./data/" + str(config["GUILD_ID"]) + ".json", 'w')
            json.dump(config, fin, indent = 4)

    @classmethod
    def calculate(cls, expression : str) -> str:
        """
        Calculate a simple mathematical expression.

        This is currently used in `calc` command.

        Parameter:
        - `expression`: The expression to calculate. Example: `5+5`.

        Return: The result of the expression.
        - If a `ZeroDivisionError` is raised, it will be "Infinity/Undefined".
        - If an `Exception` is raised, it will be "Error".
        """

        parser = Parser()
        answer = 0 
        try:
            answer = parser.parse(expression).evaluate({})
            answer = str(answer)
        except ZeroDivisionError:
            answer = "Infinity/Undefined"
        except Exception:
            answer = "Error"
        return answer  

    @classmethod
    def get_default_embed(
        cls, 
        title : str = "", 
        url : str = "", 
        description : str = "", 
        color : discord.Color = discord.Color.green(), 
        timestamp : datetime.datetime = datetime.datetime.utcnow(),
        author : discord.User = None
        ) -> discord.Embed:
        """
        Generate a "default" embed with footer and the time.

        The embed can still be mutated.

        Note that for logging, you should overwrite the footer to something else. It is default to "Requested by "

        Parameter:
        - `timestamp`: the timestamp, usually `utcnow()`. The default value is there just to make the parameters look good, you still have to provide it.
        - `author`: optional `discord.User` or `discord.Member` to set to the footer. If not provided, it won't set the footer.
        - `title`: optional title.
        - `url`: optional url for the title.
        - `description`: optional description. Internally it'll remove the tabs so no need to pass inspect.cleandoc(description).
        - `color`: optional color, default to green.

        Return type: `discord.Embed` or `None` on failure.
        """

        try:
            embed = discord.Embed(
                title = title,
                url = url,
                description = textwrap.dedent(inspect.cleandoc(description)),
                color = color,
                timestamp = timestamp
            )
            if (author is not None):
                embed.set_footer(
                    text = f"Requested by {author.name}",
                    icon_url = author.avatar_url
                )
        except AttributeError as ae:
            print(ae)
            embed = None

        return embed
    
    @classmethod
    def mention(cls, discord_object : discord.Object) -> str:
        """
        A utility function that returns a mention string to be used.

        The only reason this function exists is because `discord.Role.mention` being retarded when the role is @everyone.
        In that case, the function will return directly @everyone, not @@everyone. Otherwise, the function just simply return object.mention.

        Because of this, you can use the default `.mention` unless it's a `discord.Role`.

        Note that if there's a custom role that's literally named `@everyone` then this function will return @everyone, not @@everyone.

        Parameter:
        - `discord_object`: A Discord Object that is mentionable, including `discord.abc.User`, `discord.abc.GuildChannel` and `discord.Role`.

        Return: The string used to mention the object.
        - If the parameter's type does not satisfy the above requirements, it returns empty string.
        """
        if isinstance(discord_object, discord.abc.User):
            return discord_object.mention
        elif isinstance(discord_object, discord.abc.GuildChannel):
            return discord_object.mention
        elif isinstance(discord_object, discord.Role):
            if discord_object.name == "@everyone":
                return "@everyone"
            else:
                return discord_object.mention
        else:
            return ""
    
    @classmethod
    def striplist(cls, array : list) -> str:
        """
        Turn the list of objects into a string.

        What it does is just simply turn the list into a string and strip away `[]` and `'`.

        Useful for logging list of permissions.

        Parameter: 
        - `array`: a list.

        Return type: `str`
        """

        st = str(array)

        st = st.replace('[', "")
        st = st.replace(']', "")
        st = st.replace("'", "")

        return st
                

def setup(bot):
    bot.add_cog(Facility(bot))