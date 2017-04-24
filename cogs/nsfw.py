import discord
import asyncio

from discord.ext import commands
from random import randint
from .utils import checks

class NSFW:

    def __init__(self, bot):
        self.bot = bot

        self.db = bot.db

        self.base_url = 'https://im1.ibsearch.xxx/'
        self.api_url = 'https://ibsearch.xxx/api/v1/'
        self.api_key = bot.credentials['ibsearch']

        self.session = bot.session

    @commands.group(invoke_without_command=True, no_pm=True)
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

    @nsfw.command(no_pm=True, name='enable')
    @commands.has_permissions(manage_guild=True)
    async def n_enable(self, ctx):
        """Enables nsfw command for this channel."""
        server_db = self.db.get(ctx.guild.id, {})
        nsfw_channels = server_db.get('nsfw_channels', [])

        nsfw_channels.append(ctx.channel.id)

        server_db['nsfw_channels'] = nsfw_channels
        await self.db.put(ctx.guild.id, server_db)

        await ctx.send('👍')

    @nsfw.command(no_pm=True, name='disable')
    @commands.has_permissions(manage_guild=True)
    async def n_disable(self, ctx):
        """Disables nsfw command for this channel."""
        server_db = self.db.get(ctx.guild.id, {})
        nsfw_channels = server_db.get('nsfw_channels', [])

        nsfw_channels.remove(ctx.channel.id)

        server_db['nsfw_channels'] = nsfw_channels
        await self.db.put(ctx.guild.id, server_db)

        await ctx.send('👍')

    async def api_call(self, request, format, query, limit):
        url = f'{self.api_url}{request}.{format}?q={query}&limit={limit}&key={self.api_key}'

        async with self.session.get(url) as rawdata:
            return await rawdata.json()

def setup(bot):
    bot.add_cog(NSFW(bot))
