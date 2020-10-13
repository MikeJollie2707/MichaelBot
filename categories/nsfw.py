import discord
from discord.ext import commands
import aiohttp
from discord.ext.commands.errors import CheckFailure, NSFWChannelRequired
import hentai

import random
import datetime
import typing

from categories.utilities.method_cog import Facility
from categories.templates.navigate import Pages

class NSFW(commands.Cog, command_attrs = {"cooldown_after_parsing": True}):
    """Commands that can only be used in NSFW channels."""
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '🔞'
    
    async def cog_check(self, ctx):
        if not ctx.channel.is_nsfw():
            raise commands.NSFWChannelRequired(ctx.channel)
        
        return True

    @commands.group(invoke_without_command = True)
    @commands.bot_has_permissions(send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.member)
    async def konachan(self, ctx, img_type : str, *, tags : str = ""):
        '''
        Send a picture from konachan API.

        This will run a search on either `konachan.net` (mostly safe images) or `konachan.com` and return an image chosen deemed to be safe.

        - If not provided the tags, it'll search a random image.
        - If provided with tag(s), it'll search an image having all the tags. The tags **must be exactly the same** as it appears in `konachan.net`/`konachan.com`. 
        
        Visit [this page](https://konachan.net/tag) to see all the tags, or you can use `{prefix}konachan tags` to see some popular tags.

        **Usage:** <prefix>**{command_name}** <safe/any> [exact tags separated by space]
        **Cooldown:** 5 seconds per 1 use (member)
        **Example 1:** {prefix}{command_name} safe blush long_hair
        **Example 2:** {prefix}{command_name} any

        **You need:** None.
        **I need:** `Send Messages`.
        '''

        if ctx.invoked_subcommand == None:
            SEARCH_ENDPOINT = "https://konachan.net/post.json"
            if img_type.upper() != "SAFE" and img_type.upper() != "ANY":
                raise commands.BadArgument
            elif img_type.upper() == "SAFE":
                SEARCH_ENDPOINT = "https://konachan.net/post.json"
            else:
                SEARCH_ENDPOINT = "https://konachan.com/post.json"
                
            async with ctx.typing():
                user_tag_str = "+"
                chosen_entry = None
                cache_entry = None

                loop = 0

                # Transform user_tag_list into search query.
                user_tag_str = user_tag_str.join(tags.split())

                while chosen_entry is None:
                    if loop >= 6:
                        break
                    async with aiohttp.ClientSession() as session:

                        # Don't set count too high, otherwise it'll be significantly slow if query with tags.
                        # BUG: If a tag has too few pages, it'll most likely return no image.
                        # Possible fix: Try cache the first page to see if it has any images, and then query like normal.
                        # If it's None, then use the cache to display image.
                        page = random.randint(1, 100)
                        count = random.randint(1, 10)

                        query_location = SEARCH_ENDPOINT + "?limit=%d&tags=%s&page=%d" % (count, user_tag_str, 0 if loop == 0 else page)
                        
                        async with session.get(query_location) as resp:
                            if resp.status == 200:
                                # query is a list of dictionary.
                                query = await resp.json()

                                # Either tag not found, or page too large
                                if len(query) == 0:
                                    pass

                                def filter(entry : dict) -> bool:
                                    #if entry["rating"] != "s":
                                    #    return False
                                    #
                                    #RESTRICTED_TAGS = ["breasts", "nipples", "panties", "bikini"] # Expand this
                                    #
                                    #for index, tag in enumerate(RESTRICTED_TAGS):
                                    #    if tag in entry["tags"]:
                                    #        self.bot.debug("Index %d has tag %s so it's not safe." % (index, tag))
                                    #        return False
                                    #
                                    #return True
                                    return True if img_type.upper() == "ANY" else entry["rating"] == 's'
                                
                                random.shuffle(query)
                                chosen_entry = discord.utils.find(filter, query)

                                if chosen_entry is not None:
                                    # page != 0 is to avoid selection bias.
                                    # Basically we cache the first iteration and skip to the next iteration.
                                    if loop == 0 and page != 0:
                                        cache_entry = chosen_entry
                                        chosen_entry = None
                            else:
                                print(resp.status)
                                break
                    loop += 1

                if chosen_entry is not None or (cache_entry is not None and chosen_entry is None):
                    chosen_entry = cache_entry if chosen_entry is None else chosen_entry
                    embed = Facility.get_default_embed(
                        title = "Image incoming",
                        description = "Rating: **%s**" % chosen_entry["rating"],
                        url = chosen_entry["file_url"],
                        timestamp = datetime.datetime.utcnow(),
                    )
                    embed.set_image(
                        url = chosen_entry["file_url"] if chosen_entry["file_url"] is not None else chosen_entry["preview_url"]
                    ).set_footer(
                        text = "Click the title for full image."
                    )

                    tag_str = ""
                    for tag in chosen_entry["tags"].split():
                        tag_str += f"`{tag}` "
                    embed.add_field(name = "Tags", value = tag_str, inline = False)
                else:
                    embed = Facility.get_default_embed(
                        title = "Uh oh",
                        timestamp = datetime.datetime.utcnow()
                    )
                    embed.description = "Oops, no image for you. This is usually due to no image found or \
                        the image has been reviewed by the FBI and it did not pass (yes the images are usually reviewed by the FBI before sending)."
                    embed.set_image(url = "https://i.imgflip.com/3ddefb.jpg")
            
                await ctx.send(embed = embed)
    @konachan.command()
    async def tags(self, ctx):
        '''
        Display top 10 popular tags in konachan.

        **Usage:** <prefix>**{command_name}**
        **Cooldown:** 5 seconds per 1 use (member)
        **Example:** {prefix}{command_name}

        """
        async with ctx.typing():
            SEARCH_ENDPOINT = "https://konachan.com/tag.json"
            query_location = SEARCH_ENDPOINT + "?order=count&limit=10"
            async with aiohttp.ClientSession() as session:
                async with session.get(query_location) as resp:
                    if resp.status == 200:
                        # query is a list(dictionary)
                        query = await resp.json()
                        tag_list = ["`%s`" % tag_object["name"] for tag_object in query]

                        embed = Facility.get_default_embed(
                            title = "Top 10 Popular Tags",
                            description = Facility.striplist(tag_list),
                            timestamp = datetime.datetime.utcnow(),
                            author = ctx.author
                        )

                        await ctx.send(embed = embed)

    async def display_hentai(self, ctx, doujin : hentai.Hentai):
        tag_list = [f"`{tag.name}`" for tag in doujin.tag]
        author_list = [f"`{artist.name}`" for artist in doujin.artist]

        first_page = Facility.get_default_embed(
            title = doujin.title(),
            description = "",
            url = doujin.url,
            author = ctx.author
        ).add_field(
            name = "Tags:",
            value = Facility.striplist(tag_list),
            inline = False
        ).add_field(
            name = "Author:",
            value = Facility.striplist(author_list),
            inline = False
        ).set_image(
            url = doujin.image_urls[0]
        )
        paginate = Pages()
        paginate.add_page(first_page)
        
        for index, page in enumerate(doujin.pages):
            if index == 0:
                continue
            
            embed = Facility.get_default_embed(
                title = "Page %d" % (index + 1),
                url = page.url,
                author = ctx.author
            )
            embed.set_footer(
                text = embed.footer.text + " | Page %d/%d" % (index, len(doujin.pages))
            ).set_image(
                url = page.url
            )

            paginate.add_page(embed)

        await paginate.event(ctx, interupt = False)
    @commands.group(invoke_without_command = True)
    @commands.bot_has_permissions(send_messages = True)
    async def nhentai(self, ctx):
        '''
        Search and return a doujin on request.
        You can read the doujin right here on Discord without opening a private/incognito tab!

        Currently, this command alone does nothing. It must be used using its subcommands.
        '''
        # Issue: we're using blocking library...
        pass
    @nhentai.command(name = "random")
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.member)
    async def _random(self, ctx):
        '''
        Search and return a random doujin.

        This will show you an absolute random doujin, whether it's a piece of trash or a masterpiece.

        **Usage:** {prefix}**{command_name}**
        **Cooldown:** 5 seconds per 1 use (member)
        **Example:** {prefix}{command_name}

        **You need:** `NSFW Channel`.
        **I need:** `Read Message History`, `Add Reactions`, `Send Messages`.
        '''

        doujin = hentai.Hentai(hentai.Utils.get_random_id())

        await self.display_hentai(ctx, doujin)
    @nhentai.command()
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.member)
    async def search(self, ctx, param : typing.Optional[int], *tags):
        '''
        Search and return a doujin based on its tag or ID.

        If search based on tags, it'll search based on `Most Popular`.

        **Usage:** {prefix}**{command_name}** <id/tags>
        **Cooldown:** 5 seconds per 1 use (member)
        **Example 1:** {prefix}{command_name} 331228
        **Example 2:** {prefix}{command_name} sole-female sole-male

        **You need:** `NSFW Channel`.
        **I need:** `Read Message History`, `Add Reactions`, `Send Messages`.
        '''

        if isinstance(param, int):
            doujin = hentai.Hentai(param)

            await self.display_hentai(ctx, doujin)
        else:
            query_str = "tag:"
            joiner = "+"
            tag_join = joiner.join(tags)
            query_str += tag_join

            doujin = hentai.Hentai(
                random.choice(hentai.Hentai.search_by_query(
                    query_str, sort = hentai.Sort.Popular)
                )["id"]
            )

            await self.display_hentai(ctx, doujin)


def setup(bot):
    bot.add_cog(NSFW(bot))
