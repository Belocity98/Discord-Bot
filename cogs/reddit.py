import discord
import praw

from discord.ext import commands

class Reddit():

    def __init__(self, bot):
        self.bot = bot
        self.reddit = praw.Reddit(
        client_id=self.bot.config["reddit"]["id"],
        client_secret=self.bot.config["reddit"]["secret"],
        password=self.bot.config["reddit"]["password"],
        username=self.bot.config["reddit"]["username"],
        user_agent='Discord Reddit Bot'
        )

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def fetchtop(self, ctx, subreddit : str, time : str, amount : int):
        """Fetch top Reddit posts of a subreddit.
        Valid times: hour, day, year, all"""
        times = ["hour", "day", "year", "all"]
        if time in times:
            subs = []
            submissions = self.reddit.subreddit(subreddit).top(time)
            for submission in submissions:
                domains = ["i.imgur.com", "i.redd.it", "gfycat.com"]
                if submission.domain in domains:
                    subs.append(submission.url)
            if len(subs) == 0:
                await ctx.channel.send("```\nFound 0 submissions.\n```")
                return
            if amount > 10:
                await ctx.channel.send("```\nThat's too many posts to search through!\n```")
                return
            newsubs = len(subs)
            tmp = len(subs) - amount
            del subs[-tmp:]
            await ctx.channel.send("\n".join(subs))
            await ctx.channel.send(f"```\nFound {newsubs} submissions, printing {amount}.\n```")
        else:
            await ctx.channel.send("Time not recognized. Expected all/year/day/hour.")



def setup(bot):
    bot.add_cog(Reddit(bot))
