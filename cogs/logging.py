from discord.ext import commands
import discord
import asyncio

class Logging():

    def __init__(self, bot):
        self.bot = bot

    async def on_message_delete(self, message):
        if message.author == message.server.me:
            return
        else:
            lines = []
            lines.append("**Message Deleted**")
            lines.append("Author: {}".format(message.author))
            lines.append("Message: {}".format(message.content))
            await self.bot.send_message(self.bot.get_channel(self.bot.config["channels"]["bot-logging"]), "\n".join(lines))

    async def on_message_edit(self, before, after):
        if before.author == before.server.me:
            return
        else:
            lines = []
            lines.append("**Message Edited**")
            lines.append("Author: {}".format(before.author))
            lines.append("Before: {}".format(before.content))
            lines.append("After: {}".format(after.content))
        await self.bot.send_message(self.bot.get_channel(self.bot.config["channels"]["bot-logging"]), "\n".join(lines))

    async def do_logging(self, llog, channel=None):
        await self.bot.send_message(self.bot.get_channel(self.bot.config["channels"]["bot-logging"]), llog)
        print(llog)
        if channel != None:
            await self.bot.send_message(channel, llog)

def setup(bot):
    bot.add_cog(Logging(bot))
