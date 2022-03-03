import lightbulb
import hikari

import typing as t

import emoji

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

# Reference: https://github.com/Rapptz/discord.py/blob/master/discord/colour.py#L164
class DefaultColor:
    '''
    Store several default colors to use instantly.
    '''
    @staticmethod
    def teal(): return hikari.Color(0x1abc9c)

    @staticmethod
    def dark_teal(): return hikari.Color(0x11806a)

    @staticmethod
    def brand_green(): return hikari.Color(0x57F287)

    @staticmethod
    def green(): return hikari.Color(0x2ecc71)

    @staticmethod
    def dark_green(): return hikari.Color(0x1f8b4c)

    @staticmethod
    def blue(): return hikari.Color(0x3498db)

    @staticmethod
    def dark_blue(): return hikari.Color(0x206694)

    @staticmethod
    def purple(): return hikari.Color(0x9b59b6)

    @staticmethod
    def dark_purple(): return hikari.Color(0x71368a)

    @staticmethod
    def magenta(): return hikari.Color(0xe91e63)

    @staticmethod
    def dark_magenta(): return hikari.Color(0xad1457)

    @staticmethod
    def gold(): return hikari.Color(0xf1c40f)

    @staticmethod
    def dark_gold(): return hikari.Color(0xc27c0e)

    @staticmethod
    def orange(): return hikari.Color(0xe67e22)

    @staticmethod
    def dark_orange(): return hikari.Color(0xa84300)

    @staticmethod
    def brand_red(): return hikari.Color(0xED4245)

    @staticmethod
    def red(): return hikari.Color(0xe74c3c)

    @staticmethod
    def dark_red(): return hikari.Color(0x992d22)

    @staticmethod
    def lighter_gray(): return hikari.Color(0x95a5a6)

    @staticmethod
    def dark_gray(): return hikari.Color(0x607d8b)

    @staticmethod
    def light_gray(): return hikari.Color(0x979c9f)

    @staticmethod
    def darker_gray(): return hikari.Color(0x546e7a)

    @staticmethod
    def og_blurple(): return hikari.Color(0x7289da)

    @staticmethod
    def blurple(): return hikari.Color(0x5865F2)

    @staticmethod
    def greyple(): return hikari.Color(0x5865F2)

    @staticmethod
    def dark_theme(): return hikari.Color(0x36393F)

    @staticmethod
    def fuchsia(): return hikari.Color(0xEB459E)

    @staticmethod
    def yellow(): return hikari.Color(0xFEE75C)

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
    color = kwargs.get("color") if kwargs.get("color") is not None else DefaultColor.green()
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
