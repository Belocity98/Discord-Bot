from discord.ext import commands
import discord
import json
import aiohttp

class Stats():

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop, headers={'User-Agent': 'TheTrain2000'})
        self.cggurl = self.bot.config["cgg"]["url"]
        self.cggkey = self.bot.config["cgg"]["token"]

    @commands.command(pass_context=True)
    async def matchup(self, ctx, champ1 : str, champ2 : str):
        """See the lane matchup between two champions."""
        url = self.cggurl + "champion/" + champ1.replace(' ', '').replace("'", '') + "/matchup/" + champ2.replace(' ', '').replace("'", '') + "?api_key=" + self.cggkey
        async with self.session.get(url) as rawdata:
            data = await rawdata.json()
        if not isinstance(data, list):
            await self.bot.say("Matchup not found.")
            return
        else:
            lines = ['```', '{} vs. {}'.format(champ1, champ2), '------------']
            lines.append('Games - {0[games]}')
            lines.append('Win Rate - {0[winRate]}%')
            lines.append('Role - {0[role]}')
            lines.append('```')
            message = '\n'.join(lines)
            await self.bot.say(message.format(data[0]))
        llog = "{} found the matchup for {} and {}.".format(str(ctx.message.author), champ1, champ2)
        await self.bot.get_cog("Logging").do_logging(llog)

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
        llog = "{} found {}'s Overwatch stats.'".format(str(ctx.message.author), battletag)
        await self.bot.get_cog("Logging").do_logging(llog)
        if mode == "competitive":
            await self.bot.say(message.format(data["us"]["stats"]["competitive"]))
        elif mode == "quickplay":
            await self.bot.say(message.format(data["us"]["stats"]["quickplay"]))
        else:
            await self.bot.say("Unknown gamemode.")

    @commands.command()
    async def winrate(self, *, champ : str):
        """Get the winrate for a champion."""
        llog = "{} found LoL winrates for {}.".format(str(ctx.message.author), champ)
        await self.bot.get_cog("Logging").do_logging(llog)
        if champ == "high":
            url = self.cggurl + "stats/champs/mostWinning?api_key=" + self.cggkey
            async with self.session.get(url) as rawdata:
                data = await rawdata.json()
            await self.bot.say(
                "```\n" + "Highest Winrate Champions" + "\n"
                "-------------------------\n"
                + "1. " + data["data"][0]["name"] + " - " + data["data"][0]["role"] + " - " + str(data["data"][0]["general"]["winPercent"]) + "%\n"
                + "2. " + data["data"][1]["name"] + " - " + data["data"][1]["role"] + " - " + str(data["data"][1]["general"]["winPercent"]) + "%\n"
                + "3. " + data["data"][2]["name"] + " - " + data["data"][2]["role"] + " - " + str(data["data"][2]["general"]["winPercent"]) + "%\n"
                + "4. " + data["data"][3]["name"] + " - " + data["data"][3]["role"] + " - " + str(data["data"][3]["general"]["winPercent"]) + "%\n"
                + "5. " + data["data"][4]["name"] + " - " + data["data"][4]["role"] + " - " + str(data["data"][4]["general"]["winPercent"]) + "%\n```")
        elif champ == "low":
            url = self.cggurl + "stats/champs/leastWinning?api_key=" + self.cggkey
            async with self.session.get(url) as rawdata:
                data = await rawdata.json()
            await self.bot.say(
                "```\n" + "Lowest Winrate Champions" + "\n"
                "-------------------------\n"
                + "1. " + data["data"][0]["name"] + " - " + data["data"][0]["role"] + " - " + str(data["data"][0]["general"]["winPercent"]) + "%\n"
                + "2. " + data["data"][1]["name"] + " - " + data["data"][1]["role"] + " - " + str(data["data"][1]["general"]["winPercent"]) + "%\n"
                + "3. " + data["data"][2]["name"] + " - " + data["data"][2]["role"] + " - " + str(data["data"][2]["general"]["winPercent"]) + "%\n"
                + "4. " + data["data"][3]["name"] + " - " + data["data"][3]["role"] + " - " + str(data["data"][3]["general"]["winPercent"]) + "%\n"
                + "5. " + data["data"][4]["name"] + " - " + data["data"][4]["role"] + " - " + str(data["data"][4]["general"]["winPercent"]) + "%\n```")
        else:
            url = self.cggurl + "stats/champs/" + champ.replace(' ', '').replace("'", '') + "?api_key=" + self.cggkey
            async with self.session.get(url) as rawdata:
                data = await rawdata.json()
            lines = ["```", data[0]["title"] + " Winrates", "----------"]
            loc = 0
            while loc < len(data):
                lines.append(data[loc]["role"] + " - " + str(data[loc]["general"]["winPercent"]) + "%")
                loc += 1
            lines.append("```")
            await self.bot.say("\n".join(lines))

    @commands.command()
    async def playrate(self, *, champ : str):
        """Get the playrate for a champion."""
        llog = "{} found LoL playrates for {}.".format(str(ctx.message.author), champ)
        await self.bot.get_cog("Logging").do_logging(llog)
        if champ == "high":
            url = self.cggurl + "stats/champs/mostPlayed?api_key=" + self.cggkey
            async with self.session.get(url) as rawdata:
                data = await rawdata.json()
            await self.bot.say(
                "```\n" + "Most Played Champions" + "\n"
                "-------------------------\n"
                + "1. " + data["data"][0]["name"] + " - " + data["data"][0]["role"] + " - " + str(data["data"][0]["general"]["playPercent"]) + "%\n"
                + "2. " + data["data"][1]["name"] + " - " + data["data"][1]["role"] + " - " + str(data["data"][1]["general"]["playPercent"]) + "%\n"
                + "3. " + data["data"][2]["name"] + " - " + data["data"][2]["role"] + " - " + str(data["data"][2]["general"]["playPercent"]) + "%\n"
                + "4. " + data["data"][3]["name"] + " - " + data["data"][3]["role"] + " - " + str(data["data"][3]["general"]["playPercent"]) + "%\n"
                + "5. " + data["data"][4]["name"] + " - " + data["data"][4]["role"] + " - " + str(data["data"][4]["general"]["playPercent"]) + "%\n```")
        elif champ == "low":
            url = self.cggurl + "stats/champs/leastPlayed?api_key=" + self.cggkey
            async with self.session.get(url) as rawdata:
                data = await rawdata.json()
            await self.bot.say(
                "```\n" + "Least Played Champions" + "\n"
                "-------------------------\n"
                + "1. " + data["data"][0]["name"] + " - " + data["data"][0]["role"] + " - " + str(data["data"][0]["general"]["playPercent"]) + "%\n"
                + "2. " + data["data"][1]["name"] + " - " + data["data"][1]["role"] + " - " + str(data["data"][1]["general"]["playPercent"]) + "%\n"
                + "3. " + data["data"][2]["name"] + " - " + data["data"][2]["role"] + " - " + str(data["data"][2]["general"]["playPercent"]) + "%\n"
                + "4. " + data["data"][3]["name"] + " - " + data["data"][3]["role"] + " - " + str(data["data"][3]["general"]["playPercent"]) + "%\n"
                + "5. " + data["data"][4]["name"] + " - " + data["data"][4]["role"] + " - " + str(data["data"][4]["general"]["playPercent"]) + "%\n```")
        else:
            url = self.cggurl + "stats/champs/" + champ.replace(' ', '').replace("'", '') + "?api_key=" + self.cggkey
            async with self.session.get(url) as rawdata:
                data = await rawdata.json()
            lines = ["```", data[0]["title"] + " Playrates", "----------"]
            loc = 0
            while loc < len(data):
                lines.append(data[loc]["role"] + " - " + str(data[loc]["general"]["playPercent"]) + "%")
                loc += 1
            lines.append("```")
            await self.bot.say("\n".join(lines))

def setup(bot):
    bot.add_cog(Stats(bot))
