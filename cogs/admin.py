import discord
import os
import sys
import logging
import json

from discord.ext import commands
from .utils import checks

log = logging.getLogger(__name__)

class Admin:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True)
    @checks.is_owner()
    async def broadcast(self, ctx, *, message : str):
        """Command to broadcast a message to all the servers the bot is in."""
        for guild in self.bot.guilds:
            try:
                await guild.default_channel.send(message)
            except:
                pass

    @commands.command(hidden=True)
    @checks.is_owner()
    async def reloadconfig(self, ctx):
        """Reloads the configuration."""
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        tmp_file = os.path.join(app_path, 'config.json')
        with open(tmp_file) as fp:
            json.load(fp)
        log.info('Configuration reloaded.')

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
            log.info(f'{extension_name} reloaded.')
        except ImportError:
            await ctx.channel.send("Cog not found.")
            return

    @commands.command(hidden=True)
    @checks.is_owner()
    async def load(self, ctx, *, extension_name : str):
        """Loads an extension."""
        try:
            self.bot.load_extension(extension_name)
            log.info(f'{extension_name} loaded.')
        except (AttributeError, ImportError) as e:
            await ctx.channel.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            return

    @commands.command(hidden=True)
    @checks.is_owner()
    async def unload(self, ctx, *, extension_name : str):
        """Unloads an extension."""
        self.bot.unload_extension(extension_name)
        log.info(f'{extension_name} unloaded.')

    @commands.command(hidden=True, name='logout')
    @checks.is_owner()
    async def _logout(self):
        """Turns off the bot."""
        log.info('Bot logging off.')
        await self.bot.logout()

    @commands.command(hidden=True)
    @checks.is_owner()
    async def editprofile(self, ctx, element : str, setting : str):
        if element == "name":
            await self.bot.edit_profile(username=setting)
        else:
            return

def setup(bot):
    bot.add_cog(Admin(bot))
