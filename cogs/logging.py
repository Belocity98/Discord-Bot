import discord
import asyncio

from discord.ext import commands

class Logging():

    def __init__(self, bot):
        self.bot = bot

    async def on_message_delete(self, message):
        server = message.server
        logging_channel = discord.utils.find(lambda c: c.name == 'bot-logging', server.channels)
        if logging_channel == None:
            print("Logging channel not found.")
            print("Creating logging channel...")
            await self.bot.create_channel(server, 'bot-logging')
            return

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
            print("Logging channel not found.")
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
