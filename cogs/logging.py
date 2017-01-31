import discord
import asyncio
import logging

from discord.ext import commands

log = logging.getLogger(__name__)

class Logging():

    def __init__(self, bot):
        self.bot = bot

    async def create_logging_channel(self, server):
        everyone_perms = discord.PermissionOverwrite(read_messages=False)
        my_perms = discord.PermissionOverwrite(read_messages=True)
        everyone = discord.ChannelPermissions(target=server.default_role, overwrite=everyone_perms)
        mine = discord.ChannelPermissions(target=server.owner, overwrite=my_perms)

        await self.bot.create_channel(server, 'bot-logging', everyone, mine)
        log.info('bot-logging channel created in {}.'.format(server.name))
        return

    async def on_message_delete(self, message):
        server = message.server
        if server == None:
            return

        logging_channel = discord.utils.find(lambda c: c.name == 'bot-logging', server.channels)
        if logging_channel == None:
            await self.create_logging_channel(server)

        else:
            embed = discord.Embed(description=message.content)
            embed.colour = 0x1BE118 # lucio green
            embed.set_author(name=message.author, icon_url=message.author.avatar_url)
            embed.set_footer(text="Message Deleted", icon_url='http://i.imgur.com/ulgDAMM.png')
            if len(message.attachments) != 0:
                embed.set_image(url=message.attachments[0]['proxy_url'])
            if len(message.embeds) != 0:
                embed = discord.Embed.from_data(message.embeds[0])
                await self.bot.send_message(logging_channel, content="**Message Deleted**", embed=embed)
                return
            await self.bot.send_message(logging_channel, embed=embed)

    async def on_message_edit(self, before, after):
        server = before.server
        if server == None:
            return

        logging_channel = discord.utils.find(lambda c: c.name == 'bot-logging', server.channels)
        if logging_channel == None:
            await self.create_logging_channel(server)
            return
        if before.author == before.server.me:
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
            await self.bot.send_message(logging_channel, embed=embed)

def setup(bot):
    bot.add_cog(Logging(bot))
