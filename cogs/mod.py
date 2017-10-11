import asyncio

from discord.ext import commands
import discord


class Mod:

    def __init__(self, bot):
        self.bot = bot

        self.db = bot.db

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member: discord.Member, length: int, *, reason: str='No reason given.'):
        """Temporarily bans a member for a specified amount of time."""

        if length > 10000:
            return await ctx.send('Length of ban is too long.')

        guild = ctx.guild
        author = ctx.author

        try:
            invitation = await guild.create_invite(max_uses=1)
        except discord.HTTPException:
            return  # we couldn't create an invite, so don't ban.

        user_embed = discord.Embed()
        user_embed.color = 0xd60606
        user_embed.title = 'You have been banned!'
        user_embed.description = f'{author.name} has banned you.\n\nInvite: {invitation.url}\n' \
                                 f'After your ban time is up, click this link to rejoin the server.'
        user_embed.add_field(name='Reason', value=reason)
        user_embed.add_field(name='Length', value=f'{length} seconds')

        public_embed = discord.Embed()
        public_embed.color = 0xd60606
        public_embed.title = f'{member.name} has been banned!'
        public_embed.description = f'This member was banned by {author.name}.'
        public_embed.add_field(name='Reason', value=reason)
        public_embed.add_field(name='Length', value=f'{length} seconds')

        try:
            await ctx.send(embed=public_embed)
        except discord.HTTPException:
            pass  # couldn't send the public embed
        try:
            await member.send(embed=user_embed)
        except discord.HTTPException:
            return  # couldn't send the private message, so don't ban

        try:
            await member.ban(reason=reason, delete_message_days=0)
        except discord.HTTPException:
            return  # we couldn't ban them

        await asyncio.sleep(length)

        try:
            await member.unban(reason='Softban time expired.')
        except discord.HTTPException:
            pass  # we couldn't unban them

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member):
        """Kicks a member from the server."""

        try:
            await member.kick()
        except discord.HTTPException:
            return  # we couldn't kick them

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, limit: int=10):
        """Deletes messages from the channel."""

        limit += 1

        if limit > 100 or limit < 1:
            await ctx.send('Invalid limit!')
            return

        try:
            await ctx.channel.purge(limit=limit)
        except discord.HTTPException:
            return  # we couldn't purge the messages


def setup(bot):
    bot.add_cog(Mod(bot))
