from discord.ext import commands
import discord
import os
import sys
import json

class Admin():

    def __init__(self, bot):
        self.bot = bot
        # list of all cogs
        self.all_cogs = [
            "cogs.games",
            "cogs.mod",
            "cogs.misc",
            "cogs.stats",
            "cogs.admin",
            "cogs.reddit",
            "cogs.logging"
        ]

    @commands.command(hidden=True, pass_context=True)
    @commands.has_permissions(administrator=True)
    async def reloadconfig(self, ctx):
        """Reloads the configuration."""
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        config_file = os.path.join(app_path, 'config.json')
        with open(config_file) as fp:
            self.bot.config = json.load(fp)
        llog = "Configuration reloaded."
        await self.bot.get_cog("Logging").do_logging(llog, channel=ctx.message.channel)

    @commands.command(name='reload', hidden=True, pass_context=True)
    @commands.has_permissions(administrator=True)
    async def _reload(self, ctx, *, extension_name : str):
        """Reloads an extension."""
        if extension_name == "all":
            for cog in self.all_cogs:
                try:
                    self.bot.unload_extension(cog)
                    self.bot.load_extension(cog)
                except (AttributeError, ImportError) as e:
                    await self.bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            llog = "All cogs reloaded."
            await self.bot.get_cog("Logging").do_logging(llog, channel=ctx.message.channel)
            return
        try:
            self.bot.unload_extension(extension_name)
            self.bot.load_extension(extension_name)
        except ImportError:
            await self.bot.say("Cog not found.")
            return
        llog = "{} reloaded.".format(extension_name)
        await self.bot.get_cog("Logging").do_logging(llog, channel=ctx.message.channel)

    @commands.command(hidden=True, pass_context=True)
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, *, extension_name : str):
        """Loads an extension."""
        try:
            self.bot.load_extension(extension_name)
        except (AttributeError, ImportError) as e:
            await self.bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            return
        llog = "{} loaded.".format(extension_name)
        await self.bot.get_cog("Logging").do_logging(llog, channel=ctx.message.channel)

    @commands.command(hidden=True, pass_context=True)
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx, *, extension_name : str):
        """Unloads an extension."""
        self.bot.unload_extension(extension_name)
        await self.bot.say("{} unloaded.".format(extension_name))
        llog = "{} unloaded.".format(extension_name)
        await self.bot.get_cog("Logging").do_logging(llog, channel=ctx.message.channel)

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def logout(self):
        """Turns off the bot."""
        await self.bot.logout()

def setup(bot):
    bot.add_cog(Admin(bot))
