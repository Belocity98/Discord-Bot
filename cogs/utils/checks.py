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

def do_logging_check(ctx):
    server_db = ctx.bot.db.get(ctx.guild.id, {})

    logging_dict = server_db.get('logging', {})
    return logging_dict.get('status', False)

def do_vote_check(ctx):
    server_db = ctx.bot.db.get(ctx.guild.id, {})
    vote_db = server_db.get('vote', {})
    vote_cmds = vote_db.get('vote_cmds', [])

    if ctx.channel.id in ctx.bot.get_cog('Vote').active_votes:
        return False

    return ctx.command.name in vote_cmds

def is_owner():
    return commands.check(lambda ctx: is_owner_check(ctx))

def is_nsfw():
    return commands.check(lambda ctx: is_nsfw_check(ctx))

def doing_logging():
    return commands.check(lambda ctx: do_logging_check(ctx))

def vote_check():
    return commands.check(lambda ctx: do_vote_check(ctx))
