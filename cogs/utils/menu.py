import asyncio

import discord


class Menu:

    def __init__(self, bot, message):
        self.bot = bot

        self.db = bot.db

        self.message = message
        self.channel = message.channel
        self.author = message.author
        self.guild = message.guild

        self.embed = discord.Embed(color=0xd1302e, title='Settings Menu')

        self.active = False

        self.page = 'main'

        self.reaction_emojis = [
            ('🇭', self.show_home),
            ('🎦', self.view_settings),
            ('🔴', self.modify_settings),
            ('❓', self.show_help),
            ('❌', self.exit_menu)
        ]

        self.modification_emojis = [
            ('🇭', self.show_home),
            ('🇵', self.change_prefix),
            ('🇦', self.change_autoassign),
            ('🇷', self.change_rolepreserve),
            ('🇱', self.change_logging),
            ('🇺', self.change_units),
            ('🇻', self.change_vc_text),
            ('❌', self.exit_menu)
        ]

    def prompt_check(self, message):
        return self.author.id == message.author.id

    async def change_prefix(self):
        prompt = await self.channel.send('Enter a prefix:')
        try:
            resp = await self.bot.wait_for('message', check=self.prompt_check, timeout=120)
        except asyncio.TimeoutError:
            await prompt.delete()
            return

        server_db = self.db.get(self.guild.id, {})
        server_db['prefix'] = resp.content
        await self.db.put(self.guild.id, server_db)

        await resp.delete()
        await prompt.delete()

    async def change_rolepreserve(self):
        server_db = self.db.get(self.guild.id, {})
        role_preserve = server_db.get('role_preserve', False)

        role_preserve = not role_preserve

        if not role_preserve:
            status = await self.channel.send('Role preserving **DISABLED**.')

            p_users = server_db.get('preserved_roles', {})
            p_users = {}
            server_db['preserved_roles'] = p_users
        else:
            status = await self.channel.send('Role preserving **ENABLED**.')

        server_db['role_preserve'] = role_preserve

        await self.db.put(self.guild.id, server_db)

    async def change_autoassign(self):
        server_db = self.db.get(self.guild.id, {})
        autoassign = server_db.get('autoassign_role', None)

        roles_dict = {}
        for i, item in enumerate(self.guild.roles):
            roles_dict[i] = item.name
        roles_dict[0] = None

        message = ['Enter the number or the name of the role to be autoassigned.']
        for key, val in roles_dict.items():
            message.append(f'{key}. {val}')

        prompt = await self.channel.send('\n'.join(message))

        try:
            resp = await self.bot.wait_for('message', check=self.prompt_check, timeout=120)
        except asyncio.TimeoutError:
            return

        if resp.content.isdigit():
            index = int(resp.content)
            if index not in roles_dict.keys():
                await self.channel.send('Number not valid.')
                return

            role = discord.utils.get(self.guild.roles, name=roles_dict[index])

        else:
            name = resp.content
            if name not in roles_dict.values():
                await self.channel.send('Name not valid.')
                return
            role = discord.utils.get(self.guild.roles, name=name)

        await prompt.delete()
        await resp.delete()

        server_db['autoassign_role'] = role.id if role else None

        await self.db.put(self.guild.id, server_db)

    async def change_logging(self):
        server_db = self.db.get(self.guild.id, {})
        logging_dict = server_db.get('logging', {})
        logging = logging_dict.get('status', False)

        logging = not logging

        if not logging:
            status = await self.channel.send('Logging **DISABLED**.')
        else:
            status = await self.channel.send('Logging **ENABLED**.')

        logging_dict['status'] = logging
        server_db['logging'] = logging_dict

        await self.db.put(self.guild.id, server_db)

    async def change_vc_text(self):
        server_db = self.db.get(self.guild.id, {})
        status = server_db.get('text_vc_channels', False)

        status = not status

        if status:
            await self.channel.send('Text channels for voice **ENABLED**.')
        else:
            await self.channel.send('Text channels for voice **DISABLED**.')

        server_db['text_vc_channels'] = status
        await self.db.put(self.guild.id, server_db)

    async def change_units(self):
        server_db = self.db.get(self.guild.id, {})
        units = server_db.get('units', 'imperial')

        if units == 'imperial':
            units = 'metric'
            await self.channel.send('Units changed to **metric**.')

        elif units == 'metric':
            units = 'imperial'
            await self.channel.send('Units changed to **imperial**.')

        server_db['units'] = units
        await self.db.put(self.guild.id, server_db)

    async def show_home(self, initial=False):

        await self.message.clear_reactions()

        self.page = 'main'
        self.embed.description = 'Welcome to the settings menu!' \
                                '\nHere, you can modify Wumpus Bot to your liking.' \
                                '\n\nIf you are confused, click ❓ for help.'

        if not initial:
            return

        self.active = True
        self.message = await self.channel.send(content=' ', embed=self.embed)
        await self.add_reactions()

    async def add_reactions(self):
        if not self.message:
            return

        if self.page == 'main':
            for (emoji, _) in self.reaction_emojis:
                await self.message.add_reaction(emoji)
            return
        elif self.page == 'modify':
            for (emoji, _) in self.modification_emojis:
                await self.message.add_reaction(emoji)

    async def view_settings(self):
        server_db = self.db.get(self.guild.id, {})
        logging_dict = server_db.get('logging', {})

        prefix = server_db.get('prefix', '>')
        role_preserve = server_db.get('role_preserve', False)

        autoassign_role = server_db.get('autoassign_role', None)
        autoassign_role = discord.utils.get(self.guild.roles, id=autoassign_role)
        autoassign_role = autoassign_role.name if autoassign_role else 'None'

        logging = logging_dict.get('status', False)

        units = server_db.get('units', 'imperial').title()

        self.embed.description = f'**Prefix:** {prefix}' \
                                f'\n**Role Preserve:** {role_preserve}' \
                                f'\n**AutoAssign Role:** {autoassign_role}' \
                                f'\n**Logging:** {logging}' \
                                f'\n**Units:** {units}'


    async def show_help(self):
        self.embed.description = '🇭 - Go Home' \
                                '\n🎦 - View Current Settings' \
                                '\n🔴 - Modify Settings' \
                                '\n❓ - Show this Page' \
                                '\n❌ - Exit the Settings Menu'

    async def exit_menu(self):
        self.active = False
        await self.message.delete()

    async def update_embed(self):
        try:
            await self.message.edit(content=' ', embed=self.embed)
        except discord.NotFound:
            pass

    async def modify_settings(self):
        await self.message.clear_reactions()
        self.page = 'modify'

        self.embed.description = '🇭 - Go Home' \
                            '\n🇵 - Change Bot Prefix' \
                            '\n🇦 - Change Autoassign Role' \
                            '\n🇷 - Toggle Role Preserve' \
                            '\n🇱 - Toggle Logging' \
                            '\n🇺 - Toggle Units' \
                            '\n🇻 - Toggle text channels for voice' \
                            '\n❌ - Exit the Settings Menu'

    def react_check(self, reaction, user):
        if reaction.message.id != self.message.id:
            return False

        if user.bot:
            return False

        if user.id != self.author.id:
            return False

        if self.page == 'main':
            for (emoji, func) in self.reaction_emojis:
                if reaction.emoji == emoji:
                    self.match = func
                    return True
        elif self.page =='modify':
            for (emoji, func) in self.modification_emojis:
                if reaction.emoji == emoji:
                    self.match = func
                    return True
        return False

    async def menu(self):

        await self.show_home(initial=True)

        while self.active:
            try:
                react = await self.bot.wait_for('reaction_add', check=self.react_check, timeout=120)
            except asyncio.TimeoutError:
                await self.exit_menu()
                return

            reaction, user = react[0], react[1]
            await self.message.remove_reaction(reaction.emoji, user)

            await self.match()
            await self.update_embed()
            try:
                await self.add_reactions()
            except:
                pass
