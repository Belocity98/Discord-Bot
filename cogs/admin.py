from discord.ext import commands
import discord
import os
import sys

from .utils import checks, cjson

class Admin():

    def __init__(self, bot):
        self.bot = bot

    async def create_temporary_invite(self, channel_id):
        http = self.bot.http
        url = '{0.CHANNELS}/{1}/invites'.format(http, channel_id)
        payload = {
            'max_age' : 0,
            'max_uses' : 1,
            'temporary' : False,
            'unique' : True
        }

        data = await http.post(url, json=payload, bucket='create_invite')
        return 'http://discord.gg/' + data['code']

    @commands.command(hidden=True, pass_context=True)
    @checks.is_owner()
    async def invites(self, ctx):
        invites = []
        for server in self.bot.servers:
            server_invite = await self.create_temporary_invite(server.id)
            invites.append('{}: {}'.format(server.name, server_invite))
        await self.bot.say('\n'.join(invites))

    @commands.command(hidden=True, pass_context=True)
    @checks.is_owner()
    async def reloadconfig(self, ctx):
        """Reloads the configuration."""
        self.bot.config = cjson.open_json("load", 'config.json')
        llog = "Configuration reloaded."
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server, channel=ctx.message.channel)

    @commands.command(name='reload', hidden=True, pass_context=True)
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
                    await self.bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            llog = "All cogs reloaded."
            await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server, channel=ctx.message.channel)
            return
        try:
            self.bot.unload_extension(extension_name)
            self.bot.load_extension(extension_name)
        except ImportError:
            await self.bot.say("Cog not found.")
            return
        llog = "{} reloaded.".format(extension_name)
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server, channel=ctx.message.channel)

    @commands.command(hidden=True, pass_context=True)
    @checks.is_owner()
    async def load(self, ctx, *, extension_name : str):
        """Loads an extension."""
        try:
            self.bot.load_extension(extension_name)
        except (AttributeError, ImportError) as e:
            await self.bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            return
        llog = "{} loaded.".format(extension_name)
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server, channel=ctx.message.channel)

    @commands.command(hidden=True, pass_context=True)
    @checks.is_owner()
    async def unload(self, ctx, *, extension_name : str):
        """Unloads an extension."""
        self.bot.unload_extension(extension_name)
        llog = "{} unloaded.".format(extension_name)
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server, channel=ctx.message.channel)

    @commands.command(hidden=True)
    @checks.is_owner()
    async def logout(self):
        """Turns off the bot."""
        await self.bot.logout()

    @commands.command(hidden=True, pass_context=True)
    @checks.is_owner()
    async def editprofile(self, ctx, element : str, setting : str):
        if element == "name":
            await self.bot.edit_profile(username=setting)
        else:
            return

def setup(bot):
    bot.add_cog(Admin(bot))
