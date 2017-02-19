import discord
import asyncio
import json
import os
import sys
import logging

from discord.ext import commands
from .utils import config, checks

log = logging.getLogger(__name__)

class Mod():

    def __init__(self, bot):
        self.bot = bot
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        cfgfile = os.path.join(app_path, 'mod.json')
        cfgfile2 = os.path.join(app_path, 'banned_cache.json')
        self.config = config.Config(cfgfile, loop=bot.loop)
        self.tmp_banned_cache = config.Config(cfgfile2, loop=bot.loop)

        self.prefixes = bot.prefixes

    def is_plonked(self, guild, member):
        db = self.config.get('plonks', {}).get(guild.id, [])
        bypass_ignore = member.guild_permissions.manage_guild
        if not bypass_ignore and member.id in db:
            return True
        return False

    def __check(self, ctx):
        msg = ctx.message

        if checks.is_owner_check(ctx):
            return True

        if msg.guild:
            if self.is_plonked(msg.guild, msg.author):
                return False

        return True

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, user : discord.Member, length : int, *, reason=None):
        """Temp ban a user for a specified amount of time."""
        max_ban_length = int(self.bot.config["mod"]["max_ban_length"])

        if length > max_ban_length:
            embed = discord.Embed(description=f'You cannot ban users for more than {max_ban_length} seconds.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        guild = ctx.guild
        author = ctx.author

        embed = discord.Embed(title=f"{user.name} has been banned.")
        embed.colour = 0x1BE118 # lucio green
        embed.add_field(name="By", value=str(author))
        embed.add_field(name="For", value=str(length) + " seconds")
        await ctx.channel.send(embed=embed)

        log.info(f'{author.name} banned {user.name} for {length} seconds from {guild.name}.')
        if reason == None:
            await self.ban_func(guild, user, length=length)
        else:
            await self.ban_func(guild, user, length=length, message=reason)

    @commands.command(no_pm=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, limit : int):
        """Remove a specified amount of messages from the chat."""
        channel = ctx.channel
        guild = ctx.guild

        delete_limit = int(self.bot.config["mod"]["purge_limit"])
        if limit > delete_limit:
            embed = discord.Embed(description=f"Only up to {delete_limit} messages can be deleted at a time.")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        await channel.purge(limit=limit)
        author = ctx.author
        log.info(f'{author.name} purged {limit} messages from {channel.name} in {guild.name}.')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def massmove(self, ctx):
        """Move all voice connected users to the author's channel."""
        guild = ctx.guild
        channel = ctx.channel
        author = ctx.author
        members = self.bot.get_all_members()

        can_move = channel.permissions_for(guild.me).move_members
        if can_move:

            lines = []
            for member in members:
                if member.voice_channel != None:
                    lines.append(member)

            for member in lines:
                await member.edit(voice_channel=author.voice_channel)
            log.info(f'{author.name} massmoved all members to {channel.name} in {guild.name}.')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def voicestate(self, ctx, destination : str, voicestate : str):
        """Mute or unmute all voice connected members of the channel or guild."""
        guild = ctx.guild
        members = self.bot.get_all_members()

        lines = []
        if destination == "channel":
            for member in members:
                if member.voice_channel == ctx.author.voice_channel:
                    lines.append(member)

        elif destination == "guild":
            for member in members:
                if (member.voice_channel != None) and (member.voice_channel != ctx.guild.afk_channel ):
                    lines.append(member)

        else:
            embed = discord.Embed(description="Destination not recognized. Expected channel/guild.")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if voicestate == "mute":
            for member in lines:
                await self.bot.guild_voice_state(member, mute=True)

        elif voicestate == "unmute":
            for member in lines:
                await self.bot.guild_voice_state(member, mute=False)

        else:
            embed = discord.Embed(description="Voicestate not recognized. Expected mute/unmute.")
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

    @commands.command(no_pm=True)
    @commands.has_permissions(manage_messages=True)
    async def banchat(self, ctx, *, msg : str):
        """Ban a word or phrase from being entered into the current guild."""

        banned_chat = self.config.get('banned_chat', {})
        guild_id = ctx.guild.id
        db = banned_chat.get(guild_id, [])

        if msg.lower() in db:
            embed = discord.Embed(description='Message already banned.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        db.append(msg.lower())
        banned_chat[guild_id] = db
        await self.config.put('banned_chat', banned_chat)

        embed = discord.Embed(description='Message banned.')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

    @commands.command(no_pm=True)
    @commands.has_permissions(manage_messages=True)
    async def unbanchat(self, ctx, *, msg : str):
        """Unban a word or phrase from being entered into the current guild."""

        banned_chat = self.config.get('banned_chat', {})
        guild_id = ctx.guild.id
        db = banned_chat.get(guild_id, [])

        if msg == 'all':
            db = []
            banned_chat[guild_id] = db
            await self.config.put('banned_chat', banned_chat)

            embed = discord.Embed(description='Unbanned all messages.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        if msg not in db:
            embed = discord.Embed(description='Message not found in banned messages list.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        db.remove(msg.lower())
        banned_chat[guild_id] = db
        await self.config.put('banned_chat', banned_chat)

        embed = discord.Embed(description='Message unbanned.')
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

    @commands.command(no_pm=True)
    async def bannedchat(self, ctx):
        """View list of banned messages on the current guild."""

        banned_chat = self.config.get('banned_chat', {})
        guild_id = ctx.guild.id
        db = banned_chat.get(guild_id, [])

        embed = discord.Embed(description='This guild currently has {} banned messages.'.format(len(db)))
        if len(db) > 25:
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        embed.title = 'Banned Messages'
        msgnumber = 1

        for item in db:
            embed.add_field(name=f'Message {msgnumber}', value=item)
            msgnumber += 1

        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

    @commands.command(no_pm=True)
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx, *, prefix : str):
        """Sets the prefix for the bot on the current guild."""

        guild_prefixes = self.prefixes.get('prefixes', {})

        guild_prefixes[ctx.guild.id] = prefix

        await self.prefixes.put('prefixes', guild_prefixes)

    @commands.command(no_pm=True)
    @checks.is_owner()
    async def plonk(self, ctx, *, member: discord.Member):
        """Bans a user from using the bot in a guild."""

        plonks = self.config.get('plonks', {})
        guild_id = ctx.guild.id
        db = plonks.get(guild_id, [])

        if member.id in db:
            embed = discord.Embed(description='That user is already bot banned in this guild.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
            return

        db.append(member.id)
        plonks[guild_id] = db
        await self.config.put('plonks', plonks)
        embed = discord.Embed(description='%s has been banned from using the bot in this guild.' % member)
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

    @commands.command(no_pm=True)
    @checks.is_owner()
    async def unplonk(self, ctx, *, member: discord.Member):
        """Unbans a user from using the bot."""

        plonks = self.config.get('plonks', {})
        guild_id = ctx.guild.id
        db = plonks.get(guild_id, [])

        try:
            db.remove(member.id)
        except ValueError:
            embed = discord.Embed(description='%s is not banned from using the bot in this guild.' % member)
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)
        else:
            plonks[guild_id] = db
            await self.config.put('plonks', plonks)
            embed = discord.Embed(description='%s has been unbanned from using the bot in this guild.' % member)
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)

    @commands.command(no_pm=True)
    @checks.is_owner()
    async def plonks(self, ctx):
        """Shows members banned from the bot."""
        plonks = self.config.get('plonks', {})
        guild = ctx.guild
        db = plonks.get(guild.id, [])
        members = ', '.join(map(str, filter(None, map(guild.get_member, db))))
        if members:
            await ctx.channel.send(members)
        else:
            embed = discord.Embed(description='No members are banned in this guild.')
            embed.colour = 0x1BE118 # lucio green
            await ctx.channel.send(embed=embed)

    async def ban_func(self, guild, user, message="No reason given.", length=10):

        bans = self.tmp_banned_cache.get('bans', {})
        db = bans.get(guild.id, {})
        memberinfo = db.get(user.id, {})

        buserroles = []
        for role in user.roles[1:]:
            buserroles.append(role.id)

        memberinfo['roles'] = buserroles
        memberinfo['nick'] = user.nick

        db[user.id] = memberinfo
        bans[guild.id] = db
        await self.tmp_banned_cache.put('bans', bans)

        invite = await guild.create_invite(unique=True, max_uses=1)
        embed = discord.Embed(description='**You have been banned!**')
        embed.add_field(name='Reason', value=message)
        embed.add_field(name='Length', value=f'{length} seconds')
        embed.add_field(name='Invite', value=f"After your ban time is over, click this link to rejoin the guild.\nInvite: {invite}")
        embed.set_footer(text='Banned', icon_url='http://i.imgur.com/wBkQqOp.png')
        embed.colour = 0x1BE118 # lucio green

        await user.send(embed=embed)

        await guild.ban(user, delete_message_days=0)
        await asyncio.sleep(length)
        await guild.unban(user)
        embed = discord.Embed(description=f"{user.name} has been unbanned.")
        embed.colour = 0x1BE118 # lucio green
        await ctx.channel.send(embed=embed)

    async def on_member_join(self, member):

        bans = self.tmp_banned_cache.get('bans', {})
        db = bans.get(member.guild.id, {})

        if member.id in db:

            memberinfo = db.get(member.id, {})

            role_objects = []
            for role in memberinfo['roles']:
                role_objects.append(discord.utils.get(member.guild.roles, id=role))

            await member.add_roles(*role_objects)

            await member.edit(nick=memberinfo['nick'])

            del db[member.id]
            bans[member.guild.id] = db
            await self.tmp_banned_cache.put('bans', bans)

    async def on_message(self, message):

        if message.guild is None:
            return

        banned_chat = self.config.get('banned_chat', {})
        guild_id = message.guild.id
        banned_chat_list = banned_chat.get(guild_id, [])

        if any(word in message.content.lower() for word in banned_chat_list):
            embed = discord.Embed(description='You used a word or phrase that is banned in this guild!')
            embed.colour = 0x1BE118 # lucio green
            await message.author.send(embed=embed)
            await message.delete()

def setup(bot):
    bot.add_cog(Mod(bot))
