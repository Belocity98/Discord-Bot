from random import randint

from discord.ext import commands
import discord

from .utils import checks


class NSFW:

    def __init__(self, bot):
        self.bot = bot

        self.db = bot.db

        self.base_url = 'https://im1.ibsearch.xxx/'
        self.api_url = 'https://ibsearch.xxx/api/v1/'
        self.api_key = bot.credentials['ibsearch']

        self.session = bot.session

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @checks.is_nsfw()
    async def nsfw(self, ctx, *, tags : str=None):
        """Sends a random nsfw image. Tag(s) optional to reduce search."""

        seed = randint(1, 100000)

        searching = await ctx.send('Searching nsfw database...')

        if tags:
            resp = await self.api_call('images', 'json', f'{tags} size<2m rating:e format:jpg,png', 1)
        else:
            resp = await self.api_call('images', 'json', f'random:{seed} size<2m rating:e format:jpg,png', 1)

        try:
            url = self.base_url + resp[0]['path']
        except:
            await searching.edit(content='No results found.')
            return

        embed = discord.Embed()
        embed.color = 0x3427c4

        embed.description = f'[Image Link]({url})'
        embed.set_image(url=url)

        await searching.edit(content=' ', embed=embed)

    async def api_call(self, request, format, query, limit):
        url = f'{self.api_url}{request}.{format}?q={query}&limit={limit}&key={self.api_key}'

        async with self.session.get(url) as rawdata:
            return await rawdata.json()

def setup(bot):
    bot.add_cog(NSFW(bot))
