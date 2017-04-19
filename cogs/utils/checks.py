from discord.ext import commands
import discord.utils

def is_owner_check(ctx):
    try:
        ctx.bot.db['owner']
    except KeyError:
        return True

    return ctx.author.id == ctx.bot.db['owner']

def is_nsfw_check(ctx):
    server_db = ctx.bot.db.get(ctx.guild.id, {})
    nsfw_channels = server_db.get('nsfw_channels', [])

    return ctx.channel.id in nsfw_channels

def is_owner():
    return commands.check(lambda ctx: is_owner_check(ctx))

def is_nsfw():
    return commands.check(lambda ctx: is_nsfw_check(ctx))
