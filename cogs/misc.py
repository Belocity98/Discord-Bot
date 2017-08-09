# Credit to Danny for the Google command. https://github.com/Rapptz/RoboDanny/blob/master/cogs/buttons.py#L78-L315

import urbandict
import markovify
import discord
import asyncio
import aiohttp
import xkcd
import sys
import os

from datetime import datetime, timezone
from urllib.parse import parse_qs
from discord.ext import commands
from html2text import html2text
from lxml import etree



class ChannelOrMember(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.TextChannelConverter().convert(ctx, argument)
        except commands.BadArgument:
            return await commands.MemberConverter().convert(ctx, argument)

class Misc:

    def __init__(self, bot):
        self.bot = bot

        self.session = bot.session

        self.quote_api = r"http://quotesondesign.com/wp-json/posts?filter[orderby]=rand&filter[posts_per_page]=1"

    async def get_text(self, destination):
        message_list = []

        if isinstance(destination, discord.Member):
            for channel in destination.guild.text_channels:

                perms = channel.permissions_for(destination)
                if not perms.send_messages:
                    continue

                try:
                    async for message in channel.history(limit=500):
                        if message.content and message.author.id == destination.id:
                            message_list.append(message.content)
                except discord.Forbidden:
                    continue # We can't access that channel.
        else:
            async for message in destination.history(limit=3000, reverse=True):
                if message.content:
                    message_list.append(message.content)

        return '\n'.join(message_list)

    @commands.command()
    async def markov(self, ctx, destination : ChannelOrMember, sentence_count : int=2):
        """Generates a markov chain for a channel or member."""
        markov = await ctx.send(content='Generating markov chain...')
        text = await self.get_text(destination)

        text_model = markovify.NewlineText(text)

        sentences = []
        for i in range(sentence_count):
            sentences.append(await self.bot.loop.run_in_executor(None, text_model.make_short_sentence, 140))

        if None in sentences:
            return await markov.edit(content='Not enough data to generate chain.')

        await markov.edit(content=' '.join(sentences))

    @commands.command()
    async def charinfo(self, ctx, *, characters: str):
        """Shows you information about a number of characters.
        
        Only up to 25 characters at a time.
        """

        if len(characters) > 25:
            return await ctx.send(f'Too many characters ({len(characters)}/25)')

        def to_string(c):
            digit = f'{ord(c):x}'
            name = unicodedata.name(c, 'Name not found.')
            return f'`\\U{digit:>08}`: {name} - {c} \N{EM DASH} <http://www.fileformat.info/info/unicode/char/{digit}>'

        await ctx.send('\n'.join(map(to_string, characters)))

    @commands.command()
    async def echo(self, ctx, *, message : str):
        """Echos a message."""

        await ctx.send(message.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere'))

    @commands.command()
    @commands.guild_only()
    async def avatar(self, ctx, member : discord.Member):
        """Sends the current avatar of the member."""

        await ctx.channel.trigger_typing()

        embed = discord.Embed()
        embed.colour = 0x42c2f4

        a_url = member.avatar_url_as(format=None, size=1024)

        embed.description = f'[Link]({a_url})'
        embed.set_image(url=a_url)

        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        x = await ctx.send('Ping!')
        time = datetime.now()
        await x.edit(content='`...`')
        difference = (datetime.now() - time).total_seconds() * 1000
        difference = difference/2
        difference = str(round(difference, 2))
        await x.edit(content=f'Pong! `{difference} ms.`')

    @commands.command()
    @commands.guild_only()
    async def quote(self, ctx, user : discord.Member, message_id : int=None):
        """Quotes a user. Quotes the last message the user sent in the current channel unless an ID is specified."""

        channel = ctx.channel

        quote = None

        if not message_id:
            async for message in ctx.channel.history():
                if message.author == user:
                    quote = message
                    break

        elif message_id:
            quote = await channel.get_message(message_id)

        if not quote:
            embed = discord.Embed(description='Quote not found.')
            embed.colour = 0x42c2f4
            await ctx.channel.send(embed=embed)

            return

        embed = discord.Embed(description=quote.content)
        embed.set_author(name=quote.author.name, icon_url=quote.author.avatar_url)
        embed.timestamp = quote.created_at
        embed.colour = 0x42c2f4

        await ctx.channel.send(embed=embed)

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
        embed.colour = 0x42c2f4

        try:
            await ctx.channel.send(embed=embed)
        except:
            pass

    @commands.command()
    async def urban(self, ctx, *, word : str):
        """Sends the definition of a word from the UrbanDictionary."""

        word_list = urbandict.define(word)

        embed = discord.Embed(title=word_list[0]['word'])
        embed.description = word_list[0]['def']

        embed.colour = 0x42c2f4

        await ctx.send(embed=embed)

    @commands.command()
    async def inspire(self, ctx):
        """Sends a random quote."""

        async with self.session.get(self.quote_api) as rawdata:
            resp = await rawdata.json()

        quote_data = resp[0]
        title = quote_data['title']
        content = html2text(quote_data['content'])

        embed = discord.Embed()
        embed.colour = 0x42c2f4
        embed.description = f'**{content}**'
        embed.description += f'\n- {title}'

        await ctx.send(embed=embed)

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



def setup(bot):
    bot.add_cog(Misc(bot))
