import discord
import os
import sys
import logging

from discord.ext import commands
from .utils import config, checks

log = logging.getLogger(__name__)

class Currency():

    def __init__(self, bot):
        self.bot = bot
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        cfgfile = os.path.join(app_path, 'currency.json')
        self.config = config.Config(cfgfile, loop=bot.loop)

        self.currency_name = 'Gems'
        self.currency_icon = '💎'

    def user_bank_embed(self, server, user):
        currency = self.config.get('currency', {})
        server_id = server.id
        db = currency.get(server_id, {})
        embed = discord.Embed(title="{}'s Bank Account".format(user.name))
        embed.description = 'Server: {}'.format(server.name)
        if user.id not in db:
            embed.add_field(name=self.currency_name, value='0 {}'.format(self.currency_icon), inline=False)
        else:
            embed.add_field(name=self.currency_name, value='{} {}'.format(db[user.id], self.currency_icon), inline=False)
        embed.colour = 0x1BE118 # lucio green
        return embed

    @commands.command(name='bank', pass_context=True, no_pm=True)
    async def currency_bank_account(self, ctx):
        server = ctx.message.server
        user = ctx.message.author
        bank_embed = self.user_bank_embed(server, user)
        await self.bot.send_message(user, embed=bank_embed)


def setup(bot):
    bot.add_cog(Currency(bot))
