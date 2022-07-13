'''Contains many useful functions.'''

import asyncio
import datetime as dt
import typing as t

import emoji
import hikari
import lightbulb

from utils import models

__PERMISSIONS_MAPPING__ = {
    # Community Server Permissions
    hikari.Permissions.REQUEST_TO_SPEAK:    "Request to Speak",
    hikari.Permissions.VIEW_GUILD_INSIGHTS: "Server Insights",

    # General Server Permissions
    hikari.Permissions.VIEW_CHANNEL: "View Channels",
    hikari.Permissions.MANAGE_CHANNELS: "Manage Channels",
    hikari.Permissions.MANAGE_ROLES: "Manage Roles",
    hikari.Permissions.MANAGE_EMOJIS_AND_STICKERS: "Manage Emojis and Stickers",
    hikari.Permissions.VIEW_AUDIT_LOG: "View Audit Log",
    hikari.Permissions.MANAGE_WEBHOOKS: "Manage Webhooks",
    hikari.Permissions.MANAGE_GUILD: "Manage Server",

    # Membership Permissions
    hikari.Permissions.CREATE_INSTANT_INVITE: "Create Invite",
    hikari.Permissions.CHANGE_NICKNAME: "Change Nickname",
    hikari.Permissions.MANAGE_NICKNAMES: "Manage Nicknames",
    hikari.Permissions.KICK_MEMBERS: "Kick Members",
    hikari.Permissions.BAN_MEMBERS: "Ban Members",
    hikari.Permissions.MODERATE_MEMBERS: "Timeout Members",

    # Text Channel Permissions
    hikari.Permissions.SEND_MESSAGES: "Send Messages",
    hikari.Permissions.SEND_MESSAGES_IN_THREADS: "Send Messages in Threads",
    hikari.Permissions.CREATE_PUBLIC_THREADS: "Create Public Threads",
    hikari.Permissions.CREATE_PRIVATE_THREADS: "Create Private Threads",
    hikari.Permissions.EMBED_LINKS: "Embed Links",
    hikari.Permissions.ATTACH_FILES: "Attach Files",
    hikari.Permissions.ADD_REACTIONS: "Add Reactions",
    hikari.Permissions.USE_EXTERNAL_EMOJIS: "Use External Emoji",
    hikari.Permissions.USE_EXTERNAL_STICKERS: "Use External Stickers",
    hikari.Permissions.MENTION_ROLES: "Mention @everyone, @here, and All Roles",
    hikari.Permissions.MANAGE_MESSAGES: "Manage Messages",
    hikari.Permissions.MANAGE_THREADS: "Manage Threads",
    hikari.Permissions.READ_MESSAGE_HISTORY: "Read Message History",
    hikari.Permissions.SEND_TTS_MESSAGES: "Send Text-to-Speech Messages",
    hikari.Permissions.USE_APPLICATION_COMMANDS: "Use Application Commands",

    # Voice Channel Permissions
    hikari.Permissions.CONNECT: "Connect",
    hikari.Permissions.SPEAK: "Speak",
    hikari.Permissions.STREAM: "Video",
    hikari.Permissions.START_EMBEDDED_ACTIVITIES: "Use Activities",
    hikari.Permissions.USE_VOICE_ACTIVITY: "Use Voice Activity",
    hikari.Permissions.PRIORITY_SPEAKER: "Priority Speaker",
    hikari.Permissions.MUTE_MEMBERS: "Mute Members",
    hikari.Permissions.DEAFEN_MEMBERS: "Deafen Members",
    hikari.Permissions.MOVE_MEMBERS: "Move Members",

    # Events Permissions

    # Advanced Permissions
    hikari.Permissions.ADMINISTRATOR: "Administrator",
}

CONSUME_REST_OPTION = lightbulb.OptionModifier.CONSUME_REST
GREEDY_OPTION = lightbulb.OptionModifier.GREEDY

# Read Messages is too standard so we don't include it.
COMMAND_STANDARD_PERMISSIONS = (
    hikari.Permissions.SEND_MESSAGES,
    hikari.Permissions.READ_MESSAGE_HISTORY,
)

class ClassToDict:
    def to_dict(self) -> dict:
        if not hasattr(self, "__slots__") or not self.__slots__:
            return self.__dict__
        
        d = {}
        for attr in self.__slots__:
            d[attr] = getattr(self, attr)
        return d

def embed_from_dict(data: dict[str, t.Any], /) -> hikari.Embed:
    '''Generate an embed from a dictionary.

    Parameters
    ----------
    data : dict[str, t.Any]
        A valid dict representation of an embed.

    Returns
    -------
    hikari.Embed
        The embed from the dict.
    '''

    embed = hikari.Embed()

    embed.title = data.get("title", None)
    embed.description = data.get("description", None)
    embed.url = data.get("url", None)

    if embed.title is not None:
        embed.title = str(embed.title)
    if embed.description is not None:
        embed.description = str(embed.description)
    if embed.url is not None:
        embed.url = str(embed.url)
    
    try:
        embed.color = hikari.Color(data["color"])
    except KeyError:
        pass

    try:
        embed.timestamp = dt.datetime.fromtimestamp(data['timestamp'], tz = dt.timezone.utc)
    except KeyError:
        pass

    try:
        value = data["thumbnail"]
    except KeyError:
        pass
    else:
        embed.set_thumbnail(value)
    
    try:
        value = data["author"]
    except KeyError:
        pass
    else:
        embed.set_author(**value)
    
    try:
        value = data["fields"]
    except KeyError:
        pass
    else:
        for field in value:
            embed.add_field(**field)
    
    try:
        value = data["image"]
    except KeyError:
        pass
    else:
        embed.set_image(value)

    try:
        value = data["footer"]
    except KeyError:
        pass
    else:
        embed.set_footer(**value)

    return embed

