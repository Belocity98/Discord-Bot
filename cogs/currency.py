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

    def user_add_currency(self, server, user, amount):
        currency = self.config.get('currency', {})
        server_id = server.id
        db = currency.get(server_id, {})
        if amount < 0:
            return
        db[user.id] += amount
        currency[server.id] = db
        self.config.put('currency', currency)
        return

    def user_set_currency(self, server, user, amount):
        currency = self.config.get('currency', {})
        server_id = server.id
        db = currency.get(server_id, {})
        if amount < 0:
            return
        db[user.id] = amount
        currency[server.id] = db
        self.config.put('currency', currency)
        return

    def user_remove_currency(self, server, user, amount):
        currency = self.config.get('currency', {})
        server_id = server.id
        db = currency.get(server_id, {})
        if amount < 0:
            return
        if user.id not in db:
            return
        db[user.id] -= amount
        currency[server.id] = db
        self.config.put('currency', currency)
        return


    @commands.command(name='bank', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def currency_bank_account(self, ctx):
        """Display your own bank account for the current server."""
        server = ctx.message.server
        user = ctx.message.author
        bank_embed = self.user_bank_embed(server, user)
        await self.bot.send_message(user, embed=bank_embed)

    @commands.group(pass_context=True, invoke_without_command=False, no_pm=True)
    async def currency(self, ctx, user : discord.Member):
        """Command for adding/removing/setting/viewing a user's currency."""
        log.info('No subcommand entered for currency in {} in {}.'.format(ctx.message.channel.name, ctx.message.server.name))

    @currency.command(name='view', pass_context=True, no_pm=True)
    async def currency_view(self, ctx, user : discord.Member):
        """View a user's currency for the current server."""
        server = ctx.message.server
        bank_embed = self.user_bank_embed(server, user)
        await self.bot.send_message(ctx.message.author, embed=bank_embed)

    @currency.command(name='add', pass_context=True, no_pm=True)
    async def currency_add(self, ctx, user : discord.Member, amount : int):
        """Add currency to a user in the current server."""
        server = ctx.message.server
        self.user_add_currency(server, user, amount)

    @currency.command(name='remove', pass_context=True, no_pm=True)
    async def currency_remove(self, ctx, user : discord.Member, amount : int):
        """Remove currency from a user in the current server."""
        server = ctx.message.server
        self.user_remove_currency(server, user, amount)

    @currency.command(name='set', pass_context=True, no_pm=True)
    async def currency_set(self, ctx, user : discord.Member, amount : int):
        """Set the currency of a user in the current server."""
        server = ctx.message.server
        self.user_set_currency(server, user, amount)

def setup(bot):
    bot.add_cog(Currency(bot))
