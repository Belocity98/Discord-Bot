import discord

from discord.ext import commands
from .utils.racing import Racing


class Games:

    def __init__(self, bot):
        self.bot = bot

        self.min_racers = 3

        self.custom_emojis = {}

        self.active_race_channels = []
        self.racers = {}

    @commands.command(no_pm=True)
    async def myhorse(self, ctx, emoji):
        """Changes the emoji for your horse."""

        if not len(emoji) == 1:
            return

        if emoji == '-':
            return

        self.custom_emojis[ctx.author.id] = emoji

        await ctx.send('👌')

    @commands.command(no_pm=True)
    async def race(self, ctx):
        """Enters you for a horse race."""

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

        r = Racing(self.bot, message=ctx.message, users=user_objs, custom_emojis=self.custom_emojis)

        await r.start()
        self.active_race_channels.remove(ctx.channel.id)
        self.racers[ctx.channel.id] = []


def setup(bot):
    bot.add_cog(Games(bot))
