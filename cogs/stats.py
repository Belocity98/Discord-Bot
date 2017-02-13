import discord
import json
import aiohttp
import os

from discord.ext import commands

class Stats():

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop, headers={'User-Agent': 'TheTrain2000-i<3uFUYU'})

    @commands.command(pass_context=True)
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
            await self.bot.say(message.format(data["us"]["stats"]["competitive"]))
        elif mode == "quickplay":
            await self.bot.say(message.format(data["us"]["stats"]["quickplay"]))
        else:
            await self.bot.say("Unknown gamemode.")

    @commands.command(aliases=['stats'])
    async def about(self):
        """Tells you information about the bot itself."""

        embed = discord.Embed()
        embed.title = 'Official Bot Server Invite'
        embed.url = 'https://discord.gg/Whf6UUk'
        embed.colour = 0x1BE118 # lucio green

        owner = await self.bot.get_user_info(self.bot.config['your_user_id'])

        embed.set_author(name=str(owner), icon_url=owner.avatar_url)

        # statistics
        total_members = sum(len(s.members) for s in self.bot.servers)
        total_online  = sum(1 for m in self.bot.get_all_members() if m.status != discord.Status.offline)
        unique_members = set(self.bot.get_all_members())
        unique_online = sum(1 for m in unique_members if m.status != discord.Status.offline)

        members = '%s total\n%s online\n%s unique\n%s unique online' % (total_members, total_online, len(unique_members), unique_online)
        embed.add_field(name='Members', value=members)
        embed.set_footer(text='Made with discord.py', icon_url='http://i.imgur.com/5BFecvA.png')

        embed.add_field(name='Servers', value=len(self.bot.servers))

        await self.bot.say(embed=embed)

def setup(bot):
    bot.add_cog(Stats(bot))
