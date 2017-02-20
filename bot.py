import discord
import traceback
import os
import sys
import json
import asyncio
import logging

from discord.ext import commands
from cogs.utils import config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
log_file = os.path.join(app_path, 'bot_log.log')
fh = logging.FileHandler(filename=log_file, encoding='utf-8', mode='w')
fh.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s","%Y-%m-%d %H:%M:%S")

ch.setFormatter(formatter)
fh.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

description = "A general bot for personal use."

# Yes, I took RoboDanny's file structure.

# this specifies what extensions to load when the bot starts up
startup_extensions = [
    "cogs.games",
    "cogs.mod",
    "cogs.misc",
    "cogs.stats",
    "cogs.admin",
    "cogs.reddit",
    "cogs.logging",
    "cogs.currency"
]

app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
main_config = os.path.join(app_path, 'prefixes.json')
prefixes = config.Config(main_config)

def get_prefix(bot, message):
    server_prefixes = prefixes.get('prefixes', {})
    if message.guild.id not in server_prefixes:
        return '>'
    else:
        return server_prefixes[message.guild.id]

bot = commands.Bot(command_prefix=get_prefix, description=description, pm_help=True)
bot.prefixes = prefixes

try:
    app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    tmp_file = os.path.join(app_path, 'config.json')
    with open(tmp_file) as fp:
        bot.config = json.load(fp)
except:
    app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    tmp_file = os.path.join(app_path, 'example_config.json')
    with open(tmp_file) as fp:
        bot.config = json.load(fp)

@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name=">help | >invite"))
    print('Logged in as')
    print(f'Name: {bot.user.name}')
    print(f'ID: {bot.user.id}')
    print('------')

@bot.event
async def on_command_error(exc, ctx):
    e = getattr(exc, 'original', exc)
    if isinstance(e, (commands.MissingRequiredArgument, commands.CommandOnCooldown, discord.Forbidden)):
        await ctx.channel.send(str(e))
    elif isinstance(e, commands.CheckFailure):
        await ctx.channel.send('You do not have permission to do that.')
    else:
        tb = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        print(tb)

if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print(f'Failed to load extension {extension}\n{exc}')

    if "discord bot token" in bot.config["token"]:
        print("Bot token not found. Not running.")
    else:
        bot.run(bot.config["token"])
