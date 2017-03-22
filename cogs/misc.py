# Credit to Danny for the Google command. https://github.com/Rapptz/RoboDanny/blob/master/cogs/buttons.py#L78-L315

import urbandict
import discord
import asyncio
import logging
import aiohttp
import xkcd
import sys
import os

from lxml import etree
from random import randint
from discord.ext import commands
from .utils import checks, config
from urllib.parse import parse_qs
from datetime import datetime, timezone

log = logging.getLogger(__name__)

class Misc():

    def __init__(self, bot):
        self.bot = bot
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        cfgfile = os.path.join(app_path, 'misc.json')
        self.config = config.Config(cfgfile, loop=bot.loop)

    async def check_strikes(self, guild, user, ctx):
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

        await guild.create_role(color=color, name=name, hoist=True, mentionable=True, permissions=permissions)

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
            return m.author.id == author.id

        embed = discord.Embed(description=f"{user.name} is lying? What are they lying about?\nReply with their lie.")
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)
        lie = await self.bot.wait_for('message', timeout=60, check=author_check)

        embed = discord.Embed(title=f'{user.name} was caught lying!')
        embed.description = f'Exposed by: {author.name}'
        embed.timestamp = ctx.message.created_at
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
            strike_check = await self.check_strikes(guild, user, ctx)
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
            strike_check = await self.check_strikes(guild, user, ctx)
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
            async for message in ctx.channel.history():
                if message.author == user:
                    quote = message
                    break

        elif message_id != None:
            quote = await channel.get_message(message_id)

        if quote == None:
            embed = discord.Embed(description='Quote not found.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)

            return

        embed = discord.Embed(description=quote.content)
        embed.set_author(name=quote.author.name, icon_url=quote.author.avatar_url)
        embed.timestamp = quote.created_at
        embed.colour = 0x1BE118 # lucio green

        await ctx.channel.send(embed=embed)

    def parse_google_card(self, node):
        if node is None:
            return None

        e = discord.Embed(colour=0x1BE118)

        # check if it's a calculator card:
        calculator = node.find(".//table/tr/td/span[@class='nobr']/h2[@class='r']")
        if calculator is not None:
            e.title = 'Calculator'
            e.description = ''.join(calculator.itertext())
            return e

        parent = node.getparent()

        # check for unit conversion card
        unit = parent.find(".//ol//div[@class='_Tsb']")
        if unit is not None:
            e.title = 'Unit Conversion'
            e.description = ''.join(''.join(n.itertext()) for n in unit)
            return e

        # check for currency conversion card
        currency = parent.find(".//ol/table[@class='std _tLi']/tr/td/h2")
        if currency is not None:
            e.title = 'Currency Conversion'
            e.description = ''.join(currency.itertext())
            return e

        # check for release date card
        release = parent.find(".//div[@id='_vBb']")
        if release is not None:
            try:
                e.description = ''.join(release[0].itertext()).strip()
                e.title = ''.join(release[1].itertext()).strip()
                return e
            except:
                return None

        # check for definition card
        words = parent.find(".//ol/div[@class='g']/div/h3[@class='r']/div")
        if words is not None:
            try:
                definition_info = words.getparent().getparent()[1] # yikes
            except:
                pass
            else:
                try:
                    # inside is a <div> with two <span>
                    # the first is the actual word, the second is the pronunciation
                    e.title = words[0].text
                    e.description = words[1].text
                except:
                    return None

                # inside the table there's the actual definitions
                # they're separated as noun/verb/adjective with a list
                # of definitions
                for row in definition_info:
                    if len(row.attrib) != 0:
                        # definitions are empty <tr>
                        # if there is something in the <tr> then we're done
                        # with the definitions
                        break

                    try:
                        data = row[0]
                        lexical_category = data[0].text
                        body = []
                        for index, definition in enumerate(data[1], 1):
                            body.append('%s. %s' % (index, definition.text))

                        e.add_field(name=lexical_category, value='\n'.join(body), inline=False)
                    except:
                        continue

                return e

        # check for "time in" card
        time_in = parent.find(".//ol//div[@class='_Tsb _HOb _Qeb']")
        if time_in is not None:
            try:
                time_place = ''.join(time_in.find("span[@class='_HOb _Qeb']").itertext()).strip()
                the_time = ''.join(time_in.find("div[@class='_rkc _Peb']").itertext()).strip()
                the_date = ''.join(time_in.find("div[@class='_HOb _Qeb']").itertext()).strip()
            except:
                return None
            else:
                e.title = time_place
                e.description = '%s\n%s' % (the_time, the_date)
                return e

        # check for weather card
        # this one is the most complicated of the group lol
        # everything is under a <div class="e"> which has a
        # <h3>{{ weather for place }}</h3>
        # string, the rest is fucking table fuckery.
        weather = parent.find(".//ol//div[@class='e']")
        if weather is None:
            return None

        location = weather.find('h3')
        if location is None:
            return None

        e.title = ''.join(location.itertext())

        table = weather.find('table')
        if table is None:
            return None

        # This is gonna be a bit fucky.
        # So the part we care about is on the second data
        # column of the first tr
        try:
            tr = table[0]
            img = tr[0].find('img')
            category = img.get('alt')
            image = 'https:' + img.get('src')
            temperature = tr[1].xpath("./span[@class='wob_t']//text()")[0]
        except:
            return None # RIP
        else:
            e.set_thumbnail(url=image)
            e.description = '*%s*' % category
            e.add_field(name='Temperature', value=temperature)

        # On the 4th column it tells us our wind speeds
        try:
            wind = ''.join(table[3].itertext()).replace('Wind: ', '')
        except:
            return None
        else:
            e.add_field(name='Wind', value=wind)

        # On the 5th column it tells us our humidity
        try:
            humidity = ''.join(table[4][0].itertext()).replace('Humidity: ', '')
        except:
            return None
        else:
            e.add_field(name='Humidity', value=humidity)

        return e

    async def get_google_entries(self, query):
        params = {
            'q': query,
            'safe': 'on'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64)'
        }

        # list of URLs
        entries = []

        # the result of a google card, an embed
        card = None

        async with aiohttp.get('https://www.google.com/search', params=params, headers=headers) as resp:
            if resp.status != 200:
                raise RuntimeError('Google somehow failed to respond.')

            root = etree.fromstring(await resp.text(), etree.HTMLParser())

            # with open('google.html', 'w', encoding='utf-8') as f:
            #     f.write(etree.tostring(root, pretty_print=True).decode('utf-8'))

            """
            Tree looks like this.. sort of..
            <div class="g">
                ...
                <h3>
                    <a href="/url?q=<url>" ...>title</a>
                </h3>
                ...
                <span class="st">
                    <span class="f">date here</span>
                    summary here, can contain <em>tag</em>
                </span>
            </div>
            """

            card_node = root.find(".//div[@id='topstuff']")
            card = self.parse_google_card(card_node)

            search_nodes = root.findall(".//div[@class='g']")
            for node in search_nodes:
                url_node = node.find('.//h3/a')
                if url_node is None:
                    continue

                url = url_node.attrib['href']
                if not url.startswith('/url?'):
                    continue

                url = parse_qs(url[5:])['q'][0] # get the URL from ?q query string

                # if I ever cared about the description, this is how
                entries.append(url)

                # short = node.find(".//span[@class='st']")
                # if short is None:
                #     entries.append((url, ''))
                # else:
                #     text = ''.join(short.itertext())
                #     entries.append((url, text.replace('...', '')))

        return card, entries

    @commands.command(aliases=['google'])
    async def g(self, ctx, *, query):
        """Searches google and gives you top result."""
        channel = ctx.channel

        try:
            card, entries = await self.get_google_entries(query)
        except RuntimeError as e:
            await channel.send(str(e))
        else:
            if card:
                value = '\n'.join(entries[:3])
                if value:
                    card.add_field(name='Search Results', value=value, inline=False)
                return await channel.send(embed=card)

            if len(entries) == 0:
                return await channel.send('No results found... sorry.')

            next_two = entries[1:3]
            if next_two:
                formatted = '\n'.join(map(lambda x: '<%s>' % x, next_two))
                msg = '{}\n\n**See also:**\n{}'.format(entries[0], formatted)
            else:
                msg = entries[0]

            await channel.send(msg)

    @commands.command()
    async def xkcd(self, ctx, number=None):
        """Sends the link of a random xkcd comic to the chat.
        if a number is specified, send the comic referring to that number."""

        if number:
            comic = xkcd.getComic(number)
        else:
            comic = xkcd.getRandomComic()

        comicurl = comic.getImageLink()

        embed = discord.Embed(description=f'[Image Link]({comicurl})')
        embed.set_image(url=comicurl)
        embed.colour = 0x1BE118 # lucio green

        try:
            await ctx.channel.send(embed=embed)
        except:
            pass

    @commands.command()
    async def urband(self, ctx, *, word : str):
        """Sends the definition of a word from the UrbanDictionary."""

        word_list = urbandict.define(word)

        embed = discord.Embed(title=word_list[0]['word'])
        embed.description = word_list[0]['def']

        embed.colour = 0x1BE118 # lucio green

        await ctx.channel.send(embed=embed)

    @commands.command(no_pm=True)
    async def discrimsearch(self, ctx, discrim : str=None):
        """Sends the first 10 discrims found of the given discrim.

        If no discrim is provided, author's discrim is used."""

        embed = discord.Embed()
        embed.colour = 0x1BE118 # lucio green

        if not discrim:
            discrim = ctx.author.discriminator

        discrim_users = []
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.discriminator == discrim:
                    discrim_users.append(f'{member.name}#{member.discriminator}')

        total_matches = len(discrim_users)
        discrim_users = list(set(discrim_users))

        if total_matches == 0:
            embed.description = 'No matches found.'
            await ctx.send(embed=embed)
            return

        extra = None
        if total_matches > 10:
            extra = total_matches - 10


        embed.description = '\n'.join(discrim_users)

        if extra:
            embed.description = '\n'.join(discrim_users) + f'\n\nAnd {extra} more.'

        await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Misc(bot))
