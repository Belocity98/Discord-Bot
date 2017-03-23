# Thanks to Danny (Rapptz on GitHub) for the uptime information.

import datetime
import discord
import json
import aiohttp
import os

from discord.ext import commands

class Stats():

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop, headers={'User-Agent': 'TheTrain2000-i<3uFUYU'})

    @commands.command()
    async def ostats(self, ctx, battletag : str, mode : str):
        """Overwatch statistics for a specified user."""
        url = "https://owapi.net/api/v3/u/" + battletag.replace('#', '-') + "/stats"
        async with self.session.get(url) as rawdata:
            data = await rawdata.json()
        lines = ["```", "{}'s Overwatch Statistics".format(battletag), "----------"]
        lines.append("Level - {0[overall_stats][level]}")
        lines.append("Prestige - {0[overall_stats][prestige]}")
        lines.append("Comp. SR - {0[overall_stats][comprank]}")
        lines.append("Time Played - {0[game_stats][time_played]} hours")
        lines.append("-----")
        lines.append("Games Won - {0[game_stats][games_won]}")
        lines.append("Eliminations - {0[game_stats][eliminations]}")
        lines.append("Deaths - {0[game_stats][deaths]}")
        lines.append("KDR - {0[game_stats][kpd]}")
        lines.append("Gold Medals - {0[game_stats][medals_gold]}")
        lines.append('```')
        message = '\n'.join(lines)
        if mode == "competitive":
            await ctx.channel.send(message.format(data["us"]["stats"]["competitive"]))
        elif mode == "quickplay":
            await ctx.channel.send(message.format(data["us"]["stats"]["quickplay"]))
        else:
            await ctx.channel.send("Unknown gamemode.")

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
        embed.url = 'https://discord.gg/Whf6UUk'
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
    bot.add_cog(Stats(bot))
