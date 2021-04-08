import discord
from discord.ext import commands

import datetime
import inspect
import textwrap
from py_expression_eval import Parser
import typing
import numpy

import categories.utilities.db as DB

async def get_config(bot, guild_id) -> dict:
    """
    Return a guild's row as a `dict`.

    It is NOT recommend to add any new keys into the resultant `dict`.

    There is a special key `ERROR` to check if the resultant `dict` is good to use.

    Parameter:
    - `bot`: A `commands.Bot` instance that has a `pool` attribute.
    - `guild_id`: The guild's id.
    """

    config = {}
    async with bot.pool.acquire() as conn:
        guild = await DB.Guild.find_guild(conn, guild_id)
        if guild is not None:
            config = dict(guild)
            config["ERROR"] = 0
        else:
            config["ERROR"] = -1
    
    return config

async def save_config(bot, config) -> None:
    """
    Save the configuration for the guild.

    This is an abstract way to modify all columns in `DGuilds` except `id`.

    *This will be removed when `DB.Guild.bulk_update()` is available.*
    
    Parameter:
    - `bot`: A `commands.Bot` instance that has a `pool` attribute.
    - `config`: A `dict` that is returned previously from `get_config`.
    """
    if isinstance(config, dict):
        async with bot.pool.acquire() as conn:
            guild = await DB.Guild.find_guild(conn, config["id"])
            if guild is not None:
                guild_col = [column for column in guild]
                for option in config:
                    # We do NOT want to change the id column, ever.
                    if (option in guild_col) and (option != "id"):
                        await DB.Guild.update_generic(conn, config["id"], option, config[option])

def calculate(expression : str) -> str:
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

def convert_roleperms_dpy_discord(role_permissions : str) -> str:
    permissions = {
        # General Server Permissions
        "read_messages"        : "View Channels",
        "manage_channels"      : "Manage Channels",
        "manage_roles"         : "Manage Roles",
        "manage_emojis"        : "Manage Emojis",
        "view_audit_log"       : "View Audit Log",
        "manage_webhooks"      : "Manage Webhooks",
        "manage_guild"         : "Manage Server",

        # Membership Permissions
        "create_instant_invite": "Create Invite",
        "change_nickname"      : "Change Nickname",
        "manage_nicknames"     : "Manage Nicknames",
        "kick_members"         : "Kick Members",
        "ban_members"          : "Ban Members",

        # Text Channel Permissions
        "send_messages"        : "Send Messages",
        "embed_links"          : "Embed Links",
        "attach_files"         : "Attach Files",
        "add_reactions"        : "Add Reactions",
        "external_emojis"      : "Use External Emojis",
        "mention_everyone"     : "Mention @everyone, @here, and All Roles",
        "manage_messages"      : "Manage Messages",
        "read_message_history" : "Read Message History",
        "send_tts_messages"    : "Send TTS Messages",
        "use_slash_commands"   : "Use Slash Commands",

        # Voice Channel Permissions
        "connect"              : "Connect",
        "speak"                : "Speak",
        "stream"               : "Video",
        "use_voice_activation" : "Use Voice Activity",
        "priority_speaker"     : "Priority Speaker",
        "mute_members"         : "Mute Members",
        "deafen_members"       : "Deafen Members",
        "move_members"         : "Move Members",

        # Advanced Permissions
        "administrator"        : "Administrator"
    }
    return permissions[role_permissions]

def convert_channelperms_dpy_discord(channel_permissions : str) -> str:
    permissions = {
        # General Channel Permissions
        "read_messages"        : "View Channel",
        "manage_channels"      : "Manage Channels",
        "manage_roles"         : "Manage Permissions",
        "manage_webhooks"      : "Manage Webhooks",

        # Membership Permissions
        "create_instant_invite": "Create Invite",

        # Text Channel Permissions
        "send_messages"        : "Send Messages",
        "embed_links"          : "Embed Links",
        "attach_files"         : "Attach Files",
        "add_reactions"        : "Add Reaction",
        "external_emojis"      : "Use External Emojis",
        "mention_everyone"     : "Mention @everyone, @here, and All Roles",
        "manage_messages"      : "Manage Messages",
        "read_message_history" : "Read Message History",
        "send_tts_messages"    : "Send TTS Messages",
        "use_slash_commands"   : "Use Slash Commands",

        # Voice Channel Permissions
        "connect"              : "Connect",
        "speak"                : "Speak",
        "stream"               : "Video",
        "use_voice_activation" : "Use Voice Activity",
        "priority_speaker"     : "Priority Speaker",
        "mute_members"         : "Mute Members",
        "deafen_members"       : "Deafen Members",
        "move_members"         : "Move Members"
    }

    return permissions[channel_permissions]  

def clean_signature(command_signature : str) -> str:
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

def get_default_embed(title : str = "", url : str = "", description : str = "", color : discord.Color = discord.Color.green(), timestamp : datetime.datetime = datetime.datetime.utcnow(), author : discord.User = None) -> discord.Embed:
    """
    Generate a "default" embed with footer and the time.

    The embed can still be mutated.

    Note that for logging, you should overwrite the footer to something else. It is default to `Requested by `

    Parameter:
    - `timestamp`: the timestamp, usually `utcnow()`. The default value is there just to make the parameters look good, you still have to provide it.
    - `author`: optional `discord.User` or `discord.Member` to set to the footer. If not provided, it won't set the footer.
    - `title`: optional title.
    - `url`: optional url for the title.
    - `description`: optional description. Internally it'll remove the tabs.
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

def mention(discord_object : discord.Object) -> str:
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

def striplist(array : typing.Union[list, numpy.ndarray]) -> str:
    """
    Turn the list of objects into a string.

    What it does is just simply turn the list into a string and strip away `[]` and `'`.
    If the list is empty, it'll return the string "".

    Parameter: 
    - `array`: a list.

    Return type: `str`
    """

    if len(array) == 0:
        return ""

    #st = str(array)

    #st = st.replace('[', "")
    #st = st.replace(']', "")
    #st = st.replace("'", "")

    st = ", ".join(array)

    return st