import traceback
import datetime
import discord
import aiohttp
import sys



from logbook import Logger, StreamHandler
from discord.ext import commands
from cogs.utils import config

description = "General purpose Discord chat bot. Includes moderation and fun commands."

# Yes, I took RoboDanny's file structure.

# this specifies what extensions to load when the bot starts up
startup_extensions = [
    'cogs.leagueoflegends',
    'cogs.settings',
    'cogs.logging',
    'cogs.weather',
    'cogs.events',
    'cogs.reddit',
    'cogs.admin',
    'cogs.music',
    'cogs.games',
    'cogs.stats',
    'cogs.misc',
    'cogs.nsfw',
    'cogs.vote',
    'cogs.mod'
]

db = config.Config('data.json')


def get_prefix(bot, message):
    if not message.guild:
        return '>'
    server_data = db.get(message.guild.id, {})
    return server_data.get('prefix', '>')

bot = commands.Bot(command_prefix=get_prefix, description=description)
bot.db = db
bot.session = aiohttp.ClientSession(loop=bot.loop, headers={'User-Agent' : 'Wumpus Bot'})

StreamHandler(sys.stdout).push_application()
bot.log = Logger('Wumpus Bot')


@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name=">help | >invite"))
    bot.log.info('Logged in as')
    bot.log.info(f'Name: {bot.user.name}')
    bot.log.info(f'ID: {bot.user.id}')
    bot.log.info(f'Lib Ver: {discord.__version__}')
    bot.log.info('------')
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()


@bot.event
async def on_command_error(ctx, exc):
    e = getattr(exc, 'original', exc)
    if isinstance(e, (commands.CommandOnCooldown, discord.Forbidden)):
        bot.log.info(str(e))
    elif isinstance(e, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.invoke(bot.get_command('help'), ctx.command.name)
        bot.log.info(str(e))
    elif isinstance(e, commands.CheckFailure):
        bot.log.info('Permission denied.')
    else:
        tb = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        bot.log.error(tb)

bot.credentials = config.Config('credentials.json')
if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            bot.log.info(f'Failed to load extension {extension}\n{exc}')
    bot.run(bot.credentials['token'])
