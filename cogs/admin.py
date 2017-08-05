import datetime
import discord
import inspect
import sys
import os

from collections import Counter
from discord.ext import commands
from .utils import checks



class Admin:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='reload', hidden=True)
    @checks.is_owner()
    async def _reload(self, ctx, *, extension_name : str):
        """Reloads an extension."""
        if extension_name == "all":
            for cog in list(self.bot.cogs.keys()):
                try:
                    cog = "cogs." + cog.lower()
                    self.bot.unload_extension(cog)
                    self.bot.load_extension(cog)
                except (AttributeError, ImportError) as e:
                    await ctx.channel.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            return
        try:
            self.bot.unload_extension(extension_name)
            self.bot.load_extension(extension_name)
            self.bot.log.info(f'{extension_name} reloaded.')
        except ImportError:
            await ctx.channel.send("Cog not found.")
            return

    @commands.command(hidden=True)
    @checks.is_owner()
    async def load(self, ctx, *, extension_name : str):
        """Loads an extension."""
        try:
            self.bot.load_extension(extension_name)
            self.bot.log.info(f'{extension_name} loaded.')
        except (AttributeError, ImportError) as e:
            await ctx.channel.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            return

    @commands.command(hidden=True)
    @checks.is_owner()
    async def unload(self, ctx, *, extension_name : str):
        """Unloads an extension."""
        self.bot.unload_extension(extension_name)
        self.bot.log.info(f'{extension_name} unloaded.')

    @commands.command(hidden=True, name='logout')
    @checks.is_owner()
    async def _logout(self):
        """Turns off the bot."""
        self.bot.log.info('Bot logging off.')
        await self.bot.logout()

    @commands.command(hidden=True)
    @checks.is_owner()
    async def debug(self, ctx, *, code: str):
        """Evaluates code."""

        code = code.strip('` ')
        python = '```py\n{}\n```'
        result = None

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


def setup(bot):
    bot.add_cog(Admin(bot))
