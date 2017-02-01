import discord
import os
import sys
import logging
import asyncio

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

    def get_shop_embed(self, server):
        shop = self.config.get('shop', {})
        server_id = server.id
        db = shop.get(server_id, {})

        embed = discord.Embed(title="{}'s Shop".format(server.name))
        embed.description = 'This server has {} items in the shop.'.format(len(db))
        for item in db:
            roleobj = discord.utils.get(server.roles, id=item)
            itemname = roleobj.name
            embed.add_field(name='{}'.format(itemname), value='{} {}'.format(db[item], self.currency_name))
        if len(db) == 0:
            embed.description = 'This server has no items in the shop.'
        embed.colour = 0x1BE118 # lucio green
        return embed

    async def user_add_currency(self, server, user, amount):
        currency = self.config.get('currency', {})
        server_id = server.id
        db = currency.get(server_id, {})
        if amount < 0:
            return
        if user.id not in db:
            db[user.id] = 0
        db[user.id] += amount
        currency[server.id] = db
        await self.config.put('currency', currency)
        return

    async def user_set_currency(self, server, user, amount):
        currency = self.config.get('currency', {})
        server_id = server.id
        db = currency.get(server_id, {})
        if amount < 0:
            return
        db[user.id] = amount
        currency[server.id] = db
        await self.config.put('currency', currency)
        return

    async def user_remove_currency(self, server, user, amount):
        currency = self.config.get('currency', {})
        server_id = server.id
        db = currency.get(server_id, {})
        if amount < 0:
            return False
        if user.id not in db:
            return False
        db[user.id] -= amount
        if db[user.id] < 0:
            db[user.id] = 0
        currency[server.id] = db
        await self.config.put('currency', currency)
        return

    async def user_transfer_currency(self, server, user1, user2, amount):
        currency = self.config.get('currency', {})
        server_id = server.id
        db = currency.get(server_id, {})
        if amount < 0:
            return False
        if user1.id not in db:
            return False
        if user2.id not in db:
            db[user2.id] = 0
        if db[user1.id] < amount:
            return False
        db[user1.id] -= amount
        db[user2.id] += amount
        currency[server.id] = db
        await self.config.put('currency', currency)
        return

    @commands.command(name='bank', pass_context=True, no_pm=True)
    async def currency_bank_account(self, ctx):
        """Display your own bank account for the current server."""
        server = ctx.message.server
        user = ctx.message.author
        bank_embed = self.user_bank_embed(server, user)
        await self.bot.send_message(user, embed=bank_embed)

    @commands.command(name='transfer', pass_context=True, no_pm=True)
    async def currency_transfer(self, ctx, user : discord.Member, amount : int):
        """Transfer currency to another user."""
        server = ctx.message.server
        user1 = ctx.message.author
        user2 = user
        if await self.user_transfer_currency(server, user1, user2, amount) == False:
            embed = discord.Embed(description='You either do not have enough currency, or entered an invalid amount.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        embed = discord.Embed(description='{} sent you {} {}!'.format(user.name, amount, self.currency_name))
        embed.colour = 0x1BE118 # lucio green
        await self.bot.send_message(user2, embed=embed)

    @commands.group(pass_context=True, invoke_without_command=False, no_pm=True)
    async def currency(self, ctx):
        """Command for adding/removing/setting/viewing a user's currency."""

    @currency.command(name='view', pass_context=True, no_pm=True)
    async def currency_view(self, ctx, user : discord.Member):
        """View a user's currency for the current server."""
        server = ctx.message.server
        bank_embed = self.user_bank_embed(server, user)
        if user == None:
            bank_embed = self.user_bank_embed(server, ctx.message.author)
        await self.bot.send_message(ctx.message.author, embed=bank_embed)

    @currency.command(name='add', pass_context=True, no_pm=True)
    async def currency_add(self, ctx, user : discord.Member, amount : int):
        """Add currency to a user in the current server."""
        server = ctx.message.server
        await self.user_add_currency(server, user, amount)

    @currency.command(name='remove', pass_context=True, no_pm=True)
    async def currency_remove(self, ctx, user : discord.Member, amount : int):
        """Remove currency from a user in the current server."""
        server = ctx.message.server
        await self.user_remove_currency(server, user, amount)

    @currency.command(name='set', pass_context=True, no_pm=True)
    async def currency_set(self, ctx, user : discord.Member, amount : int):
        """Set the currency of a user in the current server."""
        server = ctx.message.server
        await self.user_set_currency(server, user, amount)

    @currency.command(name='reset', pass_context=True, no_pm=True)
    async def currency_reset(self, ctx):
        """Resets all currency for a server."""
        server = ctx.message.server
        currency = self.config.get('currency', {})
        db = currency.get(server.id, {})
        db = {}
        currency[server.id] = db
        await self.config.put('currency', currency)

    @commands.group(name='shop', pass_context=True, invoke_without_command=True, no_pm=True)
    async def shop(self, ctx):
        """Command for purchasing and listing items from the shop."""
        shop_embed = self.get_shop_embed(ctx.message.server)
        await self.bot.say(embed=shop_embed)

    @shop.command(name='add', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def shop_add(self, ctx, role : discord.Role, amount : int):
        """Command for adding a role to the shop."""
        server = ctx.message.server
        shop = self.config.get('shop', {})
        server_id = server.id
        db = shop.get(server.id, {})
        db[role.id] = amount
        shop[server.id] = db
        await self.config.put('shop', shop)

    @shop.command(name='remove', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def shop_remove(self, ctx, role : discord.Role):
        """Command for removing a role from the shop."""
        server = ctx.message.server
        shop = self.config.get('shop', {})
        server_id = server.id
        db = shop.get(server.id, {})
        if role.id in db:
            del db[role.id]
        shop[server.id] = db
        await self.config.put('shop', shop)

    @shop.command(name='edit', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def shop_edit(self, ctx, role : discord.Role, amount : int):
        """Command for editing a role in the shop."""
        server = ctx.message.server
        shop = self.config.get('shop', {})
        server_id = server.id
        db = shop.get(server.id, {})
        if amount < 0:
            return
        if role.id in db:
            db[role.id] = amount
        shop[server.id] = db
        await self.config.put('shop', shop)

    @shop.command(name='buy', pass_context=True, no_pm=True)
    async def shop_buy(self, ctx, role : discord.Role):
        """Command for buying a role from the shop."""
        server = ctx.message.server
        author = ctx.message.author

        shop = self.config.get('shop', {})
        shopdb = shop.get(server.id, {})
        currency = self.config.get('currency', {})
        currencydb = currency.get(server.id, {})
        if role in author.roles:
            embed = discord.Embed(description='You already have that role!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        if role.id not in shopdb:
            embed = discord.Embed(description='You cannot purchase that role from the shop!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        if author.id not in currencydb:
            embed = discord.Embed(description='You cannot afford that!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        if currencydb[author.id] < shopdb[role.id]:
            embed = discord.Embed(description='You cannot afford that!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        await self.user_remove_currency(server, author, shopdb[role.id])
        await self.bot.add_roles(author, role)

    @shop.command(name='sell', pass_context=True, no_pm=True)
    async def shop_sell(self, ctx, role : discord.Role):
        """Command for selling a role to the shop."""
        server = ctx.message.server
        author = ctx.message.author

        shop = self.config.get('shop', {})
        shopdb = shop.get(server.id, {})
        currency = self.config.get('currency', {})
        currencydb = currency.get(server.id, {})
        if role not in author.roles:
            embed = discord.Embed(description='You cannot sell a role that you do not have!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        if role.id not in shopdb:
            embed = discord.Embed(description='You cannot sell a role that is not in the shop!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        if author.id not in currencydb:
            currencydb[author.id] = 0
            return
        await self.user_add_currency(server, author, shopdb[role.id]/2)
        await self.bot.remove_roles(author, role)

def setup(bot):
    bot.add_cog(Currency(bot))
