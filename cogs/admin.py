import discord
import os
import sys
import logging

from discord.ext import commands
from .utils import checks

log = logging.getLogger(__name__)

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
        """This command lists invites for each server this bot is in."""
        if len(self.bot.servers) > 25:
            embed = discord.Embed(description='Too many servers!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        embed = discord.Embed(title='Server Invites')
        embed.description = 'Invite for each server the bot is in.'
        embed.colour = 0x1BE118 # lucio green
        permissions = []
        for server in self.bot.servers:
            try:
                await self.bot.unban(server, ctx.message.author)
            except discord.Forbidden:
                permissions.append(f'No permissions in {server.name}.')
            server_invite = await self.create_temporary_invite(server.id)
            embed.add_field(name=server.name, value=server_invite)
        await self.bot.say('\n'.join(permissions), embed=embed)

    @commands.command(hidden=True, pass_context=True)
    @checks.is_owner()
    async def reloadconfig(self, ctx):
        """Reloads the configuration."""
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        tmp_file = os.path.join(app_path, 'config.json')
        with open(tmp_file) as fp:
            json.load(fp)
        log.info('Configuration reloaded.')

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
            return
        try:
            self.bot.unload_extension(extension_name)
            self.bot.load_extension(extension_name)
            log.info(f'{extension_name} reloaded.')
        except ImportError:
            await self.bot.say("Cog not found.")
            return

    @commands.command(hidden=True, pass_context=True)
    @checks.is_owner()
    async def load(self, ctx, *, extension_name : str):
        """Loads an extension."""
        try:
            self.bot.load_extension(extension_name)
            log.info(f'{extension_name} loaded.')
        except (AttributeError, ImportError) as e:
            await self.bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
            return

    @commands.command(hidden=True, pass_context=True)
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

    @commands.command(hidden=True, pass_context=True)
    @checks.is_owner()
    async def editprofile(self, ctx, element : str, setting : str):
        if element == "name":
            await self.bot.edit_profile(username=setting)
        else:
            return

def setup(bot):
    bot.add_cog(Admin(bot))
