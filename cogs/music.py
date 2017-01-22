import asyncio
import discord
from discord.ext import commands
import youtube_dl
import os, sys
from random import choice

if not discord.opus.is_loaded():
    # the 'opus' library here is opus.dll on windows
    # or libopus.so on linux in the current directory
    # you should replace this with the location the
    # opus library is located in and with the proper filename.
    # note that on windows this DLL is automatically provided for you
    discord.opus.load_opus('opus')

class VoiceEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        fmt = '*{0.title}* uploaded by {0.uploader} and requested by {1.display_name}'
        duration = self.player.duration
        if duration:
            fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set() # a set of user_ids that voted
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()

class Music:
    """Voice related commands.
    Works in multiple servers at once.
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}
        #self.pause_checker = bot.loop.create_task(self.check_for_people())
"""
    async def check_for_people(self):
        while True:
            do_for_loop = True
            if len(self.voice_states) == 0:
                print("no states")
                do_for_loop = False
            if do_for_loop:
                for server in self.voice_states:
                    state = self.get_voice_state(server)
                    #if not any([x for x in server.members if x.voice.voice_channel == bot.voice_client_in(server).channel ]):
                    if len(self.bot.voice_members) == 1:
                        state.player.pause()
                        print("paused")
                    else:
                        state.player.resume()
                        print("resumed")
            await asyncio.sleep(1)
