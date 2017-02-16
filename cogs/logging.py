import discord
import asyncio
import logging
import os
import sys

from discord.ext import commands
from .utils import config

log = logging.getLogger(__name__)

class Logging():

    def __init__(self, bot):
        self.bot = bot

        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        cfgfile = os.path.join(app_path, 'logging.json')
        self.config = config.Config(cfgfile, loop=bot.loop)

    @commands.command(no_pm=True)
    @commands.has_permissions(administrator=True)
    async def enablelogging(self, ctx):
        """Enable logging for the guild."""
        guild = ctx.guild

        logging = self.config.get('logging', {})
        db = logging.get(guild.id, {})

        if db == True:
            embed = discord.Embed(description='Logging is already enabled!')
            embed.colour = 0x1BE118
            await ctx.channel.send(embed=embed)
            return

        db = True
        embed = discord.Embed(description='Logging enabled!')
        embed.colour = 0x1BE118
        await ctx.channel.send(embed=embed)

        logging[guild.id] = db

        await self.config.put('logging', logging)

    @commands.command(no_pm=True)
    @commands.has_permissions(administrator=True)
    async def disablelogging(self, ctx):
        """Disable logging for the guild."""
        guild = ctx.guild

        logging = self.config.get('logging', {})
        db = logging.get(guild.id, {})

        if db == False:
            embed = discord.Embed(description='Logging is already disabled!')
            embed.colour = 0x1BE118
            await ctx.channel.send(embed=embed)
            return

        db = False
        embed = discord.Embed(description='Logging disabled!')
        embed.colour = 0x1BE118
        await ctx.channel.send(embed=embed)

        logging[guild.id] = db

        await self.config.put('logging', logging)

    def check_if_logging(self, guild, channel):

        if guild == None:
            return

        can_make_c = channel.permissions_for(guild.me).manage_channels
        if not can_make_c:
            return

        logging = self.config.get('logging', {})
        db = logging.get(guild.id, {})

        if db == True:
            return True

        else:
            return False

    async def create_logging_channel(self, guild):
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.owner: discord.PermissionOverwrite(read_messages=True)
        }

        await guild.create_text_channel('bot-logging', overwrites=overwrites)

        log.info(f'bot-logging channel created in {guild.name}.')
        return

    async def on_message_delete(self, message):
        guild = message.guild
        channel = message.channel

        if not self.check_if_logging(guild, channel):
            return

        if guild == None:
            return

        logging_channel = discord.utils.find(lambda c: c.name == 'bot-logging', guild.channels)
        if logging_channel == None:
            await self.create_logging_channel(guild)

        else:
            embed = discord.Embed(description=message.content)
            embed.colour = 0x1BE118 # lucio green
            embed.set_author(name=message.author, icon_url=message.author.avatar_url)
            embed.set_footer(text="Message Deleted", icon_url='http://i.imgur.com/ulgDAMM.png')
            if len(message.attachments) != 0:
                embed.set_image(url=message.attachments[0]['proxy_url'])
            if len(message.embeds) != 0:
                embed = discord.Embed.from_data(message.embeds[0])
                await logging_channel.send(content="**Message Deleted**", embed=embed)
                return
            await logging_channel.send(embed=embed)

    async def on_message_edit(self, before, after):
        guild = before.guild
        channel = after.channel

        if not self.check_if_logging(guild, channel):
            return

        if guild == None:
            return

        logging_channel = discord.utils.find(lambda c: c.name == 'bot-logging', guild.channels)
        if logging_channel == None:
            await self.create_logging_channel(guild)
            return
        if before.author == before.guild.me:
            return
        if before.content == after.content:
            return
        else:
            embed = discord.Embed()
            embed.add_field(name="Before Content", value=before.content, inline=False)
            embed.add_field(name='After Content', value=after.content, inline=False)
            embed.set_footer(text="Message Edited", icon_url='http://i.imgur.com/zWTQEYe.png')
            embed.colour = 0x1BE118 # lucio green
            embed.set_author(name=before.author, icon_url=before.author.avatar_url)
            await logging_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Logging(bot))
