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

    def user_bank_embed(self, guild, user):
        currency = self.config.get('currency', {})
        guild_id = guild.id
        db = currency.get(guild_id, {})
        embed = discord.Embed(title=f"{user.name}'s Bank Account")
        embed.description = f'Guild: {guild.name}'
        if user.id not in db:
            embed.add_field(name=self.currency_name, value=f'0 {self.currency_icon}', inline=False)
        else:
            embed.add_field(name=self.currency_name, value=f'{db[user.id]} {self.currency_icon}', inline=False)
        embed.colour = 0x1BE118 # lucio green
        return embed

    def get_shop_embed(self, guild):
        shop = self.config.get('shop', {})
        guild_id = guild.id
        db = shop.get(guild_id, {})

        embed = discord.Embed(title=f"{guild.name}'s Shop")
        embed.description = 'This guild has {} items in the shop.'.format(len(db))
        sortedlist = sorted(db, key=lambda i: int(db[i]))
        sorteddb = OrderedDict()

        for item in sortedlist:
            sorteddb[item] = db[item]

        for item in sorteddb:
            roleobj = discord.utils.get(guild.roles, id=int(item))

            if not roleobj:
                continue

            itemname = roleobj.name
            embed.add_field(name=f'{itemname}', value=f'{sorteddb[item]} {self.currency_name}')

        if len(db) == 0:
            embed.description = 'This guild has no items in the shop.'

        embed.colour = 0x1BE118 # lucio green
        return embed

    async def user_add_currency(self, guild, user, amount):
        currency = self.config.get('currency', {})
        guild_id = guild.id
        db = currency.get(guild_id, {})
        if amount < 0:
            return
        if user.id not in db:
            db[user.id] = 0
        db[user.id] += amount
        currency[guild.id] = db
        await self.config.put('currency', currency)
        return

    async def user_set_currency(self, guild, user, amount):
        currency = self.config.get('currency', {})
        guild_id = guild.id
        db = currency.get(guild_id, {})
        if amount < 0:
            return
        db[user.id] = amount
        currency[guild.id] = db
        await self.config.put('currency', currency)
        return

    async def user_remove_currency(self, guild, user, amount):
        currency = self.config.get('currency', {})
        guild_id = guild.id
        db = currency.get(guild_id, {})
        if amount < 0:
            return False
        if user.id not in db:
            return False
        if db[user.id] < amount:
            return False
        db[user.id] -= amount
        if db[user.id] < 0:
            db[user.id] = 0
        currency[guild.id] = db
        await self.config.put('currency', currency)
        return

    async def user_transfer_currency(self, guild, user1, user2, amount):
        currency = self.config.get('currency', {})
        guild_id = guild.id
        db = currency.get(guild_id, {})
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
        currency[guild.id] = db
        await self.config.put('currency', currency)
        return

    @commands.command(name='bank', no_pm=True)
    async def currency_bank_account(self, ctx):
        """Display your own bank account for the current guild."""
        guild = ctx.guild
        user = ctx.author
        bank_embed = self.user_bank_embed(guild, user)
        await user.send(embed=bank_embed)

    @commands.group(invoke_without_command=False, no_pm=True)
    async def currency(self, ctx):
        """General currency command."""

    @currency.command(name='richest', no_pm=True)
    async def currency_richest(self, ctx):
        """Command for displaying the richest person on the guild."""
        guild = ctx.guild

        currency = self.config.get('currency', {})
        currencydb = currency.get(guild.id, {})
        if len(currencydb) == 0:
            embed = discord.Embed(description='Nobody on this guild has any currency!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        richest_person = guild.get_member(max(currencydb, key=currencydb.get))
        richest_person_amt = currencydb[richest_person.id]
        embed = discord.Embed(description=f'The richest person on this guild is {richest_person.name}, with {richest_person_amt} {self.currency_name}.')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

    @currency.command(name='transfer', no_pm=True)
    async def currency_transfer(self, ctx, user : discord.Member, amount : int):
        """Transfer currency to another user."""
        guild = ctx.guild
        user1 = ctx.author
        user2 = user
        if await self.user_transfer_currency(guild, user1, user2, amount) == False:
            embed = discord.Embed(description='You either do not have enough currency, or entered an invalid amount.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        embed = discord.Embed(description=f'{user.name} sent you {amount} {self.currency_name}!')
        embed.colour = 0x1BE118 # lucio green
        await user2.send(embed=embed)

    @currency.command(name='totalmoney', no_pm=True)
    async def currency_totalmoney(self, ctx):
        """Displays the collective amount of currency in the guild."""
        guild = ctx.guild

        currency = self.config.get('currency', {})
        currencydb = currency.get(guild.id, {})
        total_currency = 0
        if len(currencydb) == 0:
            embed = discord.Embed(description='Nobody on this guild has any currency!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        for key in currencydb:
            total_currency += currencydb[key]
        embed = discord.Embed(description=f'The total amount of money on this guild is: {total_currency} {self.currency_name}.')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

    @currency.command(name='view', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def currency_view(self, ctx, user : discord.Member):
        """View a user's currency for the current guild."""
        guild = ctx.guild
        bank_embed = self.user_bank_embed(guild, user)
        if user == None:
            bank_embed = self.user_bank_embed(guild, ctx.author)
        await ctx.author.send(embed=bank_embed)

    @currency.command(name='add', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def currency_add(self, ctx, user : discord.Member, amount : int):
        """Add currency to a user in the current guild."""
        guild = ctx.guild
        await self.user_add_currency(guild, user, amount)

    @currency.command(name='remove', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def currency_remove(self, ctx, user : discord.Member, amount : int):
        """Remove currency from a user in the current guild."""
        guild = ctx.guild
        await self.user_remove_currency(guild, user, amount)

    @currency.command(name='set', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def currency_set(self, ctx, user : discord.Member, amount : int):
        """Set the currency of a user in the current guild."""
        guild = ctx.guild
        await self.user_set_currency(guild, user, amount)

    @currency.command(name='reset', no_pm=True)
    @commands.has_permissions(administrator=True)
    async def currency_reset(self, ctx):
        """Resets all currency for a guild."""
        guild = ctx.guild
        currency = self.config.get('currency', {})
        db = currency.get(guild.id, {})
        db = {}
        currency[guild.id] = db
        await self.config.put('currency', currency)

    @commands.group(name='shop', invoke_without_command=True, no_pm=True)
    async def shop(self, ctx):
        """Command for purchasing and listing items from the shop."""
        shop_embed = self.get_shop_embed(ctx.guild)
        await ctx.channel.send(embed=shop_embed)

    @shop.command(name='add', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def shop_add(self, ctx, role : discord.Role, amount : int):
        """Command for adding a role to the shop."""
        guild = ctx.guild
        shop = self.config.get('shop', {})
        db = shop.get(guild.id, {})

        if len(db) >= 25:
            log.info('There cannot be more than 25 items in the shop.')
            return

        db[role.id] = amount
        shop[guild.id] = db
        await self.config.put('shop', shop)

    @shop.command(name='remove', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def shop_remove(self, ctx, role : discord.Role):
        """Command for removing a role from the shop."""
        guild = ctx.guild
        shop = self.config.get('shop', {})
        db = shop.get(guild.id, {})
        if role.id in db:
            del db[role.id]
        shop[guild.id] = db
        await self.config.put('shop', shop)

    @shop.command(name='edit', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def shop_edit(self, ctx, role : discord.Role, amount : int):
        """Command for editing a role in the shop."""
        guild = ctx.guild
        shop = self.config.get('shop', {})
        guild_id = guild.id
        db = shop.get(guild.id, {})
        if amount < 0:
            return
        if role.id in db:
            db[role.id] = amount
        shop[guild.id] = db
        await self.config.put('shop', shop)

    @shop.command(name='buy', no_pm=True)
    async def shop_buy(self, ctx, role : discord.Role):
        """Command for buying a role from the shop."""
        guild = ctx.guild
        author = ctx.author

        shop = self.config.get('shop', {})
        shopdb = shop.get(guild.id, {})
        currency = self.config.get('currency', {})
        currencydb = currency.get(guild.id, {})
        if role in author.roles:
            embed = discord.Embed(description='You already have that role!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        if role.id not in shopdb:
            embed = discord.Embed(description='You cannot purchase that role from the shop!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        if author.id not in currencydb:
            embed = discord.Embed(description='You cannot afford that!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        if currencydb[author.id] < shopdb[role.id]:
            embed = discord.Embed(description='You cannot afford that!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        await self.user_remove_currency(guild, author, shopdb[role.id])
        await author.add_roles(role)

    @shop.command(name='sell', no_pm=True)
    async def shop_sell(self, ctx, role : discord.Role):
        """Command for selling a role to the shop."""
        guild = ctx.guild
        author = ctx.author

        shop = self.config.get('shop', {})
        shopdb = shop.get(guild.id, {})
        currency = self.config.get('currency', {})
        currencydb = currency.get(guild.id, {})
        if role not in author.roles:
            embed = discord.Embed(description='You cannot sell a role that you do not have!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        if role.id not in shopdb:
            embed = discord.Embed(description='You cannot sell a role that is not in the shop!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return
        if author.id not in currencydb:
            currencydb[author.id] = 0
            return
        await self.user_add_currency(guild, author, shopdb[role.id]/2)
        await author.remove_roles(role)

    @shop.command(name='removeonbuy', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def shop_rmonbuy(self, ctx, role : discord.Role=None):
        """Toggle for enabling remove role on purchase for a specific role."""
        guild = ctx.guild

        shopitems = self.config.get('shop', {})
        itemsdb = shopitems.get(guild.id, {})

        shop = self.config.get('shop_rmonbuy', {})
        shop_rmonbuy_db = shop.get(guild.id, [])

        if role == None:
            embed = discord.Embed(title='Roles with remove on buy enabled')
            embed.description = f'There are {len(shop_rmonbuy_db)} roles with remove on buy enabled in this guild.'
            role_number = 1
            for role in shop_rmonbuy_db:
                roleobj = discord.utils.get(guild.roles, id=role)
                embed.add_field(name=f'Role {role_number}', value=f'{roleobj.name}')
                role_number += 1
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if role.id not in itemsdb:
            embed = discord.Embed(description='That item is not in the shop!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if role.id in shop_rmonbuy_db:
            shop_rmonbuy_db.remove(role.id)
            shop[guild.id] = shop_rmonbuy_db
            embed = discord.Embed(description=f'{role.name} will no longer remove on purchase.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            await self.config.put('shop_rmonbuy', shop)
            return

        shop_rmonbuy_db.append(role.id)
        shop[guild.id] = shop_rmonbuy_db
        embed = discord.Embed(description=f'{role.name} will now remove on purchase.')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)
        await self.config.put('shop_rmonbuy', shop)

    @shop.command(name='notify', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def shop_notify(self, ctx, role : discord.Role=None):
        """Toggle for enabling notifications on purchase for a specific role."""
        guild = ctx.guild

        shopitems = self.config.get('shop', {})
        itemsdb = shopitems.get(guild.id, {})

        shop = self.config.get('shop_notify', {})
        shop_notify_db = shop.get(guild.id, [])

        if role == None:
            embed = discord.Embed(title='Roles with Notify Enabled')
            embed.description = 'There are {} roles with notify enabled in this guild.'.format(len(shop_notify_db))
            role_number = 1
            for role in shop_notify_db:
                roleobj = discord.utils.get(guild.roles, id=role)
                embed.add_field(name=f'Role {role_number}', value=f'{roleobj.name}')
                role_number += 1
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if role.id not in itemsdb:
            embed = discord.Embed(description='That item is not in the shop!')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if role.id in shop_notify_db:
            shop_notify_db.remove(role.id)
            shop[guild.id] = shop_notify_db
            await self.config.put('shop_notify', shop)
            embed = discord.Embed(description=f'{role.name} will no longer notify on purchase.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        shop_notify_db.append(role.id)
        shop[guild.id] = shop_notify_db
        embed = discord.Embed(description=f'{role.name} will now notify on purchase.')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)
        await self.config.put('shop_notify', shop)

    async def create_shop_notify_channel(self, guild):
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.owner: discord.PermissionOverwrite(read_messages=True)
        }

        await guild.create_text_channel('shop-notify', overwrites=overwrites)
        log.info(f'shop-notify channel created in {guild.name}.')
        return

    async def on_member_update(self, before, after):
        guild = after.guild
        channel = after.guild.default_channel

        shoprmonbuy = self.config.get('shop_rmonbuy', {})
        shopnotify = self.config.get('shop_notify', {})
        shopitems = self.config.get('shop', {})

        items_db = shopitems.get(guild.id, {})
        rmonbuy_db = shoprmonbuy.get(guild.id, [])
        notify_db = shopnotify.get(guild.id, [])


        can_make_c = channel.permissions_for(guild.me).manage_channels
        shop_notify_channel = discord.utils.find(lambda c: c.name == 'shop-notify', guild.channels)
        if shop_notify_channel == None and can_make_c:
            if notify_db:
                shop_notify_channel = await self.create_shop_notify_channel(guild)

        if before.guild != after.guild:
            log.info('Before and after guild are not the same.')

        for role in notify_db:
            roleobj = discord.utils.get(guild.roles, id=role)
            if roleobj in after.roles:
                embed = discord.Embed(description=f'{after.name} ({after}) bought {roleobj.name} in {after.guild.name}.')
                embed.colour = 0x1BE118 # lucio green
                await shop_notify_channel.send(embed=embed)

        for role in rmonbuy_db:
            roleobj = discord.utils.get(guild.roles, id=role)
            if roleobj in after.roles:
                await after.remove_roles(roleobj)


def setup(bot):
    bot.add_cog(Currency(bot))
