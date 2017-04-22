import traceback
import datetime
import discord
import aiohttp
import asyncio
import logging
import sys
import os



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

description = "General purpose Discord chat bot. Includes moderation and fun commands."

log = logging.getLogger(__name__)
logging.getLogger('discord.http').setLevel(logging.CRITICAL)

# Yes, I took RoboDanny's file structure.

# this specifies what extensions to load when the bot starts up
startup_extensions = [
    'cogs.games',
    'cogs.mod',
    'cogs.misc',
    'cogs.stats',
    'cogs.admin',
    'cogs.reddit',
    'cogs.logging',
    'cogs.currency',
    'cogs.settings',
    'cogs.events',
    'cogs.nsfw',
    'cogs.weather'
]

app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
data = os.path.join(app_path, 'data.json')
data_base = config.Config(data)

def get_prefix(bot, message):
    server_data = data_base.get(message.guild.id, {})
    return server_data.get('prefix', '>')

bot = commands.Bot(command_prefix=get_prefix, description=description)
bot.db = data_base
bot.session = aiohttp.ClientSession(loop=bot.loop, headers={'User-Agent' : 'Wumpus Bot'})

@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name=">help | >invite"))
    print('Logged in as')
    print(f'Name: {bot.user.name}')
    print(f'ID: {bot.user.id}')
    print(f'Lib Ver: {discord.__version__}')
    print('------')
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()

@bot.event
async def on_command_error(exc, ctx):
    e = getattr(exc, 'original', exc)
    if isinstance(e, (commands.MissingRequiredArgument, commands.CommandOnCooldown, discord.Forbidden)):
        log.info(str(e))
    elif isinstance(e, commands.CheckFailure):
        log.info('Permission denied.')
    else:
        tb = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        print(tb)

bot.credentials = config.Config(os.path.join(app_path, 'credentials.json'))
if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            log.info(f'Failed to load extension {extension}\n{exc}')
    bot.run(bot.credentials['token'])
