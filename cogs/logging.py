import discord

from discord.ext import commands
from .utils import checks



class Logging:

    def __init__(self, bot):
        self.bot = bot

        self.db = bot.db

    @commands.group(name='log', no_pm=True, invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    @checks.doing_logging()
    async def _log(self, ctx):
        guild = ctx.guild

        embed = discord.Embed()
        embed.color = 0xc542f4

        server_db = self.db.get(guild.id, {})
        logging = server_db.get('logging', {})
        events = logging.get('events', [])
        log_channel = logging.get('channel', '')
        log_channel = discord.utils.get(guild.text_channels, id=log_channel)

        embed.title = 'Logging'
        embed.description = f'**Logging Channel:** {log_channel.name}\n' if log_channel else 'Logging Channel: None\n'
        embed.description += '**Events being logged:**\n'
        embed.description += '\n'.join(events) if events else 'Not logging any events.'

        await ctx.send(embed=embed)

    @_log.command(no_pm=True, name='mark')
    @commands.has_permissions(manage_guild=True)
    @checks.doing_logging()
    async def _mark(self, ctx):
        """Marks a channel as the logging channel."""

        guild = ctx.guild

        server_db = self.db.get(guild.id, {})
        logging = server_db.get('logging', {})
        channel = logging.get('channel', '')

        channel = ctx.channel.id

        logging['channel'] = channel
        server_db['logging'] = logging
        await self.db.put(guild.id, server_db)

        await ctx.send(f'Logging channel set to {ctx.channel.name}.')

    @_log.group(no_pm=True, name='messages', aliases=['message'])
    async def l_message(self, ctx):
        """Subcommand group for logging messages."""

    @_log.group(no_pm=True, name='channels', aliases=['channel'])
    async def l_channel(self, ctx):
        """Subcommand group for logging channels."""

    @l_message.command(no_pm=True, name='deleted')
    @commands.has_permissions(manage_guild=True)
    @checks.doing_logging()
    async def m_deleted(self, ctx):
        guild = ctx.guild

        server_db = self.db.get(guild.id, {})
        logging = server_db.get('logging', {})
        events = logging.get('events', [])

        events.append('deleted_messages') if 'deleted_messages' not in events else events.remove('deleted_messages')

        status = '**ENABLED**' if 'deleted_messages' in events else '**DISABLED**'

        await ctx.send(f'Logging deleted messages {status}.')

        logging['events'] = events
        server_db['logging'] = logging

        await self.db.put(guild.id, server_db)

    @l_message.command(no_pm=True, name='edited')
    @commands.has_permissions(manage_guild=True)
    @checks.doing_logging()
    async def m_edited(self, ctx):
        guild = ctx.guild

        server_db = self.db.get(guild.id, {})
        logging = server_db.get('logging', {})
        events = logging.get('events', [])

        events.append('edited_messages') if 'edited_messages' not in events else events.remove('edited_messages')

        status = '**ENABLED**' if 'edited_messages' in events else '**DISABLED**'

        await ctx.send(f'Logging edited messages {status}.')

        logging['events'] = events
        server_db['logging'] = logging

        await self.db.put(guild.id, server_db)

    @l_channel.command(no_pm=True, name='deleted')
    @commands.has_permissions(manage_guild=True)
    @checks.doing_logging()
    async def c_deleted(self, ctx):
        guild = ctx.guild

        server_db = self.db.get(guild.id, {})
        logging = server_db.get('logging', {})
        events = logging.get('events', [])

        events.append('deleted_channels') if 'deleted_channels' not in events else events.remove('deleted_channels')

        status = '**ENABLED**' if 'deleted_channels' in events else '**DISABLED**'

        await ctx.send(f'Logging deleted channels {status}.')

        logging['events'] = events
        server_db['logging'] = logging

        await self.db.put(guild.id, server_db)

    @l_channel.command(no_pm=True, name='created')
    @commands.has_permissions(manage_guild=True)
    @checks.doing_logging()
    async def c_created(self, ctx):
        guild = ctx.guild

        server_db = self.db.get(guild.id, {})
        logging = server_db.get('logging', {})
        events = logging.get('events', [])

        events.append('created_channels') if 'created_channels' not in events else events.remove('created_channels')

        status = '**ENABLED**' if 'created_channels' in events else '**DISABLED**'

        await ctx.send(f'Logging created channels {status}.')

        logging['events'] = events
        server_db['logging'] = logging

        await self.db.put(guild.id, server_db)

def setup(bot):
    bot.add_cog(Logging(bot))
