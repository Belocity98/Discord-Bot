import discord

from discord.ext import commands
from .utils.racing import Racing

class Games:

    def __init__(self, bot):
        self.bot = bot

        self.min_racers = 3

        self.active_race_channels = []
        self.racers = {}

        self.specialized_emoji = {}

    @commands.group(no_pm=True, invoke_without_command=True)
    async def race(self, ctx):
        """Enters you for a horse race."""

        await ctx.message.delete()

        if ctx.channel.id in self.active_race_channels:
            return

        racers = self.racers.get(ctx.channel.id, [])

        if ctx.author.id not in racers:
            racers.append(ctx.author.id)

        self.racers[ctx.channel.id] = racers

        if not len(racers) >= self.min_racers:
             needed = self.min_racers - len(racers)
             await ctx.send(f'{needed} more racer(s) needed.')
             return

        self.active_race_channels.append(ctx.channel.id)

        user_objs = [discord.utils.get(ctx.guild.members, id=uid) for uid in racers]

        specials = self.specialized_emoji.get(ctx.channel.id, {})
        cars = specials.get('car', [])

        r = Racing(self.bot, message=ctx.message, users=user_objs, race_cars=cars)

        await r.start()
        self.active_race_channels.remove(ctx.channel.id)
        self.racers[ctx.channel.id] = []

    @race.command(name='racecar', hidden=True, no_pm=True)
    async def race_racecar(self, ctx):
        """Changes the horse to a racecar for one race."""

        await ctx.message.delete()

        specials = self.specialized_emoji.get(ctx.channel.id, {})

        for emoji in specials:
            if ctx.author.id in specials[emoji]:
                return

        cars = specials.get('car', [])

        cars.append(ctx.author.id)
        specials['car'] = cars
        self.specialized_emoji[ctx.channel.id] = specials

def setup(bot):
    bot.add_cog(Games(bot))
