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

    async def check_strikes(self, server, user):
        strikes = self.config.get('strikes', {})
        server_id = server.id

        db = strikes.get(server_id, {})
        strikeamt = int(self.bot.config["strikes"]["amount"])
        banlength = int(self.bot.config["strikes"]["ban_length"])

        if db[user.id] >= strikeamt:
            embed = discord.Embed(description=f'{user.name} reached the max strike limit!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)

            db[user.id] = 0
            strikes[server_id] = db
            await self.config.put('strikes', strikes)

            await self.bot.get_cog("Mod").ban_func(server, user, message=f"Reaching {strikeamt} strikes.", length=banlength)
            
            return True

        return False

    @commands.command(pass_context=True, no_pm=True, name='c')
    @commands.cooldown(1, 3, commands.BucketType.server)
    async def cleverbot(self, ctx, *, msg : str):
        """Talk with Cleverbot."""
        try:
            response = self.cb.ask(msg)
            await self.bot.say(response)
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_roles=True)
    async def maketitle(self, ctx, *, name : str):
        """This command makes a role with no permissions that can be mentioned by anyone."""
        server = ctx.message.server

        for role in server.roles:
            if role.name.lower() == name.lower():
                embed = discord.Embed(description='A role with that name already exists!')
                embed.colour = 0x1BE118 # lucio green
                await self.bot.say(embed=embed)
                return

        permissions = discord.Permissions()
        color = discord.Color(value=0).orange()

        await self.bot.create_role(server, color=color, name=name, hoist=True, mentionable=True, permissions=permissions)

    @commands.command(pass_context=True, no_pm=True)
    @commands.cooldown(1, 10, commands.BucketType.server)
    async def lying(self, ctx, user : discord.Member):
        """Keep record of a lie that someone says."""
        server = ctx.message.server
        author = ctx.message.author

        lie_channel = discord.utils.find(lambda c: c.name == 'lie-channel', server.channels)
        if lie_channel == None:
            print("Lie channel not found. Returning.")
            return

        embed = discord.Embed(description=f"{user.name} is lying? What are they lying about?\nReply with their lie.")
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)
        lie = await self.bot.wait_for_message(timeout=60, author=ctx.message.author, channel=ctx.message.channel)

        embed = discord.Embed(title=f'{user.name} was caught lying!')
        embed.description = f'Exposed by: {author.name}'
        embed.timestamp = ctx.message.timestamp
        embed.add_field(name='Lie', value=lie.content)
        embed.colour = 0x1BE118 # lucio green

        await self.bot.send_message(lie_channel, embed=embed)

        embed = discord.Embed(description="Lie logged!")
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

    @commands.group(pass_context=True, no_pm=True, invoke_without_command=True)
    @commands.cooldown(1, 5.1, commands.BucketType.user)
    async def strike(self, ctx, user : discord.Member):
        """Strike somebody. 25 strikes bans for 10 seconds."""
        server = ctx.message.server
        author = ctx.message.author

        strikes = self.config.get('strikes', {})
        server_id = ctx.message.server.id
        db = strikes.get(server_id, {})

        if user.bot == True:
            embed = discord.Embed(description="Don't try to strike a lowly bot!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        log.info(f'{author.name} striked {user.name} in {server.name}.')
        if user.id in db:
            db[user.id] += 1
            strikes[server_id] = db
            await self.config.put('strikes', strikes)
            strike_check = await self.check_strikes(server, user)
            if strike_check == False:
                embed = discord.Embed(description=f'{user.name} now has {db[user.id]} strikes.')
                if db[user.id] == 1:
                    embed = discord.Embed(description=f'{user.name} now has 1 strike.')
                embed.colour = 0x1BE118 # lucio green
                await self.bot.say(embed=embed)

        else:
            db[user.id] = 1
            strikes[server_id] = db
            await self.config.put('strikes', strikes)
            embed = discord.Embed(description=f'{user.name} now has {db[user.id]} strike.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)

    @strike.command(name='list', pass_context=True)
    async def strike_list(self, ctx, user : discord.Member):
        server = ctx.message.server\

        server_id = server.id
        strikes = self.config.get('strikes', {})
        db = strikes.get(server_id, {})

        if user.id not in db:
            embed = discord.Embed(description=f'{user.name} has 0 strikes.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        if int(db[user.id]) == 1:
            embed = discord.Embed(description=f'{user.name} has 1 strike.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        embed = discord.Embed(description=f'{user.name} has {db[user.id]} strikes.')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)
        return

    @strike.command(name='add', pass_context=True)
    @commands.has_permissions(ban_members=True)
    async def strike_add(self, ctx, user : discord.Member, amount : int):
        """Add strikes to a user."""
        server = ctx.message.server
        author = ctx.message.author

        strikes = self.config.get('strikes', {})
        server_id = ctx.message.server.id
        db = strikes.get(server_id, {})

        if user.bot == True:
            embed = discord.Embed(description="Don't try to strike a lowly bot!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if amount < 0:
            embed = discord.Embed(description="You can't add negative strikes!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if user.id in db:
            log.info(f'{author.name} added {amount} strikes to {user.name} in {server.name}.')
            db[user.id] += amount
            strikes[server_id] = db
            await self.config.put('strikes', strikes)
            strike_check = await self.check_strikes(server, user)
            if strike_check == False:
                embed = discord.Embed(description=f'{user.name} now has {db[user.id]} strikes.')
                if db[user.id] == 1:
                    embed = discord.Embed(description=f'{user.name} now has 1 strike.')
                embed.colour = 0x1BE118 # lucio green
                await self.bot.say(embed=embed)

        else:
            log.info(f'{author.name} added {amount} strikes to {user.name} in {server.name}.')
            db[user.id] = amount
            strikes[server_id] = db
            await self.config.put('strikes', strikes)
            embed = discord.Embed(description=f'{user.name} now has {db[user.id]} strikes.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)

    @strike.command(name='remove', pass_context=True)
    @commands.has_permissions(ban_members=True)
    async def strike_remove(self, ctx, user : discord.Member, amount : int):
        """Remove strikes from a user."""
        server = ctx.message.server
        author = ctx.message.author

        strikes = self.config.get('strikes', {})
        server_id = ctx.message.server.id
        db = strikes.get(server_id, {})

        if user.bot == True:
            embed = discord.Embed(description="Don't try to strike a lowly bot!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if amount < 0:
            embed = discord.Embed(description="You can't remove negative strikes!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return


        if db[user.id] == 0:
            embed = discord.Embed(description='That user has no strikes.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if user.id in db:
            log.info(f'{author.name} removed {amount} strikes from {user.name} in {server.name}.')
            db[user.id] -= amount
            strikes[server_id] = db
            await self.config.put('strikes', strikes)
            if db[user.id] < 0:
                db[user.id] = 0
                strikes[server_id] = db
                await self.config.put('strikes', strikes)
            embed = discord.Embed(description=f'{user.name} now has {db[user.id]} strikes.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)

    @strike.command(name='reset', pass_context=True)
    @commands.has_permissions(manage_server=True)
    async def strike_reset(self, ctx):
        """Resets strikes for a server."""
        server = ctx.message.server
        author = ctx.message.author

        strikes = self.config.get('strikes', {})
        server_id = ctx.message.server.id

        db = strikes.get(server_id, {})
        db = {}
        strikes[server_id] = db
        await self.config.put('strikes', strikes)

        embed = discord.Embed(description='All strikes in server reset.')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

        log.info(f'{author.name} reset all strikes in {esrver.name}.')

    @commands.command(pass_context=True, no_pm=True)
    async def quote(self, ctx, user : discord.Member, message_id : int=None):
        """Quotes a user. Quotes the last message the user sent in the current channel unless an ID is specified."""

        channel = ctx.message.channel

        quote = None

        if message_id == None:
            async for message in self.bot.logs_from(ctx.message.channel):
                if message.author == user:
                    quote = message
                    break

        elif message_id != None:
            quote = await self.bot.get_message(channel, message_id)

        if quote == None:
            embed = discord.Embed(description='Quote not found.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)

            return

        embed = discord.Embed(description=quote.content)
        embed.set_author(name=quote.author.name, icon_url=quote.author.avatar_url)
        embed.timestamp = quote.timestamp
        embed.colour = 0x1BE118 # lucio green

        await self.bot.say(embed=embed)

def setup(bot):
    bot.add_cog(Misc(bot))
