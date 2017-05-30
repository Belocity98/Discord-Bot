import discord

from discord.ext import commands
from .utils.racing import Racing
from .utils import checks


class Games:

    def __init__(self, bot):
        self.bot = bot

        self.min_racers = 3

        self.fast_racers = []

        self.active_race_channels = []
        self.racers = {}

    @commands.command(no_pm=True)
    @checks.is_owner()
    async def fastracer(self, ctx, user : discord.Member):
        """Toggles whether a person is a fast racer or not."""

        if user.id in self.fast_racers:
            self.fast_racers.remove(user.id)
        else:
            self.fast_racers.append(user.id)

        await ctx.send('👌')

    @commands.command(no_pm=True)
    async def race(self, ctx):
        """Enters you for a horse race."""

        try:
            await ctx.message.delete()
        except:
            pass  # couldn't delete user's message

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

        r = Racing(self.bot, message=ctx.message, users=user_objs, fast_peeps=self.fast_racers)

        await r.start()
        self.active_race_channels.remove(ctx.channel.id)
        self.racers[ctx.channel.id] = []


def setup(bot):
    bot.add_cog(Games(bot))
