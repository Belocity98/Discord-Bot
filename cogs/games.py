import discord
import random
import asyncio
import sys
import os

from discord.ext import commands
from .utils import config

class Games():

    def __init__(self, bot):
        self.bot = bot
        self.duelchance = self.bot.config["games"]["duel_ban_chance"]
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        cfgfile = os.path.join(app_path, 'games.json')
        self.config = config.Config(cfgfile, loop=bot.loop)

        self.roulette_max_currency = 30
        self.roll_max_currency = 60
        self.flip_max_currency = 20
        self.duel_max_currency = 30

    @commands.command(pass_context=True, no_pm=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def roulette(self, ctx):
        """Game of Russian Roulette."""
        author = ctx.message.author
        server = ctx.message.server
        pot_winning = random.randint(1, self.roulette_max_currency)
        randnumber = random.randrange(6)
        if randnumber == 5:
            await self.bot.say("{} found a bullet.".format(str(author)))
            await self.bot.get_cog("Mod").ban_func(server, author, message="Finding a bullet.", length=15)

        else:
            await self.bot.say("{}'s revolver didn't fire.".format(str(author)))
            await self.bot.get_cog("Currency").user_add_currency(server, author, pot_winning)

    @commands.command(pass_context=True, no_pm=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def roll(self, ctx, number : str):
        """Pick a number between 1 and 10. If the number is
        not the same number the bot chose, the user will be
         banned for a short period of time."""
        roll_chance = self.bot.config["games"]["roll_chance"]
        banlength = self.bot.config["games"]["roll_ban_length"]
        pot_winning = random.randint(1, self.roll_max_currency)
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
            await self.bot.get_cog("Currency").user_add_currency(server, author, pot_winning)

    @commands.command(pass_context=True, no_pm=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def flip(self, ctx):
        """50 percent chance of being banned for a short period of time."""
        pot_winning = random.randint(1, self.flip_max_currency)
        banlength = self.bot.config["games"]["flip_ban_length"]
        author = ctx.message.author
        server = ctx.message.server
        randnumber = random.randint(1, 2)

        if randnumber == 1:
            embed = discord.Embed(description='{} flipped poorly.'.format(author))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            await self.bot.get_cog("Mod").ban_func(server, author, message="Flipped poorly.", length=banlength)
        else:
            embed = discord.Embed(description='{} flipped correctly.'.format(author))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            await self.bot.get_cog("Currency").user_add_currency(server, author, pot_winning)

    def duel_check(self, msg):
        yes_list = [
            "yes",
            "y",
            "yup",
            "ok",
            "yeah",
            "sure",
            "yea",
            "affirmative",
            "by all means",
            "okey-dokey",
            "roger",
            "fo' shizzle",
            "totally"
        ]
        if any(msg.content.lower() in s for s in yes_list):
            return True
        else:
            return False

    def duel_check_valid_int(self, msg):
        try:
            msg = int(msg.content)
        except ValueError:
            return False
        if (msg > self.duelchance) or (msg < 1):
            return False
        return True

    @commands.group(pass_context=True, no_pm=True,invoke_without_command=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def duel(self, ctx, user : discord.Member):
        """Duel another user. Loser is banned for a short period of time."""
        pot_winning = random.randint(1, self.duel_max_currency)
        duelchance = self.duelchance
        banlength = self.bot.config["games"]["duel_ban_length"]
        current_duels = self.config.get('current_duels', {})

        challenger = ctx.message.author
        being_attacked = user
        server = ctx.message.server
        server_id = server.id
        db = current_duels.get(server_id, {})

        if being_attacked.status == 'offline':
            embed = discord.Embed(description="You cannot start a duel with an offline user!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if being_attacked == server.me:
            embed = discord.Embed(description="You cannot start a duel with a bot!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if challenger.id == user.id:
            embed = discord.Embed(description="You cannot duel yourself!")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if (challenger.id in db) and (being_attacked.id in db):
            if (db[challenger.id] == True) or (db[being_attacked.id] == True):
                embed = discord.Embed(description="You cannot start a duel while you or your target are currently dueling!")
                embed.colour = 0x1BE118 # lucio green
                await self.bot.say(embed=embed)
                return

        db[challenger.id] = True
        db[being_attacked.id] = True
        current_duels[server_id] = db
        await self.config.put('current_duels', current_duels)

        embed = discord.Embed(description="{}, do you accept {}'s duel challenge? (yes/no)".format(being_attacked, challenger))
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)
        msg = await self.bot.wait_for_message(timeout=45, author=being_attacked)
        if msg == None:
            embed = discord.Embed(description="{} didn't respond to the duel challenge.".format(being_attacked))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            current_duels = self.config.get('current_duels', {})
            db = current_duels.get(server_id, {})
            db[challenger.id] = False
            db[being_attacked.id] = False
            current_duels[server_id] = db
            await self.config.put('current_duels', current_duels)
            return

        if not self.duel_check(msg):
            embed = discord.Embed(description='{} did not accept the duel challenge.'.format(being_attacked))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            current_duels = self.config.get('current_duels', {})
            db = current_duels.get(server_id, {})
            db[challenger.id] = False
            db[being_attacked.id] = False
            current_duels[server_id] = db
            await self.config.put('current_duels', current_duels)
            return

        embed = discord.Embed(description='{} accepted the duel challenge!\n{}, pick a number between 1 and {}.'.format(being_attacked, challenger, duelchance))
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

        challenger_number = await self.bot.wait_for_message(timeout=45, author=challenger, check=self.duel_check_valid_int)
        if challenger_number == None:
            embed = discord.Embed(description="{} didn't choose a number. Ending duel.".format(challenger))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            current_duels = self.config.get('current_duels', {})
            db = current_duels.get(server_id, {})
            db[challenger.id] = False
            db[being_attacked.id] = False
            current_duels[server_id] = db
            await self.config.put('current_duels', current_duels)
            return

        embed = discord.Embed(description='{}, pick a number between 1 and {}.'.format(being_attacked, duelchance))
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

        while True:
            being_attacked_number = await self.bot.wait_for_message(timeout=45, author=being_attacked, check=self.duel_check_valid_int)
            if challenger_number.content == being_attacked_number.content:
                embed = discord.Embed(description="Number cannot be the same as opponent's number. Please re-enter your number.")
                embed.colour = 0x1BE118 # lucio green
                await self.bot.say(embed=embed)
                continue
            else:
                break

        if being_attacked_number == None:
            embed = discord.Embed(description="{} didn't choose a number. Ending duel.".format(being_attacked))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            current_duels = self.config.get('current_duels', {})
            db = current_duels.get(server_id, {})
            db[challenger.id] = False
            db[being_attacked.id] = False
            current_duels[server_id] = db
            await self.config.put('current_duels', current_duels)
            return

        randnumber = random.randint(1, duelchance)
        challenger_distance = abs(randnumber - int(challenger_number.content))
        being_attacked_distance = abs(randnumber - int(being_attacked_number.content))

        current_duels = self.config.get('current_duels', {})
        db = current_duels.get(server_id, {})
        db[challenger.id] = False
        db[being_attacked.id] = False
        current_duels[server_id] = db
        await self.config.put('current_duels', current_duels)

        if challenger_distance < being_attacked_distance:
            embed = discord.Embed(title='{} won!'.format(challenger))
            embed.description = 'The random number was {}.'.format(randnumber)
            embed.add_field(name="{}'s Distance".format(challenger), value=challenger_distance)
            embed.add_field(name="{}'s Distance".format(being_attacked), value=being_attacked_distance, inline=False)
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            await self.bot.get_cog("Currency").user_add_currency(server, challenger, pot_winning)
            await self.bot.get_cog("Mod").ban_func(server, being_attacked, message="Lost a duel to {}.".format(challenger), length=banlength)
            return
        elif challenger_distance == being_attacked_distance:
            embed = discord.Embed(title='There was a draw.')
            embed.description = 'The random number was {}.'.format(randnumber)
            embed.add_field(name="{}'s Distance".format(challenger), value=challenger_distance)
            embed.add_field(name="{}'s Distance".format(being_attacked), value=being_attacked_distance, inline=False)
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        else:
            embed = discord.Embed(title='{} won!'.format(being_attacked))
            embed.description = 'The random number was {}.'.format(randnumber)
            embed.add_field(name="{}'s Distance".format(challenger), value=challenger_distance)
            embed.add_field(name="{}'s Distance".format(being_attacked), value=being_attacked_distance, inline=False)
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            await self.bot.get_cog("Currency").user_add_currency(server, being_attacked, pot_winning)
            await self.bot.get_cog("Mod").ban_func(server, challenger, message="Lost a duel to {}.".format(being_attacked), length=banlength)
            return
    @duel.command(name='resetstatus', pass_context=True)
    async def duel_resetstatus(self, ctx):
        server_id = ctx.message.server.id
        current_duels = self.config.get('current_duels', {})
        db = current_duels.get(server_id, {})
        db = {}
        current_duels[server_id] = db
        await self.config.put('current_duels', current_duels)
        embed = discord.Embed(description='Duel status reset in server.')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

def setup(bot):
    bot.add_cog(Games(bot))
