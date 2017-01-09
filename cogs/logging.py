from discord.ext import commands
import discord
import asyncio

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
        if message.author == message.server.me:
            return
        else:
            lines = []
            lines.append("**Message Deleted**")
            lines.append("Author: {}".format(message.author))
            lines.append("Message: {}".format(message.content))
            await self.bot.send_message(logging_channel, "\n".join(lines))
            #await self.bot.send_message(self.bot.get_channel(self.bot.config["channels"]["bot-logging"]), "\n".join(lines))

    async def on_message_edit(self, before, after):
        server = before.server
        logging_channel = discord.utils.find(lambda c: c.name == 'bot-logging', server.channels)
        if logging_channel == None:
            print("Logging channel not found.")
            return
        if before.author == before.server.me:
            return
        if before.content == after.content:
            return
        else:
            lines = []
            lines.append("**Message Edited**")
            lines.append("Author: {}".format(before.author))
            lines.append("Before: {}".format(before.content))
            lines.append("After: {}".format(after.content))
        await self.bot.send_message(logging_channel, "\n".join(lines))
        #await self.bot.send_message(self.bot.get_channel(self.bot.config["channels"]["bot-logging"]), "\n".join(lines))

    async def do_logging(self, llog, server, channel=None):
        logging_channel = discord.utils.find(lambda c: c.name == 'bot-logging', server.channels)
        if logging_channel == None:
            print("Logging channel not found.")
            return
        await self.bot.send_message(logging_channel, llog)
        #await self.bot.send_message(self.bot.get_channel(self.bot.config["channels"]["bot-logging"]), llog)
        print(llog)
        if channel != None:
            await self.bot.send_message(channel, llog)

def setup(bot):
    bot.add_cog(Logging(bot))
