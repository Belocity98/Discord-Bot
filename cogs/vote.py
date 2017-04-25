import discord
import asyncio

from discord.ext import commands
from .utils import checks

class Vote:

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

        self.active_votes = []

        self.vote_emojis = [
            '✅',
            '❌'
        ]

    async def call_vote(self, ctx, embed):

        self.active_votes.append(ctx.channel.id)
        server_db = self.db.get(ctx.guild.id, {})
        vote_db = server_db.get('vote', {})

        vote_time = vote_db.get('vote_time', 60)
        vote_min = vote_db.get('vote_min', 2)
        vote_prct = vote_db.get('vote_prct', 50)

        vote = await ctx.send(embed=embed)

        for emoji in self.vote_emojis:
            await vote.add_reaction(emoji)

        await asyncio.sleep(vote_time)

        async for message in ctx.channel.history():
            if message.id == vote.id:
                vote = message
                break

        yes_count = {}
        no_count = {}

        for reaction in vote.reactions:
            if reaction.emoji == '✅':
                yes_count['num'] = reaction.count
                yes_count['users'] = await reaction.users().flatten()
            elif reaction.emoji == '❌':
                no_count['num'] = reaction.count
                no_count['users'] = await reaction.users().flatten()

        duplicates = len(set(yes_count['users']).intersection(no_count['users'])) # Fail-safe for duplicates

        yes_count['num'] -= duplicates
        no_count['num'] -= duplicates

        total = yes_count['num'] + no_count['num']

        await vote.delete()

        self.active_votes.remove(ctx.channel.id)

        if total < vote_min:
            return False

        return yes_count['num']/total >= vote_prct/100


    async def on_reaction_add(self, reaction, user):
        """Avoids duplicate votes."""

        message = reaction.message
        channel = message.channel

        if user.bot:
            return

        if channel.id not in self.active_votes:
            return

        yes_rxn = discord.utils.get(message.reactions, emoji='✅')
        no_rxn = discord.utils.get(message.reactions, emoji='❌')

        if not yes_rxn or not no_rxn:
            return

        yes_users = await yes_rxn.users().flatten()
        no_users = await no_rxn.users().flatten()

        if user in set(yes_users).intersection(no_users):
            await message.remove_reaction(reaction.emoji, user)


    @commands.group(no_pm=True, invoke_without_command=True)
    async def vote(self, ctx):
        """Shows the currently available vote commands."""

        server_db = self.db.get(ctx.guild.id, {})
        vote_db = server_db.get('vote', {})

        vote_time = vote_db.get('vote_time', 60)
        vote_prct = vote_db.get('vote_prct', 50)
        vote_min = vote_db.get('vote_min', 2)
        vote_cmds = vote_db.get('vote_cmds', [])

        embed = discord.Embed()
        embed.color = 0xf48942

        embed.title = 'Voting'

        embed.description = f'**Voting Time:** {vote_time} seconds'
        embed.description += f'\n**Percent Yes Needed:** {vote_prct}%'
        embed.description += f'\n**Minimum Voters:** {vote_min}'
        embed.description += '\n**Enabled vote commands:**\n'
        embed.description += '\n'.join(vote_cmds)

        await ctx.send(embed=embed)

    @vote.command(name='percent', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def vote_percent(self, ctx, percent : int):
        """Sets the percent needed to pass a vote."""

        if not 1 <= percent <= 100:
            await ctx.send('Percent must be between 1 and 100.')
            return

        server_db = self.db.get(ctx.guild.id, {})
        vote_db = server_db.get('vote', {})
        vote_prct = vote_db.get('vote_prct', 50)

        vote_prct = percent

        vote_db['vote_prct'] = vote_prct
        server_db['vote'] = vote_db

        await self.db.put(ctx.guild.id, server_db)
        await ctx.send('👍')

    @vote.command(name='time', no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def vote_time(self, ctx, time : int):
        """Sets the time spent on each notion in seconds."""

        if not 5 <= time <= 180:
            await ctx.send('Time must be between 5 and 180 seconds.')
            return

        server_db = self.db.get(ctx.guild.id, {})
        vote_db = server_db.get('vote', {})
        vote_time = vote_db.get('vote_time', 60)

        vote_time = time

        vote_db['vote_time'] = vote_time
        server_db['vote'] = vote_db

        await self.db.put(ctx.guild.id, server_db)
        await ctx.send('👍')

    @vote.command(name='min', no_pm=True, aliases=['minimum'])
    @commands.has_permissions(manage_guild=True)
    async def vote_min(self, ctx, minimum : int):
        """Sets the minimum number of votes needed for the vote to pass."""

        server_db = self.db.get(ctx.guild.id, {})
        vote_db = server_db.get('vote', {})
        vote_min = vote_db.get('vote_min', 2)

        vote_min = minimum

        vote_db['vote_min'] = vote_min
        server_db['vote'] = vote_db

        await self.db.put(ctx.guild.id, server_db)
        await ctx.send('👍')

    @vote.group(no_pm=True, name='toggle')
    async def vote_toggle(self, ctx):
        """Toggles a vote command."""

    @vote_toggle.command(no_pm=True, name='kick')
    @commands.has_permissions(manage_guild=True)
    async def toggle_kick(self, ctx):
        """Toggles the vote kick command."""

        server_db = self.db.get(ctx.guild.id, {})
        vote_db = server_db.get('vote', {})
        vote_cmds = vote_db.get('vote_cmds', [])

        if 'kick' in vote_cmds:
            vote_cmds.remove('kick')
            await ctx.send('Vote kick **DISABLED**.')
        else:
            vote_cmds.append('kick')
            await ctx.send('Vote kick **ENABLED**.')

        vote_db['vote_cmds'] = vote_cmds
        server_db['vote'] = vote_db
        await self.db.put(ctx.guild.id, server_db)

    @vote_toggle.command(no_pm=True, name='mute')
    @commands.has_permissions(manage_guild=True)
    async def toggle_mute(self, ctx):
        """Toggles the vote mute command."""

        server_db = self.db.get(ctx.guild.id, {})
        vote_db = server_db.get('vote', {})
        vote_cmds = vote_db.get('vote_cmds', [])

        if 'mute' in vote_cmds:
            vote_cmds.remove('mute')
            await ctx.send('Vote mute **DISABLED**.')
        else:
            vote_cmds.append('mute')
            await ctx.send('Vote mute **ENABLED**.')

        vote_db['vote_cmds'] = vote_cmds
        server_db['vote'] = vote_db
        await self.db.put(ctx.guild.id, server_db)

    @vote.command(no_pm=True, name='kick')
    @checks.vote_check()
    async def vote_kick(self, ctx, member : discord.Member):
        """Starts a vote kick for the specified member."""

        if member.bot:
            return

        author = ctx.author

        embed = discord.Embed()
        embed.color = 0x4286f4

        embed.description = f'{author.name}#{author.discriminator} called a vote to kick {member.name}#{member.discriminator}.'

        if await self.call_vote(ctx, embed):
            await member.kick()

            embed.description = f'Vote to kick {member.name}#{member.discriminator} passed. Kicking...'
            await ctx.send(embed=embed)
        else:
            embed.description = 'Vote failed!'
            await ctx.send(embed=embed)

    @vote.command(no_pm=True, name='mute')
    @checks.vote_check()
    async def vote_mute(self, ctx, member : discord.Member):
        """Starts a vote to mute the member in the current channel for 3 minutes."""

        if member.bot:
            return

        author = ctx.author
        channel = ctx.channel

        embed = discord.Embed()
        embed.color = 0x4286f4

        embed.description = f'{author.name}#{author.discriminator} called a vote to mute {member.name}#{member.discriminator}.'

        if await self.call_vote(ctx, embed):

            overwrite = discord.PermissionOverwrite()
            overwrite.send_messages=False
            overwrite.read_messages=False

            embed.description = f'Vote passed to mute {member.name}. Muting...'
            await ctx.send(embed=embed)

            await channel.set_permissions(member, overwrite=overwrite)
            await asyncio.sleep(180)
            await channel.set_permissions(member, overwrite=None)
        else:
            embed.description = 'Vote failed!'
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Vote(bot))
