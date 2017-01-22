from discord.ext import commands
import discord
import asyncio
import json

class Mod():

    def __init__(self, bot):
        self.bot = bot

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

def setup(bot):
    bot.add_cog(Mod(bot))
