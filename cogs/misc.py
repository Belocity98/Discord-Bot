from discord.ext import commands
import discord
import asyncio

class Misc():

    def __init__(self, bot):
        self.bot = bot
        self.strikes = {}

    @commands.command(pass_context=True)
    @commands.cooldown(1, 5.1, commands.BucketType.user)
    async def strike(self, ctx, user : discord.Member):
        """Strike somebody. 25 strikes bans for 10 seconds."""
        server = ctx.message.server
        if user == server.me:
            await self.bot.say("Don't try to strike me you cunt.")
            return
        if user in self.strikes:
            self.strikes[user] += 1
            if self.strikes[user] >= 25:
                await self.bot.say("```\n{} reached the max strike limit!\n```".format(str(user)))
                self.strikes[user] = 0
                await self.bot.get_cog("Mod").ban_func(server, user, message="Reaching 25 strikes.")
            else:
                await self.bot.say(str(user) + " now has {} strikes.".format(self.strikes[user]))
        else:
            self.strikes[user] = 1
            await self.bot.say(str(user) + " now has {} strike.".format(self.strikes[user]))
        llog = "{} striked {}.".format(str(ctx.message.author), str(user))
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

def setup(bot):
    bot.add_cog(Misc(bot))
