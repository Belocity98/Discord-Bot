import discord
import asyncio

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
            ('🔄', self.assign_defaults),
            ('❓', self.show_help),
            ('❌', self.exit_menu)
        ]

        self.modification_emojis = [
            ('🇭', self.show_home),
            ('🇵', self.change_prefix),
            ('🇷', self.change_rolepreserve),
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
        prompt = await self.channel.send('Enter `True` or `False` to enable/disable role preserving.')
        try:
            resp = await self.bot.wait_for('message', check=self.prompt_check, timeout=120)
        except asyncio.TimeoutError:
            await prompt.delete()
            return

        server_db = self.db.get(self.guild.id, {})
        if 't' in resp.content.lower():
            server_db['role_preserve'] = True
        else:
            server_db['role_preserve'] = False

            p_users = server_db.get('preserved_roles', {})
            p_users = {}
            server_db['preserved_roles'] = p_users

        await self.db.put(self.guild.id, server_db)

        await resp.delete()
        await prompt.delete()

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

        if 'prefix' not in server_db:
            await self.assign_defaults()

        prefix = server_db['prefix']
        role_preserve = server_db['role_preserve']
        autoassign_role = server_db['autoassign_role']

        self.embed.description = f'**Prefix:** {prefix}' \
                                f'\n**Role Preserve:** {role_preserve}' \
                                f'\n**AutoAssign Role:** {autoassign_role}'

    async def show_help(self):
        self.embed.description = '🇭 - Go Home' \
                                '\n🎦 - View Current Settings' \
                                '\n🔴 - Modify Settings' \
                                '\n🔄 - Restore Default Settings' \
                                '\n❓ - Show this Page' \
                                '\n❌ - Exit the Settings Menu'

    async def exit_menu(self):
        self.active = False
        await self.message.delete()

    async def assign_defaults(self):
        server_db = self.db.get(self.guild.id, {})

        server_db['prefix'] = '>'
        server_db['role_preserve'] = False
        server_db['autoassign_role'] = None

        await self.db.put(self.guild.id, server_db)

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
                            '\n🇷 - Change Role Preserve' \
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
