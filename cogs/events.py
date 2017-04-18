import discord

class Events():

    def __init__(self, bot):
        self.bot = bot

        self.db = bot.db

    async def on_member_join(self, member):
        server_db = self.db.get(member.guild.id, {})
        preserved_roles = server_db.get('preserved_roles', {})

        if member.id in preserved_roles:
            roles = []
            for role_id in preserved_roles[member.id]:
                roles.append(discord.utils.get(member.guild.roles, id=role_id))

            preserved_roles = server_db.get('preserved_roles', {})
            del preserved_roles[member.id]
            server_db['preserved_roles'] = preserved_roles
            await self.db.put(member.guild.id, server_db)

            await member.add_roles(*roles)

    async def on_member_remove(self, member):
        server_db = self.db.get(member.guild.id, {})
        preserved_roles = server_db.get('preserved_roles', {})

        try:
            if server_db['role_preserve']:
                preserved_roles[member.id] = [r.id for r in member.roles]
                server_db['preserved_roles'] = preserved_roles
                await self.db.put(member.guild.id, server_db)
        except KeyError:
            pass

def setup(bot):
    bot.add_cog(Events(bot))
