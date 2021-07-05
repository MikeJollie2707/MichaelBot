# Before someone coming in here and flame at me for writing 18+ stuffs,
# this is just for FUN. This entire module (except `konachan`, which is like 50/50 18+)
# is written as a joke during NNN. Don't take this seriously ._.
from NHentai.entities.doujin import Doujin
from NHentai.entities.page import SearchPage
import discord
from discord.ext import commands
import aiohttp
from NHentai.nhentai_async import NHentaiAsync

import random
import datetime
import typing

from templates.navigate import Pages
import utilities.facility as Facility

class NSFW(commands.Cog, command_attrs = {"cooldown_after_parsing": True}):
    """Commands that can only be used in NSFW channels."""
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '🔞'
    
    async def cog_check(self, ctx):
        if not ctx.channel.is_nsfw():
            raise commands.NSFWChannelRequired(ctx.channel)
        elif isinstance(ctx.channel, discord.DMChannel):
            raise commands.NoPrivateMessage()
        
        return True

    @commands.group(invoke_without_command = True)
    @commands.bot_has_permissions(read_message_history = True, send_messages = True)
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.member)
    async def konachan(self, ctx, safe__any : str, *, tags : str = ""):
        '''
        Send a picture from konachan API.

        This will run a search on either `konachan.net` (mostly safe images) or `konachan.com` and return an image.

        - If not provided the tags, it'll search a random image.
        - If provided with tag(s), it'll search an image having all the tags. The tags **must be exactly the same** as it appears in `konachan.net`/`konachan.com`. 
        
        Visit [this page](https://konachan.net/tag) to see all the tags.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 1 use (member)
        **Example 1:** {prefix}{command_name} safe blush long_hair
        **Example 2:** {prefix}{command_name} any

        **You need:** `NSFW Channel`.
        **I need:** `Send Messages`.
        '''

        if ctx.invoked_subcommand == None:
            SEARCH_ENDPOINT = "https://konachan.net/post.json"
            if safe__any.upper() != "SAFE" and safe__any.upper() != "ANY":
                raise commands.BadArgument
            elif safe__any.upper() == "SAFE":
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
                                    return True if safe__any.upper() == "ANY" else entry["rating"] == 's'
                                
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
            
                await ctx.reply(embed = embed, mention_author = False)
    @konachan.command()
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.member)
    async def tags(self, ctx):
        '''
        Display top 10 popular tags in konachan.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 1 use (member)
        **Example:** {prefix}{command_name}

        **You need:** `NSFW Channel`.
        **I need:** `Send Messages`.
        '''
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

                        await ctx.reply(embed = embed, mention_author = False)

    async def display_hentai(self, ctx, doujin : Doujin):
        NHENTAI_DEFAULT = "https://nhentai.net/g/"
        tag_list = [f"`{tag}`" for tag in doujin.tags]
        author_list = [f"`{artist}`" for artist in doujin.artists]

        first_page = Facility.get_default_embed(
            title = doujin.title,
            description = "",
            url = f"{NHENTAI_DEFAULT}{doujin.id}",
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
            url = doujin.images[0]
            # No idea why the line below won't display the image
            #url = f"{NHENTAI_DEFAULT}{doujin.id}/1/"
        )

        paginate = Pages()
        paginate.add_page(first_page)
        
        for index, image_url in enumerate(doujin.images):
            if index == 0:
                continue
            
            embed = Facility.get_default_embed(
                title = "Page %d" % (index + 1),
                #url = image_url,
                url = f"{NHENTAI_DEFAULT}{doujin.id}/{index + 1}/",
                author = ctx.author
            )
            embed.set_footer(
                text = embed.footer.text + " | Page %d/%d" % (index, doujin.total_pages)
            ).set_image(
                url = image_url
            )

            paginate.add_page(embed)

        await paginate.start(ctx, interupt = False)
    @commands.group(invoke_without_command = True)
    @commands.bot_has_permissions(add_reactions = True, read_message_history = True, send_messages = True)
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
    async def nhentai_random(self, ctx):
        '''
        Search and return a random doujin.

        This will show you an absolute random doujin, whether it's a piece of trash or a masterpiece.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 1 use (member)
        **Example:** {prefix}{command_name}

        **You need:** `NSFW Channel`.
        **I need:** `Read Message History`, `Add Reactions`, `Send Messages`.
        '''

        doujin = await NHentaiAsync().get_random()

        await self.display_hentai(ctx, doujin)
    @nhentai.command(name = "search")
    @commands.cooldown(rate = 1, per = 5.0, type = commands.BucketType.member)
    async def nhentai_search(self, ctx, id__tags : typing.Optional[int], *tags):
        '''
        Search and return a doujin based on its tag or ID.

        If search based on tags, it'll search based on `Most Popular`.

        **Usage:** {usage}
        **Cooldown:** 5 seconds per 1 use (member)
        **Example 1:** {prefix}{command_name} 331228
        **Example 2:** {prefix}{command_name} sole-female sole-male

        **You need:** `NSFW Channel`.
        **I need:** `Read Message History`, `Add Reactions`, `Send Messages`.
        '''

        if isinstance(id__tags, int):
            doujin = await NHentaiAsync().get_doujin(id = str(id__tags))

            await self.display_hentai(ctx, doujin)
        else:
            query_str = ""
            joiner = "+"
            tag_join = joiner.join(tags)
            query_str += tag_join

            doujin = None

            doujin_list : SearchPage = await NHentaiAsync().search(
                query = query_str,
                sort = 'popular'
            )

            if len(doujin_list.doujins) > 0:
                doujin = random.choice(doujin_list.doujins)
                print(doujin.id)
                await self.display_hentai(ctx, await NHentaiAsync().get_doujin(id = doujin.id))
            else:
                await ctx.send("One of the tags doesn't exist. Please check again.")

def setup(bot):
    bot.add_cog(NSFW(bot))
