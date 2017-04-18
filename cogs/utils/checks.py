from discord.ext import commands
import discord.utils

def is_owner_check(ctx):
    try:
        ctx.bot.db['owner']
    except KeyError:
        return True

    return ctx.author.id == ctx.bot.db['owner']

def is_owner():
    return commands.check(lambda ctx: is_owner_check(ctx))
