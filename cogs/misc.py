from discord.ext import commands
import discord
import asyncio

from .utils import checks

class Misc():

    def __init__(self, bot):
        self.bot = bot
        self.strikes = {}

    async def check_strikes(self, server, user):
        strikeamt = int(self.bot.config["strikes"]["amount"])
        banlength = int(self.bot.config["strikes"]["ban_length"])
        if self.strikes[user] >= strikeamt:
            embed = discord.Embed(description='{} reached the max strike limit!'.format(str(user)))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            self.strikes[user] = 0
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
        if user == server.me:
            embed = discord.Embed(description="Don't try to strike me!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        if user in self.strikes:
            self.strikes[user] += 1
            strike_check = await self.check_strikes(server, user)
            if strike_check == False:
                embed = discord.Embed(description='{} now has {} strikes.'.format(str(user), self.strikes[user]))
                if self.strikes[user] == 1:
                    embed = discord.Embed(description='{} now has 1 strike.'.format(str(user)))
                embed.colour = 0x1BE118 # lucio green
                await self.bot.say(embed=embed)
        else:
            self.strikes[user] = 1
            embed = discord.Embed(description='{} now has {} strike.'.format(str(user), self.strikes[user]))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
        llog = "{} striked {}.".format(str(ctx.message.author), str(user))
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @strike.command(name='add', pass_context=True)
    @commands.has_permissions(ban_members=True)
    async def strike_add(self, ctx, user : discord.Member, amount : int):
        """Add strikes to a user."""
        server = ctx.message.server
        if user == server.me:
            embed = discord.Embed(description="Don't try to strike me!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        if user in self.strikes:
            self.strikes[user] += amount
            strike_check = await self.check_strikes(server, user)
            if strike_check == False:
                embed = discord.Embed(description='{} now has {} strikes.'.format(str(user), self.strikes[user]))
                if self.strikes[user] == 1:
                    embed = discord.Embed(description='{} now has 1 strike.'.format(str(user)))
                embed.colour = 0x1BE118 # lucio green
                await self.bot.say(embed=embed)
        else:
            self.strikes[user] = amount
            embed = discord.Embed(description='{} now has {} strikes.'.format(str(user), self.strikes[user]))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
        llog = "{} added {} strikes to {}.".format(str(ctx.message.author), amount, str(user))
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @strike.command(name='remove', pass_context=True)
    @commands.has_permissions(ban_members=True)
    async def strike_remove(self, ctx, user : discord.Member, amount : int):
        """Remove strikes from a user."""
        server = ctx.message.server
        if user == server.me:
            embed = discord.Embed(description="Don't try to strike me!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
        if self.strikes[user] == 0:
            embed = discord.Embed(description='That user has no strikes.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        if user in self.strikes:
            self.strikes[user] -= amount
            if self.strikes[user] < 0:
                self.strikes[user] = 0
            embed = discord.Embed(description='{} now has {} strikes.'.format(str(user), self.strikes[user]))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
        llog = "{} removed {} strikes from {}.".format(str(ctx.message.author), amount, str(user))
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

def setup(bot):
    bot.add_cog(Misc(bot))
