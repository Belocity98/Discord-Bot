import discord
import asyncio
import logging

from discord.ext import commands
from .utils import config, checks

log = logging.getLogger(__name__)

class Mod:

    def __init__(self, bot):
        self.bot = bot

        self.db = bot.db

        self.active_bans = 0

    @commands.command(no_pm=True)
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member : discord.Member, length : int, *, reason : str='No reason given.'):
        """Temporarily bans a member for a specified amount of time."""

        if length > 10000:
            return await ctx.send('Length of ban is too long.')

        guild = ctx.guild
        author = ctx.author

        invitation = await guild.create_invite(max_uses=1)

        user_embed = discord.Embed()
        user_embed.color = 0xd60606

        user_embed.title = 'You have been banned!'
        user_embed.description = f'{author.name} has banned you.\n\nInvite: {invitation.url}\nAfter your ban time is up, ' \
                                'click this link to rejoin the server.'
        user_embed.add_field(name='Reason', value=reason)
        user_embed.add_field(name='Length', value=f'{length} seconds')

        public_embed = discord.Embed()
        public_embed.color = 0xd60606

        public_embed.title = f'{member.name} has been banned!'
        public_embed.description = f'This member was banned by {author.name}.'
        public_embed.add_field(name='Reason', value=reason)
        public_embed.add_field(name='Length', value=f'{length} seconds')

        await ctx.send(embed=public_embed)
        await member.send(embed=user_embed)

        await member.ban(reason=reason, delete_message_days=0)
        self.active_bans += 1

        await asyncio.sleep(length)

        self.active_bans -= 1
        await member.unban(reason='Softban time expired.')

    @commands.command()
    @checks.is_owner()
    async def activebans(self, ctx):
        """Views the amount of active softbans."""
        await ctx.send(self.active_bans)

    @commands.command(no_pm=True)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member : discord.Member):
        """Kicks a member from the server."""

        await member.kick()

    @commands.command(no_pm=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, limit : int=10):
        """Deletes messages from the channel."""

        limit += 1

        if limit > 100 or limit < 1:
            await ctx.send('Invalid limit!')
            return

        await ctx.channel.purge(limit=limit)

def setup(bot):
    bot.add_cog(Mod(bot))
