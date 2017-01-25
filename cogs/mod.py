from discord.ext import commands
from .utils import config

import discord
import asyncio
import json
import os
import sys

class Mod():

    def __init__(self, bot):
        self.bot = bot
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        cfgfile = os.path.join(app_path, 'mod.json')
        self.config = config.Config(cfgfile, loop=bot.loop)

    @commands.command(pass_context=True)
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, user : discord.Member, length : int, reason=None):
        """Temp ban a user for a specified amount of time."""
        server = ctx.message.server
        author = ctx.message.author
        embed = discord.Embed(title="{} has been banned.".format(str(user)))
        embed.colour = 0x1BE118 # lucio green
        embed.add_field(name="By", value=str(author))
        embed.add_field(name="For", value=str(length) + " seconds")
        await self.bot.say(embed=embed)
        if reason == None:
            await self.ban_func(server, user, length=length)
        else:
            await self.ban_func(server, user, length=length, message=reason)
        llog = "{} banned {} for {} seconds.".format(str(ctx.message.author), str(user), str(length))
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @commands.command(pass_context=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, limit : int):
        """Remove a specified amount of messages from the chat."""
        delete_limit = int(self.bot.config["mod"]["purge_limit"])
        if limit > delete_limit:
            embed = discord.Embed(description="Only up to {} messages can be deleted at a time.".format(str(delete_limit)))
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        channel = ctx.message.channel
        server = ctx.message.server
        await self.bot.purge_from(channel, limit=limit)
        llog = "{} purged {} messages from {}.".format(str(ctx.message.author), str(limit), str(channel.name))
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def massmove(self, ctx):
        """Move all voice connected users to the author's channel."""
        server = ctx.message.server
        channel = ctx.message.channel
        author = ctx.message.author
        members = self.bot.get_all_members()
        can_move = channel.permissions_for(server.me).move_members
        if can_move:
            lines = []
            for member in members:
                if member.voice_channel != None:
                    lines.append(member)
            for member in lines:
                await self.bot.move_member(member, author.voice_channel)
        llog = "{} mass moved everyone to {}.".format(str(author), author.voice_channel.name)
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def voicestate(self, ctx, destination : str, voicestate : str):
        """Mute or unmute all voice connected members of the channel or server."""
        server = ctx.message.server
        members = self.bot.get_all_members()
        lines = []
        if destination == "channel":
            for member in members:
                if member.voice_channel == ctx.message.author.voice_channel:
                    lines.append(member)
        elif destination == "server":
            for member in members:
                if (member.voice_channel != None) and (member.voice_channel != ctx.message.server.afk_channel ):
                    lines.append(member)
        else:
            embed = discord.Embed(description="Destination not recognized. Expected channel/server.")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        if voicestate == "mute":
            for member in lines:
                await self.bot.server_voice_state(member, mute=True)
        elif voicestate == "unmute":
            for member in lines:
                await self.bot.server_voice_state(member, mute=False)
        else:
            embed = discord.Embed(description="Voicestate not recognized. Expected mute/unmute.")
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        llog = "{} {}d all members in the {}".format(str(ctx.message.author), voicestate, destination)
        await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @commands.command(no_pm=True, pass_context=True)
    @commands.has_permissions(manage_messages=True)
    async def banchat(self, ctx, *, msg : str):
        """Ban a word or phrase from being entered into the current server."""

        banned_chat = self.config.get('banned_chat', {})
        server_id = ctx.message.server.id
        db = banned_chat.get(server_id, [])

        if msg in db:
            embed = discord.Embed(description='Message already banned.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        db.append(msg)
        banned_chat[server_id] = db
        await self.config.put('banned_chat', banned_chat)
        embed = discord.Embed(description='Message banned.')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

    @commands.command(no_pm=True, pass_context=True)
    @commands.has_permissions(manage_messages=True)
    async def unbanchat(self, ctx, *, msg : str):
        """Unban a word or phrase from being entered into the current server."""

        banned_chat = self.config.get('banned_chat', {})
        server_id = ctx.message.server.id
        db = banned_chat.get(server_id, [])

        if msg == 'all':
            db = []
            banned_chat[server_id] = db
            await self.config.put('banned_chat', banned_chat)

            embed = discord.Embed(description='Unbanned all messages.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        if msg not in db:
            embed = discord.Embed(description='Message not found in banned messages list.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return

        db.remove(msg)
        banned_chat[server_id] = db
        await self.config.put('banned_chat', banned_chat)
        embed = discord.Embed(description='Message unbanned.')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

    @commands.command(no_pm=True, pass_context=True)
    @commands.has_permissions(manage_messages=True)
    async def bannedchat(self, ctx):
        """View list of banned messages on the current server."""

        banned_chat = self.config.get('banned_chat', {})
        server_id = ctx.message.server.id
        db = banned_chat.get(server_id, [])

        embed = discord.Embed(description='This server currently has {} banned messages.'.format(len(db)))
        embed.title = 'Banned Messages'
        msgnumber = 1
        for item in db:
            embed.add_field(name='Message {}'.format(msgnumber), value=item)
            msgnumber += 1
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

    @commands.command(no_pm=True, pass_context=True)
    @commands.has_permissions(manage_server=True)
    async def plonk(self, ctx, *, member: discord.Member):
        """Bans a user from using the bot.
        This bans a person from using the bot in the current server.
        There is no concept of a global ban. This ban can be bypassed
        by having the Manage Server permission.
        To use this command you must have the Manage Server permission
        or have a Bot Admin role.
        """

        plonks = self.config.get('plonks', {})
        guild_id = ctx.message.server.id
        db = plonks.get(guild_id, [])

        if member.id in db:
            await self.bot.say('That user is already bot banned in this server.')
            return

        db.append(member.id)
        plonks[guild_id] = db
        await self.config.put('plonks', plonks)
        await self.bot.say('%s has been banned from using the bot in this server.' % member)

    async def ban_func(self, server, user, message="No reason given.", length=10):
        buserroles = user.roles[1:]
        self.bot.tmp_banned_cache[user] = buserroles
        invite = await self.bot.create_invite(server, max_uses=1)
        embed = discord.Embed(description='**You have been banned!**')
        embed.add_field(name='Reason', value=message)
        embed.add_field(name='Length', value='{} seconds'.format(str(length)))
        embed.add_field(name='Invite', value="After your ban time is over, click this link to rejoin the server.\nInvite: {}".format(invite))
        embed.set_footer(text='Banned', icon_url='http://i.imgur.com/wBkQqOp.png')
        embed.colour = 0x1BE118 # lucio green
        await self.bot.send_message(user, embed=embed)
        #lines = []
        #lines.append("--------------------")
        #lines.append("**You have been banned!**")
        #lines.append("For: {}".format(message))
        #lines.append("Length: {} seconds.".format(str(length)))
        #lines.append("After your ban time is over, click this link to rejoin the server.\nInvite: {}".format(invite))
        #lines.append("This invite will say expired when your ban time is up, but it is not expired!")
        #lines.append("--------------------")
        #await self.bot.send_message(user, '\n'.join(lines))
        await self.bot.ban(user, delete_message_days=0)
        await asyncio.sleep(length)
        await self.bot.unban(server, user)
        embed = discord.Embed(description="{} has been unbanned.".format(str(user)))
        embed.colour = 0x1BE118 # lucio green
        await self.bot.say(embed=embed)

    async def on_member_join(self, member):
        if member in self.bot.tmp_banned_cache:
            await self.bot.add_roles(member, *self.bot.tmp_banned_cache[member])
            try:
                del self.bot.tmp_banned_cache[member]
            except KeyError:
                pass

    async def on_message(self, message):

        banned_chat = self.config.get('banned_chat', {})
        server_id = message.server.id
        banned_chat_list = banned_chat.get(server_id, [])

        if any(word in message.content.lower() for word in banned_chat_list):
            embed = discord.Embed(description='You used a word or phrase that is banned in this server!')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.send_message(message.author, embed=embed)
            await self.bot.delete_message(message)

def setup(bot):
    bot.add_cog(Mod(bot))
