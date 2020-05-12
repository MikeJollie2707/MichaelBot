import json
import discord
import datetime
import textwrap

def get_config(guild_id) -> dict:
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

def save_config(config) -> None:
    """
    Save the configuration for the guild.
    Note: This function is deprecated and will be removed in near future.
    """
    if isinstance(config, dict):
        fin = open("./data/" + str(config["GUILD_ID"]) + ".json", 'w')
        json.dump(config, fin, indent = 4)

def get_default_embed(author : discord.User, title : str = "", description : str = "", color : discord.Color = discord.Color.green(), timestamp : datetime.datetime = datetime.datetime.utcnow()) -> discord.Embed:
    """
    Generate a "default" embed with footer and the time.

    The embed can still be mutated.

    Note that for logging, you should overwrite the footer to something else. It is default to "Requested by "

    Parameter:
    - `author`: a `discord.User` or `discord.Member` to set to the footer.
    - `title`: optional title.
    - `description`: optional description.
    - `color`: optional color, default to green.
    - `timestamp`: optional timestamp, default to utcnow().

    Return type: `discord.Embed` or `None` on failure.
    """
    try:
        embed = discord.Embed(
            title = title,
            description = textwrap.dedent(description),
            color = color,
            timestamp = timestamp
        ).set_footer(
            text = f"Requested by {author.name}",
            icon_url = author.avatar_url
        )
    except AttributeError as ae:
        print(ae)
        embed = None

    return embed

def striplist(array : list) -> str:
    """
    Turn the list of objects into a string.

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