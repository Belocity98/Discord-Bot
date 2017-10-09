import asyncio

from discord.ext import commands
import discord

from .utils.racing import Racing


class Games:

    def __init__(self, bot):
        self.bot = bot

        self.min_racers = 3

        self.custom_emojis = {}

        self.active_race_channels = []
        self.racers = {}

        self.count_high_scores = {}
        self.channel_count = {}
        self.active_count_channels = []

    @commands.command(hidden=True)
    @commands.guild_only()
    async def myhorse(self, ctx, emoji):
        """Changes the emoji for your horse."""

        if not len(emoji) == 1:
            return

        if emoji == '-':
            return

        self.custom_emojis[ctx.author.id] = emoji

        await ctx.message.add_reaction('👌')

    @commands.command()
    @commands.guild_only()
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

    @commands.command()
    @commands.guild_only()
    async def count(self, ctx):
        """Starts a counting game."""

        if ctx.channel.id in self.active_count_channels:
            return

        embed = discord.Embed()
        embed.color = 0x4286f4
        embed.title = f'{ctx.author.name} has started a counting game!'

        await ctx.send(embed=embed)

        self.active_count_channels.append(ctx.channel.id)

    async def on_message(self, message):

        channel = message.channel

        if channel.id not in self.active_count_channels:
            return

        if message.author.bot:
            return

        async def end_game():

            self.active_count_channels.remove(channel.id)

            count = self.channel_count.get(channel.id, 0)
            highscore = self.count_high_scores.get(message.guild.id, 0)

            if count > highscore:
                self.count_high_scores[message.guild.id] = count
                highscore = count

            self.channel_count[channel.id] = 0

            embed = discord.Embed()
            embed.color = 0xfc1500
            embed.title = f'{message.author.name} lost the counting game for everybody!'
            embed.description = f'The current high score for this server is **{highscore}**.'

            if message.guild.id == 183389961016311808:
                await channel.send(embed=embed)

                if count == 0:
                    return

                inv = await message.guild.create_invite(max_uses=1, unique=True)
                await message.author.send(f'You were banned for **{count}** seconds.\n{inv.url}')
                await asyncio.sleep(1)
                await message.author.ban(delete_message_days=0)
                await asyncio.sleep(count)
                await message.author.unban()
                return

            return await channel.send(embed=embed)

        if not message.content.isdigit():
            return await end_game()

        count = self.channel_count.get(channel.id, 0)

        if int(message.content) != count + 1:
            return await end_game()

        self.channel_count[channel.id] = int(message.content)

def setup(bot):
    bot.add_cog(Games(bot))
