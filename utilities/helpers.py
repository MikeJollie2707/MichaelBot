import lightbulb
import hikari
import emoji

import typing as t

import utilities.models as models

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
COMMAND_STANDARD_PERMISSIONS = [
    hikari.Permissions.SEND_MESSAGES,
    hikari.Permissions.READ_MESSAGE_HISTORY,
]

def get_emote(discord_text: str) -> str:
    '''
    Return the Unicode emoji based on the name provided.

    Parameter:
    - `discord_text`: Discord/Twitter name of the emoji including `:`. Example: `:grin:`.

    Exception:
    - `KeyError`: Cannot find the emoji based on the text.
    '''

    ret = emoji.emojize(discord_text, use_aliases = True)
    if ret == discord_text:
        raise KeyError(f"Emoji {discord_text} cannot be found.")
    return ret

def get_friendly_permissions(permissions: hikari.Permissions) -> t.List[str]:
    '''
    Return a list of highlighted permissions string presented in the permission provided.
    This returns the exact Discord's string of the permission.

    Parameter:
    - `permissions`: A permission object.

    Note: `Manage Events` cannot be found in Hikari's doc.
    '''

    l = []
    for permission in __PERMISSIONS_MAPPING__:
        if permissions & permission:
            l.append(f"`{__PERMISSIONS_MAPPING__[permission]}`")
    return l

def get_default_embed(author: hikari.Member = None, **kwargs) -> hikari.Embed:
    '''
    Return a default embed to work with for consistency.

    Parameter:
    - `author`: The author to set in the footer.
    - `**kwargs`: `hikari.Embed` constructor.
    '''

    title = kwargs.get("title")
    url = kwargs.get("url")
    description = kwargs.get("description")
    color = kwargs.get("color") if kwargs.get("color") is not None else models.DefaultColor.green()
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

def mention(mentionable_object: t.Union[hikari.PartialUser, hikari.PartialRole, hikari.TextableGuildChannel]) -> str:
    '''
    Return the appropriate mention string for a mentionable object.
    
    If the object is a `hikari.PartialRole` and it has the name "@everyone", then it'll return the name directly.
    Otherwise, it returns the object's default mention.

    Parameter:
    - `mentionable_object`: The object to mention.
    '''

    if isinstance(mentionable_object, hikari.PartialRole):
        if mentionable_object.name == "@everyone":
            return mentionable_object.name
    
    return mentionable_object.mention

def striplist(arr: t.Sequence) -> str:
    '''
    Return a nice string representation of a list.

    Parameter:
    - `arr`: A `Sequence`.
    '''

    if len(arr) == 0:
        return ""
    return ", ".join(arr)
