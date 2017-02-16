import discord
import os
import sys
import logging
import json

from discord.ext import commands
from .utils import checks

log = logging.getLogger(__name__)

class Admin():

    def __init__(self, bot):
        self.bot = bot


        data = await http.post(url, json=payload, bucket='create_invite')
        return 'http://discord.gg/' + data['code']

    @commands.command(hidden=True)
    @checks.is_owner()
    async def invites(self, ctx):
        """This command lists invites for each guild this bot is in."""
        if len(self.bot.guilds) > 25:
            embed = discord.Embed(description='Too many guilds!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        embed = discord.Embed(title='Guild Invites')
        embed.description = 'Invite for each guild the bot is in.'
        embed.colour = 0x1BE118 # lucio green
        permissions = []
        for guild in self.bot.guilds:
            try:
                await guild.unban(ctx.author)
            except discord.Forbidden:
                permissions.append(f'No permissions in {guild.name}.')
            try:
                guild_invite = await guild.create_invite(unique=True, max_uses=1)
                embed.add_field(name=guild.name, value=guild_invite)
            except discord.Forbidden:
                embed.add_field(name=guild.name, value='No Invite')

        await ctx.channel.send('\n'.join(permissions), embed=embed)

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
