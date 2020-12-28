import discord
from discord.ext import commands

import json
import datetime
import inspect
import textwrap
from py_expression_eval import Parser
import ast
import typing
import numpy

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
    def convert_roleperms_dpy_discord(self, role_permissions : str) -> str:
        if role_permissions == "administrator":
            return "Administrator"
        if role_permissions == "view_audit_log":
            return "View Audit Log"
        if role_permissions == "manage_guild":
            return "Manage Server"
        if role_permissions == "manage_roles":
            return "Manage Roles"
        if role_permissions == "manage_channels":
            return "Manage Channels"
        if role_permissions == "kick_members":
            return "Kick Members"
        if role_permissions == "ban_members":
            return "Ban Members"
        if role_permissions == "create_instant_invite":
            return "Create Invite"
        if role_permissions == "change_nickname":
            return "Change Nickname"
        if role_permissions == "manage_nicknames":
            return "Manage Nicknames"
        if role_permissions == "manage_emojis":
            return "Manage Emojis"
        if role_permissions == "manage_webhooks":
            return "Manage Webhooks"
        if role_permissions == "read_messages":
            return "Read Text Channels & See Voice Channels"
        if role_permissions == "send_messages":
            return "Send Messages"
        if role_permissions == "send_tts_messages":
            return "Send TTS Messages"
        if role_permissions == "embed_links":
            return "Embed Links"
        if role_permissions == "attach_files":
            return "Attach Files"
        if role_permissions == "read_message_history":
            return "Read Message History"
        if role_permissions == "mention_everyone":
            return "Mention Everyone"
        if role_permissions == "external_emojis":
            return "Use External Emojis"
        if role_permissions == "add_reactions":
            return "Add Reactions"
        if role_permissions == "connect":
            return "Connect"
        if role_permissions == "speak":
            return "Speak"
        if role_permissions == "mute_members":
            return "Mute Members"
        if role_permissions == "deafen_members":
            return "Deafen Members"
        if role_permissions == "move_members":
            return "Move Members"
        if role_permissions == "use_voice_activation":
            return "Use Voice Activity"
        if role_permissions == "priority_speaker":
            return "Priority Speaker"
        if role_permissions == "stream":
            return "Go Live"
    
    @classmethod
    def convert_channelperms_dpy_discord(self, channel_permissions : str) -> str:
        if channel_permissions == "create_instant_invite":
            return "Create Invite"
        if channel_permissions == "manage_channels":
            return "Manage Channels"
        if channel_permissions == "manage_messages":
            return "Manage Messages"
        if channel_permissions == "manage_roles":
            return "Manage Permissions"
        if channel_permissions == "manage_webhooks":
            return "Manage Webhooks"
        if channel_permissions == "read_messages":
            return "Read Messages & View Channel"
        if channel_permissions == "send_messages":
            return "Send Messages"
        if channel_permissions == "send_tts_messages":
            return "Send TTS Messages"
        if channel_permissions == "embed_links":
            return "Embed Links"
        if channel_permissions == "attach_files":
            return "Attach Files"
        if channel_permissions == "read_message_history":
            return "Read Message History"
        if channel_permissions == "mention_everyone":
            return "Mention Everyone"
        if channel_permissions == "external_emojis":
            return "Use External Emojis"
        if channel_permissions == "add_reactions":
            return "Add Reactions"
        # Voice channels
        if channel_permissions == "connect":
            return "Connect"
        if channel_permissions == "speak":
            return "Speak"
        if channel_permissions == "mute_members":
            return "Mute Members"
        if channel_permissions == "deafen_members":
            return "Deafen Members"
        if channel_permissions == "move_members":
            return "Move Members"
        if channel_permissions == "use_voice_activation":
            return "Use Voice Activity"
        if channel_permissions == "priority_speaker":
            return "Priority Speaker"
        if channel_permissions == "stream":
            return "Go Live"  

    @classmethod
    def clean_signature(self, command_signature : str) -> str:
        """
        This method automatically convert a command's signature into a more friendly help message
        display in the `Usage` section.
        
        Note that your parameter's variable should be named carefully:
        - `a_command` will be `a command`
        - `a__command` will be `a/command`

        Parameter:
        - `command_signature`: the command's signature.
        
        Return type: `str`.
        """

        return command_signature.replace('__', '/').replace('_', ' ')

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

        Because of this, you can use the default `.mention` (recommended) unless it's a `discord.Role`.

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
    def striplist(cls, array : typing.Union[list, numpy.ndarray]) -> str:
        """
        Turn the list of objects into a string.

        What it does is just simply turn the list into a string and strip away `[]` and `'`.
        If the list is empty, it'll return the string "None".

        Parameter: 
        - `array`: a list.

        Return type: `str`
        """

        if len(array) == 0:
            return "None"

        st = str(array)

        st = st.replace('[', "")
        st = st.replace(']', "")
        st = st.replace("'", "")

        return st
                

def setup(bot):
    bot.add_cog(Facility(bot))