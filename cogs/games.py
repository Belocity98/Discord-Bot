import discord
import random
import asyncio
import sys
import os
import logging

from discord.ext import commands
from .utils import config

log = logging.getLogger(__name__)

class Games():

    def __init__(self, bot):
        self.bot = bot
        self.duelchance = self.bot.config["games"]["duel_ban_chance"]
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        cfgfile = os.path.join(app_path, 'games.json')
        self.config = config.Config(cfgfile, loop=bot.loop)

        self.currency_name = 'Gems'

        self.roulette_max_currency = 10
        self.roll_max_currency = 60
        self.flip_max_currency = 20
        self.duel_max_currency = 30

        self.lottery_time = 120
        self.lottery_min_amt = 30

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

    async def start_lottery(self, server):
        lottery_status = self.config.get('lottery_status', {})

        lottery_status[server.id] = True
        log.info('Lottery started in {}.'.format(server.name))
        await self.config.put('lottery_status', lottery_status)
        return

    async def stop_lottery(self, server):
        lottery_status = self.config.get('lottery_status', {})

        lottery = self.config.get('lottery', {})
        players = lottery.get(server.id, {})

        players = {}
        lottery[server.id] = players
        lottery_status[server.id] = False
        log.info('Lottery stopped in {}.'.format(server.name))
        await self.config.put('lottery_status', lottery_status)
        await self.config.put('lottery', lottery)
        return

    def lottery_jackpot(self, server):
        lottery = self.config.get('lottery', {})
        players = lottery.get(server.id, {})

        jackpot = 0
        for player in players:
            jackpot += players[player]

        return jackpot

    @commands.group(pass_context=True, no_pm=True, invoke_without_command=True)
    async def lottery(self, ctx):
        """Lottery game. There must be atleast three people for a winner to be drawn after two minutes."""
        server = ctx.message.server

        lottery_status = self.config.get('lottery_status', {})

        if server.id not in lottery_status:
            await self.stop_lottery(server)

        lottery_status = self.config.get('lottery_status', {})

        if lottery_status[server.id] == True:
            embed = discord.Embed(description='There is an ongoing lottery!\nType `>lottery bet <amount>` to enter!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        embed = discord.Embed(description='Started a lottery!\nType `>lottery bet <amount>` to enter!')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

        await self.start_lottery(server)

        await asyncio.sleep(self.lottery_time)

        lottery = self.config.get('lottery', {})
        players = lottery.get(server.id, {})

        if len(players) < 3:
            embed = discord.Embed(description='Not enough players entered the lottery! Returning money...')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            for player in players:
                playerobj = server.get_member(player)
                await self.bot.get_cog("Currency").user_add_currency(server, playerobj, players[player])
            await self.stop_lottery(server)
            return

        winner_id = random.choice(list(players.keys()))
        winner_obj = server.get_member(winner_id)

        jackpot = self.lottery_jackpot(server)

        embed = discord.Embed(description='{} won the total jackpot of {} {}!'.format(winner_obj.name, jackpot, self.currency_name))
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

        await self.bot.get_cog("Currency").user_add_currency(server, winner_obj, jackpot)

        await self.stop_lottery(server)

    @lottery.command(name='bet', pass_context=True, no_pm=True)
    async def lottery_bet(self, ctx, amount : int):
        """Bet in the lottery."""
        server = ctx.message.server
        author = ctx.message.author

        lottery = self.config.get('lottery', {})
        players = lottery.get(server.id, {})

        lottery_status = self.config.get('lottery_status', {})

        if amount < self.lottery_min_amt:
            embed = discord.Embed(description='You must bet atleast {} {} to enter the lottery!'.format(self.lottery_min_amt, self.currency_name))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if amount < 0:
            embed = discord.Embed(description='You cannot bet a negative amount!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if server.id not in lottery_status:
            embed = discord.Embed(description='There is no ongoing lottery!\nType `>lottery` to start a lottery!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if lottery_status[server.id] == False:
            embed = discord.Embed(description='There is no ongoing lottery!\nType `>lottery` to start a lottery!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if await self.bot.get_cog("Currency").user_remove_currency(server, author, amount) == False:
            embed = discord.Embed(description='You cannot afford to bet that much!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if author.id not in players:
            players[author.id] = amount
        else:
            players[author.id] += amount

        lottery[server.id] = players
        await self.config.put('lottery', lottery)

        jackpot = self.lottery_jackpot(server)

        embed = discord.Embed(description='You currently have {} {} in the lottery.\nThe current jackpot is {} {}!'.format(players[author.id], self.currency_name, jackpot, self.currency_name))
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

    @lottery.command(name='forcepayout', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def lottery_forcepayout(self, ctx):
        """Force a payout for the lottery."""
        server = ctx.message.server

        lottery = self.config.get('lottery', {})
        players = lottery.get(server.id, {})

        winner_id = random.choice(list(players.keys()))
        winner_obj = server.get_member(winner_id)

        jackpot = self.lottery_jackpot(server)

        embed = discord.Embed(description='{} won the total jackpot of {} {}!'.format(winner_obj.name, jackpot, self.currency_name))
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

        await self.bot.get_cog("Currency").user_add_currency(server, winner_obj, jackpot)

        await self.stop_lottery(server)

    @lottery.command(name='forcerefund', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def lottery_forcerefund(self, ctx):
        """Force a refund for the lottery."""
        server = ctx.message.server

        lottery = self.config.get('lottery', {})
        players = lottery.get(server.id, {})

        embed = discord.Embed(description='Returning money...')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

        for player in players:
            playerobj = server.get_member(player)
            await self.bot.get_cog("Currency").user_add_currency(server, playerobj, players[player])

        await self.stop_lottery(server)

def setup(bot):
    bot.add_cog(Games(bot))
