import inspect

from discord.ext import commands
from cogs.utils import config


class Admin:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx, *, extension_name: str):
        """Reloads an extension."""
        try:
            self.bot.unload_extension(extension_name)
            self.bot.load_extension(extension_name)
            self.bot.log.info(f'{extension_name} reloaded.')
            await ctx.message.add_reaction('👌')
        except ImportError:
            await ctx.channel.send("Cog not found.")
            return

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, *, extension_name: str):
        """Loads an extension."""
        try:
            self.bot.load_extension(extension_name)
            self.bot.log.info(f'{extension_name} loaded.')
            await ctx.message.add_reaction('👌')
        except (AttributeError, ImportError) as e:
            await ctx.channel.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            return

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, *, extension_name: str):
        """Unloads an extension."""
        self.bot.unload_extension(extension_name)
        self.bot.log.info(f'{extension_name} unloaded.')
        await ctx.message.add_reaction('👌')

    @commands.command(hidden=True, name='logout')
    @commands.is_owner()
    async def _logout(self, ctx):
        """Turns off the bot."""
        self.bot.log.info('Bot logging off.')
        await self.bot.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def debug(self, ctx, *, code: str):
        """Evaluates code."""

        code = code.strip('` ')
        python = '```py\n{}\n```'

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'message': ctx.message,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author
        }

        env.update(globals())

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            await ctx.send(python.format(type(e).__name__ + ': ' + str(e)))
            return

        await ctx.send(python.format(result))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def updatecfg(self, ctx):
        """Updates the configuration."""

        self.bot.db = config.Config("credentials.json")


def setup(bot):
    bot.add_cog(Admin(bot))
