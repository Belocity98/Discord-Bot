from discord.ext import commands
from fuzzywuzzy import process
import discord

from .utils import checks


class Settings:

    def __init__(self, bot):
        self.bot = bot

        self.db = bot.db

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @checks.has_permissions_or_owner(administrator=True)
    async def settings(self, ctx):
        """Main command for modifying settings.

        If no setting is specified, lists all available
        settings that can be modified. Not specifying a value
        for a setting views the setting."""

        sub_cmds = [f'**{command.name}**' for command in self.settings.commands]
        sub_cmd_helps = [command.help for command in self.settings.commands]
        available_settings = dict(zip(sub_cmds, sub_cmd_helps))
        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.title = 'Available Settings'
        em.description = 'Use `>settings <setting name> <value>` to set a setting.\nUse `>settings <setting name>`' \
                         ' to see the currently set value for a setting.\n\n'
        for key, val in available_settings.items():
            em.description += f'{key} - {val}\n'

        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            return

    @settings.command(name='prefix')
    @checks.has_permissions_or_owner(administrator=True)
    async def s_prefix(self, ctx, *, prefix: str=None):
        """String. The prefix that the bot uses for the server."""
        server_db = self.db.get(ctx.guild.id, {})
        if prefix is None:
            prefix = server_db.get('prefix', '>')
            em = discord.Embed()
            em.color = discord.Color.blurple()
            em.description = f'prefix = `{prefix}`'
            return await ctx.send(embed=em)

        server_db['prefix'] = prefix
        await self.db.put(ctx.guild.id, server_db)
        await ctx.message.add_reaction('👌')

    @settings.command(name='role_preserve')
    @checks.has_permissions_or_owner(administrator=True)
    async def s_role_preserve(self, ctx, state: bool=None):
        """True/False. Whether or not the bot should preserve roles when users leave the server."""
        server_db = self.db.get(ctx.guild.id, {})
        if state is None:
            state = server_db.get('role_preserve', False)
            em = discord.Embed()
            em.color = discord.Color.blurple()
            em.description = f'role_preserve = `{state}`'
            return await ctx.send(embed=em)

        server_db['role_preserve'] = state
        await self.db.put(ctx.guild.id, server_db)
        await ctx.message.add_reaction('👌')

    @settings.command(name='logging')
    @checks.has_permissions_or_owner(administrator=True)
    async def s_logging(self, ctx, state: bool=None):
        """True/False. Whether or not the bot should use the logging features."""
        server_db = self.db.get(ctx.guild.id, {})
        logging = server_db.get('logging', {})
        if state is None:
            state = logging.get('status', False)
            em = discord.Embed()
            em.color = discord.Color.blurple()
            em.description = f'logging = `{state}`'
            return await ctx.send(embed=em)

        logging['status'] = state
        server_db['logging'] = logging
        await self.db.put(ctx.guild.id, server_db)
        await ctx.message.add_reaction('👌')

    @settings.command(name='text_voicechannels')
    @checks.has_permissions_or_owner(administrator=True)
    async def s_text_voicechannels(self, ctx, state: bool=None):
        """True/False. Whether or not the bot should enable text channels for voice channels."""
        server_db = self.db.get(ctx.guild.id, {})
        if state is None:
            state = server_db.get('text_vc_channels', False)
            em = discord.Embed()
            em.color = discord.Color.blurple()
            em.description = f'text_voicechannels = `{state}`'
            return await ctx.send(embed=em)

        server_db['text_vc_channels'] = state
        await self.db.put(ctx.guild.id, server_db)
        await ctx.message.add_reaction('👌')

    @settings.command(name='units_type')
    @checks.has_permissions_or_owner(administrator=True)
    async def s_units_type(self, ctx, unit_type: str=None):
        """'metric'/'imperial'. The type of units the bot should use."""
        server_db = self.db.get(ctx.guild.id, {})
        if unit_type is None:
            unit_type = server_db.get('units', 'imperial')
            em = discord.Embed()
            em.color = discord.Color.blurple()
            em.description = f'units_type = `{unit_type}`'
            return await ctx.send(embed=em)

        if unit_type.lower() == 'metric':
            server_db['units'] = 'metric'
        elif unit_type.lower() == 'imperial':
            server_db['units'] = 'imperial'
        else:
            return await ctx.message.add_reaction('❌')

        await ctx.message.add_reaction('👌')
        await self.db.put(ctx.guild.id, server_db)

    @settings.command(name='autoassign_role')
    @checks.has_permissions_or_owner(administrator=True)
    async def s_autoassign_role(self, ctx, role_name: str=None):
        """Role name. The role that should be assigned to new server members. Set to 'none' to disable."""
        server_db = self.db.get(ctx.guild.id, {})
        em = discord.Embed()
        em.color = discord.Color.blurple()
        if role_name is None:
            role_id = server_db.get('autoassign_role')
            if role_id is not None:
                role = discord.utils.get(ctx.guild.roles, id=role_id)
                if role is None:
                    em.description = 'autoassign_role = `NOT SET`'
                else:
                  em.description = f'autoassign_role = {role.name}'
            elif role_id is None:
                em.description = 'autoassign_role = `NOT SET`'
            return await ctx.send(embed=em)

        if role_name.lower() == 'none':
            server_db['autoassign_role'] = None
            await ctx.message.add_reaction('👌')
            await self.db.put(ctx.guild.id, server_db)
            return

        role_names = [role.name for role in ctx.guild.roles[1:]]
        matched_role = list(process.extractOne(role_name, role_names))

        if matched_role[1] < 60:
            em.description = 'Role not found.'
            return await ctx.send(embed=em)

        role = discord.utils.get(ctx.guild.roles, name=matched_role[0])
        server_db['autoassign_role'] = role.id if role else None

        await ctx.message.add_reaction('👌')
        await self.db.put(ctx.guild.id, server_db)


def setup(bot):
    bot.add_cog(Settings(bot))
