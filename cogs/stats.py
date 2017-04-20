# Thanks to Danny (Rapptz on GitHub) for most of this cog.
# Especially the uptime and socket stats information.

import datetime
import discord
import json
import aiohttp
import os

from discord.ext import commands
from collections import Counter

class Stats():

    def __init__(self, bot):
        self.bot = bot

    async def on_command(self, ctx):
        self.bot.commands_used[ctx.command.qualified_name] += 1

    async def on_socket_response(self, msg):
        self.bot.socket_stats[msg.get('t')] += 1

    @commands.command(hidden=True)
    async def socketstats(self, ctx):
        delta = datetime.datetime.utcnow() - self.bot.uptime
        minutes = delta.total_seconds() / 60
        total = sum(self.bot.socket_stats.values())
        cpm = total / minutes

        fmt = '%s socket events observed (%.2f/minute):\n%s'
        await ctx.send(fmt % (total, cpm, self.bot.socket_stats))

    def get_bot_uptime(self, *, brief=False):
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if not brief:
            if days:
                fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
            else:
                fmt = '{h} hours, {m} minutes, and {s} seconds'
        else:
            fmt = '{h}h {m}m {s}s'
            if days:
                fmt = '{d}d ' + fmt

        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    @commands.command()
    async def uptime(self, ctx):
        """Tells you how long the bot has been up for."""
        await ctx.send('Uptime: **{}**'.format(self.get_bot_uptime()))

    @commands.command(aliases=['stats'])
    async def about(self, ctx):
        """Tells you information about the bot itself."""

        embed = discord.Embed()
        embed.title = 'Official Bot Guild Invite'
        embed.url = 'https://discord.gg/xbBmYcq'
        embed.colour = 0x1BE118 # lucio green

        owner = await self.bot.get_user_info(self.bot.config['your_user_id'])

        embed.set_author(name=str(owner), icon_url=owner.avatar_url)

        # statistics
        total_members = sum(len(s.members) for s in self.bot.guilds)
        unique_members = len(self.bot.users)

        members = '%s total\n%s unique' % (total_members, unique_members)
        embed.add_field(name='Members', value=members)
        embed.add_field(name='Uptime', value=self.get_bot_uptime(brief=True))
        embed.set_footer(text='Made with discord.py', icon_url='http://i.imgur.com/5BFecvA.png')

        embed.add_field(name='Servers', value=len(self.bot.guilds))
        embed.add_field(name='Commands Run', value=sum(self.bot.commands_used.values()))

        await ctx.channel.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        """Sends an invite link to invite the bot to a server."""

        server_amt = len(self.bot.guilds)
        your_server = server_amt + 1
        server_info = f'This bot is in {server_amt} servers, your server could be number {your_server}!'

        embed = discord.Embed(title=server_info)
        embed.colour = 0x1BE118 # lucio green
        embed.description = '[Invitation Link](https://discordapp.com/oauth2/authorize?client_id=257198307137421312&scope=bot&permissions=1573121151)'
        await ctx.author.send(embed=embed)

def setup(bot):
    bot.commands_used = Counter()
    bot.socket_stats = Counter()
    bot.add_cog(Stats(bot))