"""
    def check_if_done(self, ctx):
        state = self.get_voice_state(ctx.message.server)
        player = state.player
        if len(state.songs._queue) == 0 and state.is_playing() == False:
            embed = discord.Embed(description='Queue finished. Disconnecting.')
            embed.colour = 0x1BE118 # lucio green
            coro = self.bot.send_message(ctx.message.channel, embed=embed)
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass
            del self.voice_states[ctx.message.server.id]
            coro = state.voice.disconnect()
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass
            return
        else:
            state.toggle_next()
            return

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx, *, channel : discord.Channel):
        """Joins a voice channel."""
        if channel == ctx.message.server.afk_channel:
            await bot.say('You cannot move the bot to the AFK channel.')
            return
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await self.bot.say('Already in a voice channel...')
        except discord.InvalidArgument:
            await self.bot.say('This is not a voice channel...')
        else:
            await self.bot.say('Ready to play audio in ' + channel.name)
            llog = "Music bot joined {}.".format(channel.name)
            await self.bot.get_cog("Logging").do_logging(llog, channel.server)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel."""
        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            await self.bot.say('You are not in a voice channel.')
            return False
        if summoned_channel == ctx.message.server.afk_channel:
            await self.bot.say('You cannot summon the bot to the AFK channel.')
            return
        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)
            llog = "Music bot summoned to {}.".format(str(summoned_channel))
            await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

        return True

    @commands.command(pass_context=True, no_pm=True)
    async def play(self, ctx, *, song : str):
        """Plays a song.
        If there is a song currently in the queue, then it is
        queued until the next song is done playing.
        This command automatically searches as well from YouTube.
        The list of supported sites can be found here:
        https://rg3.github.io/youtube-dl/supportedsites.html
        """
        state = self.get_voice_state(ctx.message.server)
        cd = str(os.path.dirname(os.path.realpath(__file__)))
        cache_loc = cd + '\\cache'
        opts = {
            'extractaudio' : True,
            'cachedir' : cache_loc,
            'format' : 'bestaudio/best',
            'audioformat' : 'mp3',
            'default_search': 'auto',
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'logtostderr': True,
            'quiet': True,
            'no_warnings': True,
            'outtmpl': '%(extractor)s-%(id)s-%(title)s'
        }

        music_quotes = [
            "Oh, this is my jam!",
            "Oh, turn it up.",
            "Pump up the volume.",
            "Rasin' the volume!",
            "Woo, you feel that?",
            "Ooh, you hear that?",
            "Oh, let's break it down!",
            "Let's up the tempo."
        ]

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        if not state.is_playing():
            await self.bot.say(choice(music_quotes))

        try:
            #player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
            player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=lambda: self.check_if_done(ctx))
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:

            player.volume = 0.05
            entry = VoiceEntry(ctx.message, player)
            embed = self.embed(ctx.message, player)
            await self.bot.send_message(ctx.message.channel, content=None, embed=embed)
            await state.songs.put(entry)

            llog = "{} queued {}.".format(str(ctx.message.author), str(entry))
            await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_messages=True)
    async def volume(self, ctx, value : int):
        """Sets the volume of the currently playing song."""

        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.volume = value / 100
            await self.bot.say('Set the volume to {:.0%}'.format(player.volume))
            llog = "{} set the volume to {}%".format(str(ctx.message.author), player.volume)
            await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_messages=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()
            llog = "{} paused the music bot.".format(str(ctx.message.author))
            await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_messages=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()
            llog = "{} resumed the music bot.".format(str(ctx.message.author))
            await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @commands.command(pass_context=True, no_pm=True)
    @commands.has_permissions(manage_messages=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        """
        server = ctx.message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.player
            player.stop()
            llog = "{} stopped the music bot.".format(str(ctx.message.author))
            await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('Not playing any music right now...')
            return

        voter = ctx.message.author
        if voter == state.current.requester:
            await self.bot.say('Requester requested skipping song...')
            state.skip()
            llog = "{} skipped the current song.".format(str(ctx.message.author))
            await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)
        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= 3:
                await self.bot.say('Skip vote passed, skipping song...')
                state.skip()
                llog = "Skip vote passed, song skipped."
                await self.bot.get_cog("Logging").do_logging(llog)
            else:
                await self.bot.say('Skip vote added, currently at [{}/3]'.format(total_votes))
                llog = "{} voted to skip the current song.".format(str(voter))
                await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)
        else:
            await self.bot.say('You have already voted to skip this song.')

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @commands.has_permissions(administrator=True)
    async def masterskip(self, ctx):
            state = self.get_voice_state(ctx.message.server)
            if not state.is_playing():
                await self.bot.say("Not playing any music right now...")
                return
            state.skip()
            await self.bot.say("Skipping song...")
            llog = "{} used a masterskip to skip the current song.".format(str(ctx.message.author))
            await self.bot.get_cog("Logging").do_logging(llog, ctx.message.server)

    @commands.command(pass_context=True, no_pm=True)
    async def queue(self, ctx):
        """Shows songs in the queue."""
        state = self.get_voice_state(ctx.message.server)
        if len(state.songs._queue) == 0:
            embed = discord.Embed(description='There are no songs in the queue.')
            embed.colour = 0x1BE118 # lucio green
            await self.bot.say(embed=embed)
            return
        embed = discord.Embed(description='----------')
        embed.title = 'Song Queue'
        embed.colour = 0x1BE118 # lucio green
        embed.add_field(name='Now playing', value=state.current)
        song_number = 1
        for item in state.songs._queue:
            embed.add_field(name=str(song_number), value=str(item))
            song_number += 1
        await self.bot.say(embed=embed)

    def embed(self, message, player):
        requester = message.author
        channel = message.channel
        embed = discord.Embed(description='Uploaded by: {}'.format(str(player.uploader)))
        embed.title = str(player.title)
        #embed.url = player.download_url
        embed.colour = 0x1BE118 # lucio green
        embed.set_author(name=str(requester.display_name), icon_url=requester.avatar_url)
        embed.add_field(name='Views', value=player.views)
        embed.add_field(name='Likes', value=player.likes)
        embed.add_field(name='Dislikes', value=player.dislikes)
        embed.add_field(name='Length', value='{0[0]}m {0[1]}s'.format(divmod(player.duration, 60)))
        embed.set_footer(text='Uploaded: {}'.format(player.upload_date), icon_url=embed.Empty)
        return embed

def setup(bot):
    cog_instance = Music(bot)
    bot.add_cog(cog_instance)