def embed_to_dict(embed: hikari.Embed, /) -> dict[str, t.Any]:
    '''Convert an embed into a dict object.

    Parameters
    ----------
    embed : hikari.Embed
        An embed object to convert.

    Returns
    -------
    dict[str, t.Any]
        A dictionary that conforms Discord's structure.
    '''

    d = {}

    if bool(embed.title):
        d["title"] = embed.title
    if bool(embed.description):
        d["description"] = embed.description
    if bool(embed.url):
        d["url"] = embed.url
    
    if bool(embed.color):
        d["color"] = int(embed.color)
    if bool(embed.timestamp):
        d["timestamp"] = embed.timestamp.timestamp()
    if bool(embed.thumbnail):
        d["thumbnail"] = embed.thumbnail.url
    if bool(embed.author):
        d["author"] = {
            "name": embed.author.name,
            "url": embed.author.url
        }

        if bool(embed.author.icon):
            d["author"]["icon"] = embed.author.icon.url
    if bool(embed.fields):
        d["fields"] = []
        for field in embed.fields:
            d["fields"].append({
                "name": field.name,
                "value": field.value,
                "inline": field.is_inline
            })
    if bool(embed.image):
        d["image"] = embed.image.url
    if bool(embed.footer):
        d["footer"] = {
            "text": embed.footer.text
        }

        if bool(embed.footer.icon):
            d["footer"]["icon"] = embed.footer.icon.url
    
    return d

def get_emote(discord_text: str, /) -> str:
    '''Return the Unicode emoji based on the name provided.

    Parameters
    ----------
    discord_text : str
        Discord/Twitter name of the emoji including `:`. Example: `:grin:`.

    Returns
    -------
    str
        The Unicode emoji matching the text.

    Raises
    ------
    KeyError
        Cannot find the emoji based on the text.
    '''

    ret = emoji.emojize(discord_text, language = "alias")
    if ret == discord_text:
        raise KeyError(f"Emoji {discord_text} cannot be found.")
    return ret

def get_friendly_permissions(permissions: hikari.Permissions, /) -> t.List[str]:
    '''Return a list of highlighted permissions string presented in the permission provided.
    This returns the exact Discord's string of the permission.

    Parameters
    ----------
    permissions : hikari.Permissions
        A permission object.

    Returns
    -------
    t.List[str]
        A list of highlighted permissions string represented in the permission provided.

    Notes
    -----
    `Manage Events` cannot be found in Hikari's documentation. Therefore, it is not included.
    '''

    l = []
    for permission, text in __PERMISSIONS_MAPPING__.items():
        if permissions & permission:
            l.append(f"`{text}`")
    return l

def get_default_embed(*, author: hikari.Member = None, **kwargs) -> hikari.Embed:
    '''Return a default embed to work with for consistency.

    Args:
        author: The author to set in the footer.
        **kwargs: `hikari.Embed` constructor.

    Parameters
    ----------
    author : hikari.Member, optional
        The author to set in the footer. If not provided, the footer will not be edited.
    **kwargs : dict
        The options passed into `hikari.Embed()`.

    Returns
    -------
    hikari.Embed
        The default embed.
    '''

    title = kwargs.get("title")
    url = kwargs.get("url")
    description = kwargs.get("description")
    color = kwargs.get("color") if kwargs.get("color") is not None else models.DefaultColor.green
    timestamp = kwargs.get("timestamp")

    embed = hikari.Embed(
        title = title,
        url = url,
        description = description,
        color = color,
        timestamp = timestamp
    )
    if author is not None:
        embed.set_footer(
            text = f"Requested by {author.username}",
            icon = author.avatar_url
        )
    
    return embed

def mention(mentionable_object: t.Union[hikari.PartialUser, hikari.PartialRole, hikari.TextableGuildChannel], /) -> str:
    '''Return the appropriate mention string for a mentionable object.

    Parameters
    ----------
    mentionable_object : t.Union[hikari.PartialUser, hikari.PartialRole, hikari.TextableGuildChannel]
        The object to mention.

    Returns
    -------
    str
        The object's default mention string.
    
    Notes
    -----
    If the object is a `hikari.PartialRole` and it has the name `@everyone`, it'll return the name directly.
    '''

    if isinstance(mentionable_object, hikari.PartialRole):
        if mentionable_object.name == "@everyone":
            return mentionable_object.name
    
    return mentionable_object.mention

async def sleep_until(when: dt.datetime, /):
    '''Wait until the specified time.

    Parameters
    ----------
    when : dt.datetime
        The time to resume. Must be tz aware and in utc.
    '''
    time = when - dt.datetime.now().astimezone()
    if time.total_seconds() > 0:
        await asyncio.sleep(time.total_seconds())

def striplist(arr: t.Sequence[str], /) -> str:
    '''Return a string from a list, separated by comma.

    Parameters
    ----------
    arr : t.Sequence[str]
        A sequence of objects that are convertible to `str`.

    Returns
    -------
    str
        The final string. Empty if sequence is empty.
    '''

    return ", ".join(arr)

# Default emojis for the navigators and stuffs. Just save it here for now.
__default_emojis__ = {
    "first_page": get_emote(":last_track_button:"),
    "prev_page": get_emote(":arrow_backward:"),
    "next_page": get_emote(":arrow_forward:"),
    "last_page": get_emote(":next_track_button:"),
    "terminate": get_emote(":stop_button:"),
    "timeout": get_emote(":clock12:"),
    "success": get_emote(":white_check_mark:"),
    "return": get_emote(":arrow_up_small:"),
}
