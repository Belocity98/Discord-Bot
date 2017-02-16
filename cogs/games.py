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

    @commands.command(no_pm=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def roulette(self, ctx):
        """Game of Russian Roulette."""
        author = ctx.author
        guild = ctx.guild
        pot_winning = random.randint(1, self.roulette_max_currency)
        randnumber = random.randrange(6)
        if randnumber == 5:
            await ctx.channel.send(f'{author.name} found a bullet.')
            await self.bot.get_cog("Mod").ban_func(guild, author, message="Finding a bullet.", length=15)

        else:
            await ctx.channel.send(f"{author.name}'s revolver didn't fire.")
            await self.bot.get_cog("Currency").user_add_currency(guild, author, pot_winning)

    @commands.command(no_pm=True)
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
            await ctx.channel.send(embed=embed)
            return

        if (number > roll_chance) or (number < 1):
            embed = discord.Embed(description=f'The number entered was not between 1 and {roll_chance}.')
            embed.colour = 0x1BE118
            await ctx.channel.send(embed=embed)
            return

        guild = ctx.guild
        author = ctx.author
        randnumber = random.randint(1, roll_chance)
        if not number == randnumber:
            embed = discord.Embed(description=f'{author.name} entered the wrong number! The correct number was {randnumber}.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            await self.bot.get_cog("Mod").ban_func(guild, author, message=f"Number did not match random number. The bot chose {randnumber}.", length=banlength)
        else:
            embed = discord.Embed(description=f'{author.name} entered the correct number!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            await self.bot.get_cog("Currency").user_add_currency(guild, author, pot_winning)

    @commands.command(no_pm=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def flip(self, ctx):
        """50 percent chance of being banned for a short period of time."""
        pot_winning = random.randint(1, self.flip_max_currency)
        banlength = self.bot.config["games"]["flip_ban_length"]
        author = ctx.author
        guild = ctx.guild
        randnumber = random.randint(1, 2)

        if randnumber == 1:
            embed = discord.Embed(description=f'{author.name} flipped poorly.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            await self.bot.get_cog("Mod").ban_func(guild, author, message="Flipped poorly.", length=banlength)
        else:
            embed = discord.Embed(description=f'{author.name} flipped correctly.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            await self.bot.get_cog("Currency").user_add_currency(guild, author, pot_winning)

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

    @commands.group(no_pm=True,invoke_without_command=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def duel(self, ctx, user : discord.Member):
        """Duel another user. Loser is banned for a short period of time."""
        pot_winning = random.randint(1, self.duel_max_currency)
        duelchance = self.duelchance
        banlength = self.bot.config["games"]["duel_ban_length"]
        current_duels = self.config.get('current_duels', {})

        challenger = ctx.author
        being_attacked = user
        guild = ctx.guild
        guild_id = guild.id
        db = current_duels.get(guild_id, {})

        if being_attacked.status == 'offline':
            embed = discord.Embed(description="You cannot start a duel with an offline user!")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if being_attacked == guild.me:
            embed = discord.Embed(description="You cannot start a duel with a bot!")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if challenger.id == user.id:
            embed = discord.Embed(description="You cannot duel yourself!")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if (challenger.id in db) and (being_attacked.id in db):
            if (db[challenger.id] == True) or (db[being_attacked.id] == True):
                embed = discord.Embed(description="You cannot start a duel while you or your target are currently dueling!")
                embed.colour = 0x1BE118 # lucio green
                await ctx.channel.send(embed=embed)
                return

        db[challenger.id] = True
        db[being_attacked.id] = True
        current_duels[guild_id] = db
        await self.config.put('current_duels', current_duels)

        embed = discord.Embed(description=f"{being_attacked.name}, do you accept {challenger.name}'s duel challenge? (yes/no)")
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)
        msg = await self.bot.wait_for('message', timeout=45, author=being_attacked)
        if msg == None:
            embed = discord.Embed(description=f"{being_attacked.name} didn't respond to the duel challenge.")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            current_duels = self.config.get('current_duels', {})
            db = current_duels.get(guild_id, {})
            db[challenger.id] = False
            db[being_attacked.id] = False
            current_duels[guild_id] = db
            await self.config.put('current_duels', current_duels)
            return

        if not self.duel_check(msg):
            embed = discord.Embed(description=f'{being_attacked.name} did not accept the duel challenge.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            current_duels = self.config.get('current_duels', {})
            db = current_duels.get(guild_id, {})
            db[challenger.id] = False
            db[being_attacked.id] = False
            current_duels[guild_id] = db
            await self.config.put('current_duels', current_duels)
            return

        embed = discord.Embed(description=f'{being_attacked.name} accepted the duel challenge!\n{challenger.name}, pick a number between 1 and {duelchance}.')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

        challenger_number = await self.bot.wait_for('message', timeout=45, author=challenger, check=self.duel_check_valid_int)
        if challenger_number == None:
            embed = discord.Embed(description=f"{challenger.name} didn't choose a number. Ending duel.")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            current_duels = self.config.get('current_duels', {})
            db = current_duels.get(guild_id, {})
            db[challenger.id] = False
            db[being_attacked.id] = False
            current_duels[guild_id] = db
            await self.config.put('current_duels', current_duels)
            return

        embed = discord.Embed(description=f'{being_attacked.name}, pick a number between 1 and {duelchance}.')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

        while True:
            being_attacked_number = await self.bot.wait_for('message', timeout=45, author=being_attacked, check=self.duel_check_valid_int)
            if challenger_number.content == being_attacked_number.content:
                embed = discord.Embed(description="Number cannot be the same as opponent's number. Please re-enter your number.")
                embed.colour = 0x1BE118 # lucio green
                await ctx.channel.send(embed=embed)
                continue
            else:
                break

        if being_attacked_number == None:
            embed = discord.Embed(description=f"{being_attacked.name} didn't choose a number. Ending duel.")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            current_duels = self.config.get('current_duels', {})
            db = current_duels.get(guild_id, {})
            db[challenger.id] = False
            db[being_attacked.id] = False
            current_duels[guild_id] = db
            await self.config.put('current_duels', current_duels)
            return

        randnumber = random.randint(1, duelchance)
        challenger_distance = abs(randnumber - int(challenger_number.content))
        being_attacked_distance = abs(randnumber - int(being_attacked_number.content))

        current_duels = self.config.get('current_duels', {})
        db = current_duels.get(guild_id, {})
        db[challenger.id] = False
        db[being_attacked.id] = False
        current_duels[guild_id] = db
        await self.config.put('current_duels', current_duels)

        if challenger_distance < being_attacked_distance:
            embed = discord.Embed(title=f'{challenger.name} won!')
            embed.description = f'The random number was {randnumber}.'
            embed.add_field(name=f"{challenger.name}'s Distance", value=challenger_distance)
            embed.add_field(name=f"{being_attacked.name}'s Distance", value=being_attacked_distance, inline=False)
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            await self.bot.get_cog("Currency").user_add_currency(guild, challenger, pot_winning)
            await self.bot.get_cog("Mod").ban_func(guild, being_attacked, message=f"Lost a duel to {challenger.name}.", length=banlength)
            return
        elif challenger_distance == being_attacked_distance:
            embed = discord.Embed(title='There was a draw.')
            embed.description = f'The random number was {randnumber}.'
            embed.add_field(name=f"{challenger.name}'s Distance", value=challenger_distance)
            embed.add_field(name=f"{being_attacked.name}'s Distance", value=being_attacked_distance, inline=False)
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        else:
            embed = discord.Embed(title=f'{being_attacked.name} won!')
            embed.description = f'The random number was {randnumber}.'
            embed.add_field(name=f"{challenger.name}'s Distance", value=challenger_distance)
            embed.add_field(name=f"{being_attacked.name}'s Distance", value=being_attacked_distance, inline=False)
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            await self.bot.get_cog("Currency").user_add_currency(guild, being_attacked, pot_winning)
            await self.bot.get_cog("Mod").ban_func(guild, challenger, message=f"Lost a duel to {being_attacked.name}.", length=banlength)
            return
    @duel.command(name='resetstatus')
    async def duel_resetstatus(self, ctx):
        guild_id = ctx.guild.id
        current_duels = self.config.get('current_duels', {})
        db = current_duels.get(guild_id, {})
        db = {}
        current_duels[guild_id] = db
        await self.config.put('current_duels', current_duels)
        embed = discord.Embed(description='Duel status reset in guild.')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

    async def start_lottery(self, guild):
        lottery_status = self.config.get('lottery_status', {})

        lottery_status[guild.id] = True
        log.info(f'Lottery started in {guild.name}.')
        await self.config.put('lottery_status', lottery_status)
        return

    async def stop_lottery(self, guild):
        lottery_status = self.config.get('lottery_status', {})

        lottery = self.config.get('lottery', {})
        players = lottery.get(guild.id, {})

        players = {}
        lottery[guild.id] = players
        lottery_status[guild.id] = False
        log.info(f'Lottery stopped in {guild.name}.')
        await self.config.put('lottery_status', lottery_status)
        await self.config.put('lottery', lottery)
        return

    def lottery_jackpot(self, guild):
        lottery = self.config.get('lottery', {})
        players = lottery.get(guild.id, {})

        jackpot = 0
        for player in players:
            jackpot += players[player]

        return jackpot

    @commands.group(no_pm=True, invoke_without_command=True)
    async def lottery(self, ctx):
        """Lottery game. There must be atleast three people for a winner to be drawn after two minutes."""
        guild = ctx.guild

        lottery_status = self.config.get('lottery_status', {})

        if guild.id not in lottery_status:
            await self.stop_lottery(guild)

        lottery_status = self.config.get('lottery_status', {})

        if lottery_status[guild.id] == True:
            embed = discord.Embed(description='There is an ongoing lottery!\nType `>lottery bet <amount>` to enter!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        embed = discord.Embed(description='Started a lottery!\nType `>lottery bet <amount>` to enter!')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

        await self.start_lottery(guild)

        await asyncio.sleep(self.lottery_time)

        lottery = self.config.get('lottery', {})
        players = lottery.get(guild.id, {})

        if len(players) < 3:
            embed = discord.Embed(description='Not enough players entered the lottery! Returning money...')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            for player in players:
                playerobj = guild.get_member(player)
                await self.bot.get_cog("Currency").user_add_currency(guild, playerobj, players[player])
            await self.stop_lottery(guild)
            return

        winner_id = random.choice(list(players.keys()))
        winner_obj = guild.get_member(winner_id)

        jackpot = self.lottery_jackpot(guild)

        embed = discord.Embed(description=f'{winner_obj.name} won the total jackpot of {jackpot} {self.currency_name}!')
        random_double = random.randint(1, 100)
        if random_double == 100:
            jackpot = jackpot * 2
            embed.description = f'The jackpot was randomly doubled!\n{winner_obj.name} won the total jackpot of {jackpot} {self.currency_name}!'
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

        await self.bot.get_cog("Currency").user_add_currency(guild, winner_obj, jackpot)

        await self.stop_lottery(guild)

    @lottery.command(name='bet', no_pm=True)
    async def lottery_bet(self, ctx, amount : int):
        """Bet in the lottery."""
        guild = ctx.guild
        author = ctx.author

        lottery = self.config.get('lottery', {})
        players = lottery.get(guild.id, {})

        lottery_status = self.config.get('lottery_status', {})

        if amount < self.lottery_min_amt and author.id not in players:
            embed = discord.Embed(description=f'You must bet atleast {self.lottery_min_amt} {self.currency_name} to enter the lottery!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if amount < 0:
            embed = discord.Embed(description='You cannot bet a negative amount!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if guild.id not in lottery_status:
            embed = discord.Embed(description='There is no ongoing lottery!\nType `>lottery` to start a lottery!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if lottery_status[guild.id] == False:
            embed = discord.Embed(description='There is no ongoing lottery!\nType `>lottery` to start a lottery!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if await self.bot.get_cog("Currency").user_remove_currency(guild, author, amount) == False:
            embed = discord.Embed(description='You cannot afford to bet that much!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if author.id not in players:
            players[author.id] = amount
        else:
            players[author.id] += amount

        lottery[guild.id] = players
        await self.config.put('lottery', lottery)

        jackpot = self.lottery_jackpot(guild)

        embed = discord.Embed(description='You currently have {} {} in the lottery.\nThe current jackpot is {} {}!'.format(players[author.id], self.currency_name, jackpot, self.currency_name))
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

    @lottery.command(name='forcepayout', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def lottery_forcepayout(self, ctx):
        """Force a payout for the lottery."""
        guild = ctx.guild

        lottery_status = self.config.get('lottery_status', {})
        if guild.id not in lottery_status:
            embed = discord.Embed(description='There is no ongoing lottery!\nType `>lottery` to start a lottery!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if lottery_status[guild.id] == False:
            embed = discord.Embed(description='There is no ongoing lottery!\nType `>lottery` to start a lottery!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        lottery = self.config.get('lottery', {})
        players = lottery.get(guild.id, {})

        winner_id = random.choice(list(players.keys()))
        winner_obj = guild.get_member(winner_id)

        jackpot = self.lottery_jackpot(guild)

        embed = discord.Embed(description=f'{winner_obj.name} won the total jackpot of {jackpot} {self.currency_name}!')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

        await self.bot.get_cog("Currency").user_add_currency(guild, winner_obj, jackpot)

        await self.stop_lottery(guild)

    @lottery.command(name='forcerefund', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def lottery_forcerefund(self, ctx):
        """Force a refund for the lottery."""
        guild = ctx.guild

        lottery_status = self.config.get('lottery_status', {})
        if guild.id not in lottery_status:
            embed = discord.Embed(description='There is no ongoing lottery!\nType `>lottery` to start a lottery!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if lottery_status[guild.id] == False:
            embed = discord.Embed(description='There is no ongoing lottery!\nType `>lottery` to start a lottery!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        lottery = self.config.get('lottery', {})
        players = lottery.get(guild.id, {})

        embed = discord.Embed(description='Returning money...')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

        for player in players:
            playerobj = guild.get_member(player)
            await self.bot.get_cog("Currency").user_add_currency(guild, playerobj, players[player])

        await self.stop_lottery(guild)

def setup(bot):
    bot.add_cog(Games(bot))
