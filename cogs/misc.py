import discord
import asyncio
import sys
import os
import logging

from cleverbot import Cleverbot
from discord.ext import commands
from .utils import checks, config
from datetime import datetime, timezone

log = logging.getLogger(__name__)

class Misc():

    def __init__(self, bot):
        self.bot = bot
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        cfgfile = os.path.join(app_path, 'misc.json')
        self.config = config.Config(cfgfile, loop=bot.loop)

        self.cb = Cleverbot('discord-bot')

    async def check_strikes(self, guild, user):
        strikes = self.config.get('strikes', {})
        guild_id = guild.id

        db = strikes.get(guild_id, {})
        strikeamt = int(self.bot.config["strikes"]["amount"])
        banlength = int(self.bot.config["strikes"]["ban_length"])

        if db[user.id] >= strikeamt:
            embed = discord.Embed(description=f'{user.name} reached the max strike limit!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)

            db[user.id] = 0
            strikes[guild_id] = db
            await self.config.put('strikes', strikes)

            await self.bot.get_cog("Mod").ban_func(guild, user, message=f"Reaching {strikeamt} strikes.", length=banlength)

            return True

        return False

    @commands.command(no_pm=True, name='c')
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def cleverbot(self, ctx, *, msg : str):
        """Talk with Cleverbot."""
        try:
            response = self.cb.ask(msg)
            await ctx.channel.send(response)
        except:
            pass

    @commands.command(no_pm=True)
    @commands.has_permissions(manage_roles=True)
    async def maketitle(self, ctx, *, name : str):
        """This command makes a role with no permissions that can be mentioned by anyone."""
        guild = ctx.guild

        for role in guild.roles:
            if role.name.lower() == name.lower():
                embed = discord.Embed(description='A role with that name already exists!')
                embed.colour = 0x1BE118 # lucio green
                await ctx.channel.send(embed=embed)
                return

        permissions = discord.Permissions()
        color = discord.Color(value=0).orange()

        await self.bot.create_role(guild, color=color, name=name, hoist=True, mentionable=True, permissions=permissions)

    @commands.command(no_pm=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def lying(self, ctx, user : discord.Member):
        """Keep record of a lie that someone says."""
        guild = ctx.guild
        author = ctx.author

        lie_channel = discord.utils.find(lambda c: c.name == 'lie-channel', guild.channels)
        if lie_channel == None:
            ctx.channel.send('Lie channel not found.\nCreate a channel called `lie-channel` to enable this feature.')
            return

        def author_check(m):
            return m.author.id == user.id

        embed = discord.Embed(description=f"{user.name} is lying? What are they lying about?\nReply with their lie.")
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)
        lie = await self.bot.wait_for('message', timeout=60, check=author_check)

        embed = discord.Embed(title=f'{user.name} was caught lying!')
        embed.description = f'Exposed by: {author.name}'
        embed.timestamp = ctx.message.timestamp
        embed.add_field(name='Lie', value=lie.content)
        embed.colour = 0x1BE118 # lucio green

        await lie_channel.send(embed=embed)

        embed = discord.Embed(description="Lie logged!")
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

    @commands.group(no_pm=True, invoke_without_command=True)
    @commands.cooldown(1, 5.1, commands.BucketType.user)
    async def strike(self, ctx, user : discord.Member):
        """Strike somebody. 25 strikes bans for 10 seconds."""
        guild = ctx.guild
        author = ctx.author

        strikes = self.config.get('strikes', {})
        guild_id = ctx.guild.id
        db = strikes.get(guild_id, {})

        if user.bot == True:
            embed = discord.Embed(description="Don't try to strike a lowly bot!")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        log.info(f'{author.name} striked {user.name} in {guild.name}.')
        if user.id in db:
            db[user.id] += 1
            strikes[guild_id] = db
            await self.config.put('strikes', strikes)
            strike_check = await self.check_strikes(guild, user)
            if strike_check == False:
                embed = discord.Embed(description=f'{user.name} now has {db[user.id]} strikes.')
                if db[user.id] == 1:
                    embed = discord.Embed(description=f'{user.name} now has 1 strike.')
                embed.colour = 0x1BE118 # lucio green
                await ctx.channel.send(embed=embed)

        else:
            db[user.id] = 1
            strikes[guild_id] = db
            await self.config.put('strikes', strikes)
            embed = discord.Embed(description=f'{user.name} now has {db[user.id]} strike.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)

    @strike.command(name='list')
    async def strike_list(self, ctx, user : discord.Member):
        guild = ctx.guild

        guild_id = guild.id
        strikes = self.config.get('strikes', {})
        db = strikes.get(guild_id, {})

        if user.id not in db:
            embed = discord.Embed(description=f'{user.name} has 0 strikes.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        if int(db[user.id]) == 1:
            embed = discord.Embed(description=f'{user.name} has 1 strike.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        embed = discord.Embed(description=f'{user.name} has {db[user.id]} strikes.')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)
        return

    @strike.command(name='add')
    @commands.has_permissions(ban_members=True)
    async def strike_add(self, ctx, user : discord.Member, amount : int):
        """Add strikes to a user."""
        guild = ctx.guild
        author = ctx.author

        strikes = self.config.get('strikes', {})
        guild_id = ctx.guild.id
        db = strikes.get(guild_id, {})

        if user.bot == True:
            embed = discord.Embed(description="Don't try to strike a lowly bot!")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if amount < 0:
            embed = discord.Embed(description="You can't add negative strikes!")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if user.id in db:
            log.info(f'{author.name} added {amount} strikes to {user.name} in {guild.name}.')
            db[user.id] += amount
            strikes[guild_id] = db
            await self.config.put('strikes', strikes)
            strike_check = await self.check_strikes(guild, user)
            if strike_check == False:
                embed = discord.Embed(description=f'{user.name} now has {db[user.id]} strikes.')
                if db[user.id] == 1:
                    embed = discord.Embed(description=f'{user.name} now has 1 strike.')
                embed.colour = 0x1BE118 # lucio green
                await ctx.channel.send(embed=embed)

        else:
            log.info(f'{author.name} added {amount} strikes to {user.name} in {guild.name}.')
            db[user.id] = amount
            strikes[guild_id] = db
            await self.config.put('strikes', strikes)
            embed = discord.Embed(description=f'{user.name} now has {db[user.id]} strikes.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)

    @strike.command(name='remove')
    @commands.has_permissions(ban_members=True)
    async def strike_remove(self, ctx, user : discord.Member, amount : int):
        """Remove strikes from a user."""
        guild = ctx.guild
        author = ctx.author

        strikes = self.config.get('strikes', {})
        guild_id = ctx.guild.id
        db = strikes.get(guild_id, {})

        if user.bot == True:
            embed = discord.Embed(description="Don't try to strike a lowly bot!")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if amount < 0:
            embed = discord.Embed(description="You can't remove negative strikes!")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return


        if db[user.id] == 0:
            embed = discord.Embed(description='That user has no strikes.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if user.id in db:
            log.info(f'{author.name} removed {amount} strikes from {user.name} in {guild.name}.')
            db[user.id] -= amount
            strikes[guild_id] = db
            await self.config.put('strikes', strikes)
            if db[user.id] < 0:
                db[user.id] = 0
                strikes[guild_id] = db
                await self.config.put('strikes', strikes)
            embed = discord.Embed(description=f'{user.name} now has {db[user.id]} strikes.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)

    @strike.command(name='reset')
    @commands.has_permissions(manage_guild=True)
    async def strike_reset(self, ctx):
        """Resets strikes for a guild."""
        guild = ctx.guild
        author = ctx.author

        strikes = self.config.get('strikes', {})
        guild_id = ctx.guild.id

        db = strikes.get(guild_id, {})
        db = {}
        strikes[guild_id] = db
        await self.config.put('strikes', strikes)

        embed = discord.Embed(description='All strikes in guild reset.')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

        log.info(f'{author.name} reset all strikes in {esrver.name}.')

    @commands.command(no_pm=True)
    async def quote(self, ctx, user : discord.Member, message_id : int=None):
        """Quotes a user. Quotes the last message the user sent in the current channel unless an ID is specified."""

        channel = ctx.channel

        quote = None

        if message_id == None:
            async for message in self.bot.logs_from(ctx.channel):
                if message.author == user:
                    quote = message
                    break

        elif message_id != None:
            quote = await self.bot.get_message(channel, message_id)

        if quote == None:
            embed = discord.Embed(description='Quote not found.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)

            return

        embed = discord.Embed(description=quote.content)
        embed.set_author(name=quote.author.name, icon_url=quote.author.avatar_url)
        embed.timestamp = quote.timestamp
        embed.colour = 0x1BE118 # lucio green

        await ctx.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Misc(bot))
