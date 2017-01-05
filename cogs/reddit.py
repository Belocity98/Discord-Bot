from discord.ext import commands
import discord
import praw

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

    @commands.command(pass_context=True)
    @commands.cooldown(1, 15, commands.BucketType.server)
    async def fetchtop(self, ctx, subreddit : str, time : str, amount : int):
        """Fetch top Reddit posts of a subreddit."""
        times = ["hour", "day", "year", "all"]
        if time in times:
            subs = []
            submissions = self.reddit.subreddit(subreddit).top(time)
            for submission in submissions:
                if (submission.domain == "i.imgur.com") or (submission.domain == "i.redd.it") or (submission.domain == "gfycat.com"):
                    subs.append(submission.url)
            if len(subs) == 0:
                await self.bot.say("```\nFound 0 submissions.\n```")
                return
            if amount > 10:
                await self.bot.say("```\nThat's too many posts to search through!\n```")
                return
            newsubs = len(subs)
            tmp = len(subs) - amount
            del subs[-tmp:]
            await self.bot.say("\n".join(subs))
            await self.bot.say("```\nFound {} submissions, printing {}.\n```".format(newsubs, amount))
            llog = "{} fetched {} top {} posts from {}.".format(str(ctx.message.author), str(amount), time, subreddit)
            await self.bot.get_cog("Logging").do_logging(llog)
        else:
            await self.bot.say("Time not recognized. Expected all/year/day/hour.")



def setup(bot):
    bot.add_cog(Reddit(bot))
