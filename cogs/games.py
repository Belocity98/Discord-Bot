import discord
from discord.ext import commands
import random
import asyncio

class Games():

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def roulette(self, ctx):
        """Game of Russian Roulette."""
        author = ctx.message.author
        server = ctx.message.server
        randnumber = random.randrange(6)
        if randnumber == 5:
            await self.bot.say("{} found a bullet.".format(str(author)))
            await self.bot.get_cog("Mod").ban_func(server, author, message="Finding a bullet.", length=15)

        else:
            status = "didn't find a bullet."
            await self.bot.say("{}'s revolver didn't fire.".format(str(author)))
        llog = "{} played a game of Russian Roulette.".format(str(author))
        await self.bot.get_cog("Logging").do_logging(llog)

def setup(bot):
    bot.add_cog(Games(bot))
