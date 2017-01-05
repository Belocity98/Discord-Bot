import discord
from discord.ext import commands
import traceback
import os
import sys
import json
import asyncio

description = "A general bot for personal use."

# this specifies what extensions to load when the bot starts up
startup_extensions = [
    "cogs.games",
    "cogs.mod",
    "cogs.misc",
    "cogs.stats",
    "cogs.admin",
    "cogs.reddit",
    "cogs.logging"
]

bot = commands.Bot(command_prefix='?', description=description)

app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
config_file = os.path.join(app_path, 'config.json')
with open(config_file) as fp:
    bot.config = json.load(fp)

bot.tmp_banned_cache = {}

@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name=">help"))
    print('Logged in as')
    print('Name: ' + bot.user.name)
    print('ID: '+ bot.user.id)
    print('------')

@bot.event
async def on_command_error(exc, ctx):
    e = getattr(exc, 'original', exc)
    if isinstance(e, (commands.MissingRequiredArgument, commands.CommandNotFound, commands.CommandOnCooldown, commands.CheckFailure, discord.Forbidden)):
        await bot.send_message(ctx.message.channel, str(e))
    else:
        tb = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        print(tb)

if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))

    bot.run(bot.config["test_token"])
