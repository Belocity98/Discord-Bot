from discord.ext import commands
import discord
import league


class LeagueOfLegends:

    def __init__(self, bot):
        self.bot = bot

        self.session = bot.session

        self.api_key = bot.credentials['championgg']

    @commands.group(name='lol', aliases=['leagueoflegends', 'league'])
    async def _lol(self, ctx):
        """Shows information about League of Legends."""


    @_lol.command(name='champ', aliases=['champion'])
    async def lol_champ(self, ctx, *, champion : str):
        """Shows statistics for the specified champion."""

        embed = discord.Embed()
        embed.color = 0xa442f4

        resp = await self.api_call(f'champion/{champion}/general')
        if isinstance(resp, dict) and resp.get('error'):
            e = resp.get('error')
            embed.description = f'Error: {e}'
            await ctx.send(embed=embed)
            return

        name = resp[0]['name']
        embed.title = name
        embed.description = f'Showing statistics for {name}.'

        for role in resp:
            role_name = role['role']
            win_prct = role['winPercent']['val']
            win_change = role['winPercent']['change']
            play_prct = role['playPercent']['val']
            play_change = role['playPercent']['change']
            ban_prct = role['banRate']['val']
            ban_change = role['banRate']['change']

            avg_kills = role['kills']['val']
            avg_kills_change = role['kills']['change']
            avg_dths = role['deaths']['val']
            avg_dths_change = role['deaths']['change']
            avg_asts = role['assists']['val']
            avg_asts_change = role['assists']['change']

            value = f'Winrate: {win_prct}%, changed {win_change}% since last patch.\n' \
                    f'Playrate: {play_prct}%, changed {play_change}% since last patch.\n' \
                    f'Banrate: {ban_prct}%, changed {ban_change}% since last patch.\n' \
                    f'\nAvg. Kills: {avg_kills}, changed {avg_kills_change} since last patch.\n' \
                    f'Avg. Deaths: {avg_dths}, changed {avg_dths_change} since last patch.\n' \
                    f'Avg. Assists: {avg_asts}, changed {avg_asts_change} since last patch.'

            embed.add_field(name=role_name, value=value)

        await ctx.send(embed=embed)


    async def api_call(self, call, terms={}):

        url = f'http://api.champion.gg/{call}?api_key={self.api_key}'

        async with self.session.get(url, params=terms) as rawdata:
            return await rawdata.json()

def setup(bot):
    bot.add_cog(LeagueOfLegends(bot))
