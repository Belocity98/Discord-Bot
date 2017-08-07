import discord

from discord.ext import commands
from .utils.menu import Menu



class Settings:

    def __init__(self, bot):
        self.bot = bot

        self.db = bot.db

    @commands.command(name='settings')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _settings(self, ctx):
        """Opens the settings menu.

        If there is no current owner, the owner becomes the first person
        to open the settings menu."""

        guild = ctx.guild
        author = ctx.author

        try:
            self.bot.db['owner']
        except:
            await self.bot.db.put('owner', author.id)

        m = Menu(self.bot, message=ctx.message)

        if m.active:
            return

        await m.menu()

def setup(bot):
    bot.add_cog(Settings(bot))
