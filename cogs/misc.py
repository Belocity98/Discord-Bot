from discord.ext import commands
import discord
import asyncio
import sys, os

from .utils import checks, config

class Misc():

    def __init__(self, bot):
        self.bot = bot
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        cfgfile = os.path.join(app_path, 'misc.json')
        self.config = config.Config(cfgfile, loop=bot.loop)

    async def check_strikes(self, server, user):
        strikes = self.config.get('strikes', {})
        server_id = server.id
        db = strikes.get(server_id, {})
        strikeamt = int(self.bot.config["strikes"]["amount"])
        banlength = int(self.bot.config["strikes"]["ban_length"])
        if db[user.id] >= strikeamt:
            embed = discord.Embed(description='{} reached the max strike limit!'.format(str(user)))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            db[user.id] = 0
            strikes[server_id] = db
            await self.config.put('strikes', strikes)
            await self.bot.get_cog("Mod").ban_func(server, user, message="Reaching {} strikes.".format(strikeamt), length=banlength)
            return True
        return False

    @commands.command(pass_context=True, no_pm=True)
    @commands.cooldown(1, 10, commands.BucketType.server)
    async def lying(self, ctx, user : discord.Member):
        """Keep record of a lie that someone says."""
        server = ctx.message.server
        lie_channel = discord.utils.find(lambda c: c.name == 'lie-channel', server.channels)
        if lie_channel == None:
            print("Lie channel not found. Returning.")
            return
        await self.bot.say("{} is lying? What are they lying about?\nReply with their lie.".format(str(user)))
        lie = await self.bot.wait_for_message(timeout=60, author=ctx.message.author, channel=ctx.message.channel)
        lines = ['```']
        lines.append('{} was caught lying!'.format(str(user)))
        lines.append('Lie: {}\n```'.format(lie.content))
        await self.bot.send_message(lie_channel, '\n'.join(lines))
        await self.bot.say("Lie logged!")

    @commands.group(pass_context=True, no_pm=True, invoke_without_command=True)
    @commands.cooldown(1, 5.1, commands.BucketType.user)
    async def strike(self, ctx, user : discord.Member):
        """Strike somebody. 25 strikes bans for 10 seconds."""
        server = ctx.message.server
        strikes = self.config.get('strikes', {})
        server_id = ctx.message.server.id
        db = strikes.get(server_id, {})

        if user == server.me:
            embed = discord.Embed(description="Don't try to strike me!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if user.id in db:
            db[user.id] += 1
            strikes[server_id] = db
            await self.config.put('strikes', strikes)
            strike_check = await self.check_strikes(server, user)
            if strike_check == False:
                embed = discord.Embed(description='{} now has {} strikes.'.format(str(user), db[user.id]))
                if db[user.id] == 1:
                    embed = discord.Embed(description='{} now has 1 strike.'.format(str(user)))
                embed.colour = 0x1BE118 # lucio green
                await self.bot.say(embed=embed)

        else:
            db[user.id] = 1
            strikes[server_id] = db
            await self.config.put('strikes', strikes)
            embed = discord.Embed(description='{} now has {} strike.'.format(str(user), db[user.id]))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)

        llog = "{} striked {}.".format(str(ctx.message.author), str(user))
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @strike.command(name='list', pass_context=True)
    async def strike_list(self, ctx, user : discord.Member):
        server = ctx.message.server
        server_id = server.id
        strikes = self.config.get('strikes', {})
        db = strikes.get(server_id, {})
        if user.id not in db:
            embed = discord.Embed(description='{} has 0 strikes.'.format(str(user)))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        if int(db[user.id]) == 1:
            embed = discord.Embed(description='{} has 1 strike.'.format(str(user)))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        embed = discord.Embed(description='{} has {} strikes.'.format(str(user), db[user.id]))
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)
        return

    @strike.command(name='add', pass_context=True)
    @commands.has_permissions(ban_members=True)
    async def strike_add(self, ctx, user : discord.Member, amount : int):
        """Add strikes to a user."""
        server = ctx.message.server
        strikes = self.config.get('strikes', {})
        server_id = ctx.message.server.id
        db = strikes.get(server_id, {})

        if user == server.me:
            embed = discord.Embed(description="Don't try to strike me!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if amount < 0:
            embed = discord.Embed(description="You can't add negative strikes!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if user.id in db:
            db[user.id] += amount
            strikes[server_id] = db
            await self.config.put('strikes', strikes)
            strike_check = await self.check_strikes(server, user)
            if strike_check == False:
                embed = discord.Embed(description='{} now has {} strikes.'.format(str(user), db[user.id]))
                if db[user.id] == 1:
                    embed = discord.Embed(description='{} now has 1 strike.'.format(str(user)))
                embed.colour = 0x1BE118 # lucio green
                await self.bot.say(embed=embed)

        else:
            db[user.id] = amount
            strikes[server_id] = db
            await self.config.put('strikes', strikes)
            embed = discord.Embed(description='{} now has {} strikes.'.format(str(user), db[user.id]))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
        llog = "{} added {} strikes to {}.".format(str(ctx.message.author), amount, str(user))
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @strike.command(name='remove', pass_context=True)
    @commands.has_permissions(ban_members=True)
    async def strike_remove(self, ctx, user : discord.Member, amount : int):
        """Remove strikes from a user."""
        server = ctx.message.server
        strikes = self.config.get('strikes', {})
        server_id = ctx.message.server.id
        db = strikes.get(server_id, {})

        if user == server.me:
            embed = discord.Embed(description="Don't try to strike me!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)

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
            db[user.id] -= amount
            strikes[server_id] = db
            await self.config.put('strikes', strikes)
            if db[user.id] < 0:
                db[user.id] = 0
                strikes[server_id] = db
                await self.config.put('strikes', strikes)
            embed = discord.Embed(description='{} now has {} strikes.'.format(str(user), db[user.id]))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
        llog = "{} removed {} strikes from {}.".format(str(ctx.message.author), amount, str(user))
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @strike.command(name='reset', pass_context=True)
    @commands.has_permissions(manage_server=True)
    async def strike_reset(self, ctx):
        """Resets strikes for a server."""
        server = ctx.message.server
        strikes = self.config.get('strikes', {})
        server_id = ctx.message.server.id
        db = strikes.get(server_id, {})
        db = {}
        strikes[server_id] = db
        await self.config.put('strikes', strikes)
        embed = discord.Embed(description='All strikes in server reset.')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)
        llog = "{} reset all strikes in {}.".format(str(ctx.message.author), server.name)
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

def setup(bot):
    bot.add_cog(Misc(bot))
