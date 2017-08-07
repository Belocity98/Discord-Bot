from discord.ext import commands
import discord.utils

def is_nsfw_check(ctx):
    return isinstance(ctx.channel, discord.TextChannel) and ctx.channel.is_nsfw()

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

def is_nsfw():
    return commands.check(lambda ctx: is_nsfw_check(ctx))

def doing_logging():
    return commands.check(lambda ctx: do_logging_check(ctx))

def vote_check():
    return commands.check(lambda ctx: do_vote_check(ctx))
