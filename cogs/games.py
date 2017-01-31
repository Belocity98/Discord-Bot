import discord
from discord.ext import commands
import random
import asyncio

class Games():

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True)
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
            await self.bot.say("{}'s revolver didn't fire.".format(str(author)))
        llog = "{} played a game of Russian Roulette.".format(str(author))
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @commands.command(pass_context=True, no_pm=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def roll(self, ctx, number : str):
        """Pick a number between 1 and 10. If the number is
        not the same number the bot chose, the user will be banned for a short period of time."""
        roll_chance = self.bot.config["games"]["roll_chance"]
        banlength = self.bot.config["games"]["ban_length"]
        try:
            number = int(number)
        except ValueError:
            embed = discord.Embed(description='A number must be entered.')
            embed.colour = 0x1BE118
            await self.bot.say(embed=embed)
            return

        if (number > roll_chance) or (number < 1):
            embed = discord.Embed(description='The number entered was not between 1 and {}.'.format(roll_chance))
            embed.colour = 0x1BE118
            await self.bot.say(embed=embed)
            return

        server = ctx.message.server
        author = ctx.message.author
        randnumber = random.randint(1, roll_chance)
        if not number == randnumber:
            embed = discord.Embed(description='{} entered the wrong number! The correct number was {}.'.format(author, randnumber))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            await self.bot.get_cog("Mod").ban_func(server, author, message="Number did not match random number. The bot chose {}.".format(randnumber), length=banlength)
        else:
            embed = discord.Embed(description='{} entered the correct number!'.format(author))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)


def setup(bot):
    bot.add_cog(Games(bot))
