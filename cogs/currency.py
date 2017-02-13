import discord
import os
import sys
import logging
import asyncio

from discord.ext import commands
from .utils import config, checks
from collections import OrderedDict

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
        embed = discord.Embed(title=f"{user.name}'s Bank Account")
        embed.description = f'Server: {server.name}'
        if user.id not in db:
            embed.add_field(name=self.currency_name, value=f'0 {self.currency_icon}', inline=False)
        else:
            embed.add_field(name=self.currency_name, value=f'{db[user.id]} {self.currency_icon}', inline=False)
        embed.colour = 0x1BE118 # lucio green
        return embed

    def get_shop_embed(self, server):
        shop = self.config.get('shop', {})
        server_id = server.id
        db = shop.get(server_id, {})

        embed = discord.Embed(title=f"{server.name}'s Shop")
        embed.description = 'This server has {} items in the shop.'.format(len(db))
        sortedlist = sorted(db, key=lambda i: int(db[i]))
        sorteddb = OrderedDict()

        for item in sortedlist:
            sorteddb[item] = db[item]

        for item in sorteddb:
            roleobj = discord.utils.get(server.roles, id=item)
            itemname = roleobj.name
            embed.add_field(name=f'{itemname}', value=f'{sorteddb[item]} {self.currency_name}')

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
        if db[user.id] < amount:
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

    @commands.group(pass_context=True, invoke_without_command=False, no_pm=True)
    async def currency(self, ctx):
        """General currency command."""

    @currency.command(name='richest', pass_context=True, no_pm=True)
    async def currency_richest(self, ctx):
        """Command for displaying the richest person on the server."""
        server = ctx.message.server

        currency = self.config.get('currency', {})
        currencydb = currency.get(server.id, {})
        if len(currencydb) == 0:
            embed = discord.Embed(description='Nobody on this server has any currency!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        richest_person = server.get_member(max(currencydb, key=currencydb.get))
        richest_person_amt = currencydb[richest_person.id]
        embed = discord.Embed(description=f'The richest person on this server is {richest_person.name}, with {richest_person_amt} {self.currency_name}.')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

    @currency.command(name='transfer', pass_context=True, no_pm=True)
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
        embed = discord.Embed(description=f'{user.name} sent you {amount} {self.currency_name}!')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.send_message(user2, embed=embed)

    @currency.command(name='totalmoney', pass_context=True, no_pm=True)
    async def currency_totalmoney(self, ctx):
        """Displays the collective amount of currency in the server."""
        server = ctx.message.server

        currency = self.config.get('currency', {})
        currencydb = currency.get(server.id, {})
        total_currency = 0
        if len(currencydb) == 0:
            embed = discord.Embed(description='Nobody on this server has any currency!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        for key in currencydb:
            total_currency += currencydb[key]
        embed = discord.Embed(description=f'The total amount of money on this server is: {total_currency} {self.currency_name}.')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

    @currency.command(name='view', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def currency_view(self, ctx, user : discord.Member):
        """View a user's currency for the current server."""
        server = ctx.message.server
        bank_embed = self.user_bank_embed(server, user)
        if user == None:
            bank_embed = self.user_bank_embed(server, ctx.message.author)
        await self.bot.send_message(ctx.message.author, embed=bank_embed)

    @currency.command(name='add', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def currency_add(self, ctx, user : discord.Member, amount : int):
        """Add currency to a user in the current server."""
        server = ctx.message.server
        await self.user_add_currency(server, user, amount)

    @currency.command(name='remove', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def currency_remove(self, ctx, user : discord.Member, amount : int):
        """Remove currency from a user in the current server."""
        server = ctx.message.server
        await self.user_remove_currency(server, user, amount)

    @currency.command(name='set', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def currency_set(self, ctx, user : discord.Member, amount : int):
        """Set the currency of a user in the current server."""
        server = ctx.message.server
        await self.user_set_currency(server, user, amount)

    @currency.command(name='reset', pass_context=True, no_pm=True)
    @commands.has_permissions(administrator=True)
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
        db = shop.get(server.id, {})

        if len(db) >= 25:
            log.info('There cannot be more than 25 items in the shop.')
            return

        db[role.id] = amount
        shop[server.id] = db
        await self.config.put('shop', shop)

    @shop.command(name='remove', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def shop_remove(self, ctx, role : discord.Role):
        """Command for removing a role from the shop."""
        server = ctx.message.server
        shop = self.config.get('shop', {})
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

    @shop.command(name='removeonbuy', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def shop_rmonbuy(self, ctx, role : discord.Role=None):
        """Toggle for enabling remove role on purchase for a specific role."""
        server = ctx.message.server

        shopitems = self.config.get('shop', {})
        itemsdb = shopitems.get(server.id, {})

        shop = self.config.get('shop_rmonbuy', {})
        shop_rmonbuy_db = shop.get(server.id, [])

        if role == None:
            embed = discord.Embed(title='Roles with remove on buy enabled')
            embed.description = f'There are {len(shop_rmonbuy_db)} roles with remove on buy enabled in this server.'
            role_number = 1
            for role in shop_rmonbuy_db:
                roleobj = discord.utils.get(server.roles, id=role)
                embed.add_field(name=f'Role {role_number}', value=f'{roleobj.name}')
                role_number += 1
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if role.id not in itemsdb:
            embed = discord.Embed(description='That item is not in the shop!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if role.id in shop_rmonbuy_db:
            shop_rmonbuy_db.remove(role.id)
            shop[server.id] = shop_rmonbuy_db
            embed = discord.Embed(description=f'{role.name} will no longer remove on purchase.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            await self.config.put('shop_rmonbuy', shop)
            return

        shop_rmonbuy_db.append(role.id)
        shop[server.id] = shop_rmonbuy_db
        embed = discord.Embed(description=f'{role.name} will now remove on purchase.')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)
        await self.config.put('shop_rmonbuy', shop)

    @shop.command(name='notify', pass_context=True, no_pm=True)
    @commands.has_permissions(manage_server=True)
    async def shop_notify(self, ctx, role : discord.Role=None):
        """Toggle for enabling notifications on purchase for a specific role."""
        server = ctx.message.server

        shopitems = self.config.get('shop', {})
        itemsdb = shopitems.get(server.id, {})

        shop = self.config.get('shop_notify', {})
        shop_notify_db = shop.get(server.id, [])

        if role == None:
            embed = discord.Embed(title='Roles with Notify Enabled')
            embed.description = 'There are {} roles with notify enabled in this server.'.format(len(shop_notify_db))
            role_number = 1
            for role in shop_notify_db:
                roleobj = discord.utils.get(server.roles, id=role)
                embed.add_field(name=f'Role {role_number}', value=f'{roleobj.name}')
                role_number += 1
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if role.id not in itemsdb:
            embed = discord.Embed(description='That item is not in the shop!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if role.id in shop_notify_db:
            shop_notify_db.remove(role.id)
            shop[server.id] = shop_notify_db
            await self.config.put('shop_notify', shop)
            embed = discord.Embed(description=f'{role.name} will no longer notify on purchase.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        shop_notify_db.append(role.id)
        shop[server.id] = shop_notify_db
        embed = discord.Embed(description=f'{role.name} will now notify on purchase.')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)
        await self.config.put('shop_notify', shop)

    async def create_shop_notify_channel(self, server):
        everyone_perms = discord.PermissionOverwrite(read_messages=False)
        my_perms = discord.PermissionOverwrite(read_messages=True)
        everyone = discord.ChannelPermissions(target=server.default_role, overwrite=everyone_perms)
        mine = discord.ChannelPermissions(target=server.owner, overwrite=my_perms)

        await self.bot.create_channel(server, 'shop-notify', everyone, mine)
        log.info(f'shop-notify channel created in {server.name}.')
        return

    async def on_member_update(self, before, after):
        server = after.server
        channel = after.server.default_channel

        shoprmonbuy = self.config.get('shop_rmonbuy', {})
        shopnotify = self.config.get('shop_notify', {})
        shopitems = self.config.get('shop', {})

        items_db = shopitems.get(server.id, {})
        rmonbuy_db = shoprmonbuy.get(server.id, [])
        notify_db = shopnotify.get(server.id, [])


        can_make_c = channel.permissions_for(server.me).manage_channels
        shop_notify_channel = discord.utils.find(lambda c: c.name == 'shop-notify', server.channels)
        if shop_notify_channel == None and can_make_c:
            shop_notify_channel = await self.create_shop_notify_channel(server)

        if before.server != after.server:
            log.info('Before and after server are not the same.')

        for role in notify_db:
            roleobj = discord.utils.get(server.roles, id=role)
            if roleobj in after.roles:
                embed = discord.Embed(description=f'{after.name} ({after}) bought {roleobj.name} in {after.server.name}.')
                embed.colour = 0x1BE118 # lucio green
                await self.bot.send_message(shop_notify_channel, embed=embed)

        for role in rmonbuy_db:
            roleobj = discord.utils.get(server.roles, id=role)
            if roleobj in after.roles:
                await self.bot.remove_roles(after, roleobj)


def setup(bot):
    bot.add_cog(Currency(bot))
