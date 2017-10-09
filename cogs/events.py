import datetime

import discord


class Events:

    def __init__(self, bot):
        self.bot = bot

        self.db = bot.db

    def __global_check(self, ctx):
        server_db = self.db.get(ctx.guild.id, {})
        disabled_cmds = server_db.get('disabled_cmds', [])

        if ctx.command.name in disabled_cmds:
            return False

        return True

    async def on_member_join(self, member):

        guild = member.guild
        server_db = self.db.get(member.guild.id, {})
        preserved_roles = server_db.get('preserved_roles', {})
        autoassign_role = server_db.get('autoassign_role', None)
        autoassign_role = discord.utils.get(guild.roles, id=autoassign_role)

        roles_to_add = []

        roles_to_add.append(autoassign_role)

        if member.id in preserved_roles:
            role_ids = preserved_roles[member.id]
            for role in role_ids:
                roles_to_add.append(discord.utils.get(guild.roles, id=role))

            del preserved_roles[member.id]
            server_db['preserved_roles'] = preserved_roles
            await self.db.put(guild.id, server_db)

        try:
            await member.add_roles(*roles_to_add)
        except:
            pass

    async def on_member_remove(self, member):
        server_db = self.db.get(member.guild.id, {})

        preserved_roles = server_db.get('preserved_roles', {})
        role_preserve = server_db.get('role_preserve', False)

        if role_preserve:
            preserved_roles[member.id] = [r.id for r in member.roles]
            server_db['preserved_roles'] = preserved_roles
            await self.db.put(member.guild.id, server_db)

    async def on_message_delete(self, message):

        guild = message.guild

        server_db = self.db.get(guild.id, {})
        logging = server_db.get('logging', {})
        events = logging.get('events', [])
        status = logging.get('status', False)
        log_channel = logging.get('channel', '')
        log_channel = discord.utils.get(guild.text_channels, id=log_channel)

        if not log_channel:
            return

        if 'deleted_messages' in events and status:
            embed = self.create_message_embed(message, 'deleted')
            await log_channel.send(embed=embed)

    async def on_message_edit(self, before, after):

        if before.content == after.content:
            return

        guild = before.guild

        server_db = self.db.get(guild.id, {})
        logging = server_db.get('logging', {})
        events = logging.get('events', [])
        status = logging.get('status', False)
        log_channel = logging.get('channel', '')
        log_channel = discord.utils.get(guild.text_channels, id=log_channel)

        if not log_channel:
            return

        if 'edited_messages' in events and status:
            embed = self.create_message_embed(before, 'edited', after_msg=after)
            await log_channel.send(embed=embed)

    async def on_channel_delete(self, channel):

        guild = channel.guild

        server_db = self.db.get(guild.id, {})
        logging = server_db.get('logging', {})
        events = logging.get('events', [])
        status = logging.get('status', False)
        log_channel = logging.get('channel', '')
        log_channel = discord.utils.get(guild.text_channels, id=log_channel)

        if not log_channel:
            return

        if 'deleted_channels' in events and status:
            embed = discord.Embed()
            embed.color = 0xba0000

            channel_type = 'Text' if isinstance(channel, discord.TextChannel) else 'Voice'

            embed.set_footer(text='Channel Deleted', icon_url='http://i.imgur.com/Yt5YHzv.png')
            embed.timestamp = datetime.datetime.utcnow()

            embed.title = channel.name
            embed.description = f'**Type:** {channel_type}\n' \
                                f'**ID:** {channel.id}'

            if channel.topic:
                embed.add_field(name='Topic', value=channel.topic, inline=False)

            await log_channel.send(embed=embed)

    async def on_channel_create(self, channel):

        guild = channel.guild

        server_db = self.db.get(guild.id, {})
        logging = server_db.get('logging', {})
        events = logging.get('events', [])
        status = logging.get('status', False)
        log_channel = logging.get('channel', '')
        log_channel = discord.utils.get(guild.text_channels, id=log_channel)

        if not log_channel:
            return

        if 'created_channels' in events and status:
            embed = discord.Embed()
            embed.color = 0x01a004

            channel_type = 'Text' if isinstance(channel, discord.TextChannel) else 'Voice'

            embed.set_footer(text='Channel Created', icon_url='http://i.imgur.com/gUgzCDp.png')
            embed.timestamp = datetime.datetime.utcnow()

            embed.title = channel.name
            embed.description = f'**Type:** {channel_type}\n' \
                                f'**ID:** {channel.id}'

            if channel.topic:
                embed.add_field(name='Topic', value=channel.topic, inline=False)

            await log_channel.send(embed=embed)

    async def on_voice_state_update(self, member, before, after):
        """Used for detecting whether a user joins/leaves a voice channel.

            Useful for text voice channels."""

        if member.bot:
            return

        guild = member.guild

        server_db = self.db.get(guild.id, {})
        status = server_db.get('text_vc_channels', False)

        if not status:
            return

        b_channel = before.channel
        a_channel = after.channel

        if b_channel and a_channel:
            if a_channel.id == b_channel.id:
                return

        default_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        if b_channel:
            b_txt_name = 'vc_' + b_channel.name.replace(' ', '_').lower()
            b_txt_chan = discord.utils.get(guild.text_channels, name=b_txt_name)

            if not b_txt_chan:
                try:
                    b_txt_chan = await guild.create_text_channel(name=b_txt_name, overwrites=default_overwrites)
                except discord.Forbidden:
                    return

            await b_txt_chan.set_permissions(member, overwrite=None)

        if a_channel:
            a_txt_name = 'vc_' + a_channel.name.replace(' ', '_').lower()
            a_txt_chan = discord.utils.get(guild.text_channels, name=a_txt_name)

            if not a_txt_chan:
                try:
                    a_txt_chan = await guild.create_text_channel(name=a_txt_name, overwrites=default_overwrites)
                except discord.Forbidden:
                    return

            await a_txt_chan.set_permissions(member, overwrite=discord.PermissionOverwrite(read_messages=True))

    def create_message_embed(self, message, event, after_msg=None):
        author = message.author

        embed = discord.Embed()
        embed.color = 0xe00000 if event is 'deleted' else 0x0065d1

        a_url = author.avatar_url_as(format='png')

        embed.timestamp = datetime.datetime.utcnow() if event is 'deleted' else after_msg.edited_at

        footer_text = 'Message Deleted' if event is 'deleted' else 'Message Edited'
        icon_url = 'http://i.imgur.com/Yt5YHzv.png' if event is 'deleted' else 'http://i.imgur.com/3H8z4nW.png'

        embed.set_footer(text=footer_text, icon_url=icon_url)
        embed.set_author(name=author.name, icon_url=a_url)

        if event == 'edited':
            embed.add_field(name='Before', value=message.content)
            embed.add_field(name='After', value=after_msg.content, inline=False)
        else:
            embed.description = message.content

        return embed


def setup(bot):
    bot.add_cog(Events(bot))
