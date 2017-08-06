import os
import re
import math
import shutil
import asyncio
import aiohttp
import discord
import functools
import youtube_dl

from discord.ext import commands
from cogs.utils import config



class YoutubeSource(discord.FFmpegPCMAudio):
    def __init__(self, path):
        super().__init__(path)

class Music:
    def __init__(self, bot):
        self.bot = bot

        self.queues = {}
        self.volumes = {}
        self.now_playing = {}

    @commands.group(aliases=['m'], invoke_without_command=True)
    async def music(self, ctx):
        """Main command for all music-based commands."""
        pass

    @music.group(name='admin', aliases=['a'], invoke_without_command=True)
    async def admin_(self, ctx):
        """Main command for all music admin commands."""
        pass

    @admin_.command(name='next', aliases=['skip'])
    @commands.has_permissions(mute_members=True)
    async def a_next(self, ctx):
        """Force next command for admins only."""
        voice = ctx.guild.voice_client
        if not voice:
            return

        voice.stop()

    @admin_.command(name='stop')
    @commands.has_permissions(mute_members=True)
    async def a_stop(self, ctx):
        """Force stop command for admins only."""
        voice = ctx.guild.voice_client
        if not voice:
            return

        if voice.is_playing():
            self.queues[ctx.guild.id] = []
            voice.stop()
            self.now_playing[ctx.guild.id] = {}

    @music.command()
    async def play(self, ctx, *, query: str=None):
        """Plays a YouTube video from a URL or a search."""
        if not query:
            query = 'brain power'

        curr_voice = ctx.guild.voice_client
        user_voice = ctx.author.voice
        if not user_voice and not curr_voice:
            return

        if not curr_voice:
            channel = user_voice.channel
            await channel.connect()
            curr_voice = ctx.guild.voice_client

        if curr_voice.is_playing():
            data = await self.get_info_from_query(query=query)
            data['ctx'] = ctx

            if data['duration'] > 600:
                return await ctx.send('Song is too long.')

            em = self.format_song_embed(data)
            a_url = ctx.author.avatar_url_as(format='png', size=1024)
            em.set_footer(text=f'{ctx.author} added a song to the queue.', icon_url=a_url)

            await ctx.send(embed=em)

            queue = self.queues.get(ctx.guild.id, [])
            self.queues[ctx.guild.id] = queue
            data = await self.get_song(data)
            queue.append(data)
            return

        def end_music(e):
            self.now_playing[ctx.guild.id] = {}
            curr_voice = ctx.guild.voice_client
            channel = curr_voice.channel
            if len(channel.members) == 1: # we are the only one in the channel
                self.queues[ctx.guild.id] = []
                self.bot.loop.create_task(curr_voice.disconnect())

            queue = self.queues.get(ctx.guild.id, [])
            try:
                next_song = queue.pop(0)
            except IndexError:
                self.bot.loop.create_task(curr_voice.disconnect())
                return
            self.queues[ctx.guild.id] = queue

            em = self.format_song_embed(next_song)
            em.set_footer(text='Now playing.')
            self.bot.loop.create_task(ctx.send(embed=em))

            vol = self.volumes.get(ctx.guild.id, 0.5)
            audio_src = YoutubeSource(next_song['file'])
            volume_src = discord.PCMVolumeTransformer(audio_src, volume=vol)
            curr_voice.play(volume_src, after=end_music)
            self.now_playing[ctx.guild.id] = next_song

        vol = self.volumes.get(ctx.guild.id, 0.5)

        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.description = 'Downloading song...'
        msg = await ctx.send(embed=em)

        data = await self.get_info_from_query(query=query)
        data['ctx'] = ctx

        if data['duration'] > 600:
            return await ctx.send('Song is too long.')

        data = await self.get_song(data)
        em = self.format_song_embed(data)
        a_url = ctx.author.avatar_url_as(format='png', size=1024)
        em.set_footer(text=f'{ctx.author} started playing a song.', icon_url=a_url)
        await msg.edit(embed=em)

        audio_src = YoutubeSource(data['file'])
        volume_src = discord.PCMVolumeTransformer(audio_src, volume=vol)
        curr_voice.play(volume_src, after=end_music)
        self.now_playing[ctx.guild.id] = data

    @music.command(name='next', aliases=['skip'])
    async def _next(self, ctx):
        """Plays the next song in the queue.
        """
        voice = ctx.guild.voice_client
        if not voice:
            return

        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.description = 'Skip the currently playing song?'
        msg = await ctx.send(embed=em)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')

        await asyncio.sleep(15)

        async for message in ctx.channel.history():
            if message.id == msg.id:
                vote = message
                break

        voice = ctx.guild.voice_client # re-fetch the voice client
        if not voice:
            return
        if not voice.is_playing():
            return # we're no longer playing music

        yes_count = {}
        no_count = {}

        for reaction in vote.reactions:
            if reaction.emoji == '✅':
                yes_count['num'] = reaction.count
                yes_count['users'] = await reaction.users().flatten()
            elif reaction.emoji == '❌':
                no_count['num'] = reaction.count
                no_count['users'] = await reaction.users().flatten()

        try:
            await msg.delete()
        except discord.HTTPException:
            pass # couldn't delete

        duplicates = len(set(yes_count['users']).intersection(no_count['users'])) # Fail-safe for duplicates

        yes_count['num'] -= duplicates
        no_count['num'] -= duplicates

        total = yes_count['num'] + no_count['num']

        if yes_count['num']/total > 0.5:
            em.description = '✅ Vote passed.'
            await ctx.send(embed=em)
            voice.stop()
        else:
            em.description = '❌ Vote failed.'
            await ctx.send(embed=em)

    @music.command()
    @commands.has_permissions(mute_members=True)
    async def pause(self, ctx):
        """Pauses the music.
        """
        voice = ctx.guild.voice_client
        if not voice:
            return

        if voice.is_paused():
            return

        if voice.is_playing():
            voice.pause()

    @music.command()
    @commands.has_permissions(mute_members=True)
    async def resume(self, ctx):
        """Resumes the music.
        """
        voice = ctx.guild.voice_client
        if not voice:
            return

        if voice.is_playing():
            return

        if voice.is_paused():
            voice.resume()

    @music.command()
    async def stop(self, ctx):
        """Stops playing music.
        """
        voice = ctx.guild.voice_client
        if not voice:
            return

        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.description = 'Stop playing music?'
        msg = await ctx.send(embed=em)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')

        await asyncio.sleep(15)

        async for message in ctx.channel.history():
            if message.id == msg.id:
                vote = message
                break

        voice = ctx.guild.voice_client # re-fetch the voice client
        if not voice:
            return
        if not voice.is_playing():
            return # we're no longer playing music

        yes_count = {}
        no_count = {}

        for reaction in vote.reactions:
            if reaction.emoji == '✅':
                yes_count['num'] = reaction.count
                yes_count['users'] = await reaction.users().flatten()
            elif reaction.emoji == '❌':
                no_count['num'] = reaction.count
                no_count['users'] = await reaction.users().flatten()

        try:
            await msg.delete()
        except discord.HTTPException:
            pass # couldn't delete

        duplicates = len(set(yes_count['users']).intersection(no_count['users'])) # Fail-safe for duplicates

        yes_count['num'] -= duplicates
        no_count['num'] -= duplicates

        total = yes_count['num'] + no_count['num']

        if yes_count['num']/total > 0.5:
            em.description = '✅ Vote passed.'
            await ctx.send(embed=em)
            self.queues[ctx.guild.id] = []
            voice.stop()
            self.now_playing[ctx.guild.id] = {}
        else:
            em.description = '❌ Vote failed.'
            await ctx.send(embed=em)

    @music.command()
    async def volume(self, ctx, volume: int=None):
        """Sets the volume of the audio."""

        if not volume:
            vol = self.volumes.get(ctx.guild.id, 0.5)
            prct = vol * 100
            return await ctx.send(f'Current volume is set to **{prct}%**.')

        if not 1 <= volume <= 100:
            await ctx.send('Volume must be a number 1-100.')
            return

        volume = volume/100
        self.volumes[ctx.guild.id] = volume

        voice = ctx.guild.voice_client
        if voice and voice.is_playing():
            src = voice.source
            src.volume = volume

    @music.command(aliases=['summon'])
    async def join(self, ctx, *, channel_name: str=None):
        """Joins a voice channel.

        If the bot is already in a voice channel, it will move the bot.
        """
        channel = None
        if channel_name:
            lower_names = [channel.name.lower() for channel in ctx.guild.voice_channels]
            names = [channel.name for channel in ctx.guild.voice_channels]
            name_dict = dict(zip(lower_names, names))
            name = name_dict.get(channel_name, 'no channel')
            channel = discord.utils.get(ctx.guild.voice_channels,
                                            name=name)

        if not channel:
            voice = ctx.author.voice
            if not voice:
                return
            channel = voice.channel

        curr_voice = ctx.guild.voice_client
        if curr_voice and channel.id != curr_voice.channel.id:
            await curr_voice.move_to(channel)
            return

        await channel.connect()

    @music.command(aliases=['dc', 'disconnect'])
    async def leave(self, ctx):
        """Leave the voice channel and disconnect from all voice.
        """
        curr_voice = ctx.guild.voice_client
        if not curr_voice:
            return

        if curr_voice.is_playing():
            curr_voice.stop()

        self.queues[ctx.guild.id] = []
        await curr_voice.disconnect()

    @music.command()
    async def queue(self, ctx):
        """Views the song queue."""
        queue = self.queues.get(ctx.guild.id, [])
        em = discord.Embed()
        em.color = discord.Colour.blurple()
        if not queue:
            em.description = 'No songs are in the queue.'
            return await ctx.send(embed=em)

        em.title = 'Song Queue'
        lst = []
        for i, data in enumerate(queue):
            lst.append(f'**{i+1}.** {data["uploader"]} - {data["title"]}')
            if i+1 >= 10:
                left = len(queue) - 10
                if left > 0:
                    lst.append(f'+ {left} more.')
                break

        em.description = '\n'.join(lst)

        await ctx.send(embed=em)

    @music.command()
    async def playing(self, ctx):
        """Shows the currently playing song."""
        voice = ctx.guild.voice_client
        if not voice:
            return

        if not voice.is_playing():
             return await ctx.send('Not playing any songs.')

        data = self.now_playing.get(ctx.guild.id, {})
        if not data:
            return

        em = self.format_song_embed(data)
        em.set_footer(text='Now playing.')

        await ctx.send(embed=em)

    @music.command(hidden=True)
    async def info(self, ctx):
        """Shows stats for nerds."""
        voice = ctx.guild.voice_client
        if not voice:
            return

        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.title = 'Voice Connection Stats'

        if voice.is_playing():
            src = voice.source.original
            audio_bytes = str(src.read())

            transformations = {
                re.escape(c): '\\' + c
                for c in ('*', '`', '_', '~', '\\', '<')
            }

            def replace(obj):
                return transformations.get(re.escape(obj.group(0)), '')
            pattern = re.compile('|'.join(transformations.keys()))
            audio_bytes = pattern.sub(replace, audio_bytes)

            bytes_per_ms = math.ceil(len(audio_bytes) / 20)
            em.add_field(name='PCM Bytes (sliced to 1 ms)', value=f'{audio_bytes[:bytes_per_ms]}\n\n')

        connected_guilds = [guild for guild in self.bot.guilds if guild.voice_client]

        em.add_field(name='Session ID', value=f'{voice.session_id}\n')
        em.add_field(name='Endpoint', value=f'{voice.endpoint}\n')
        em.add_field(name='Connections', value=f'{len(connected_guilds)}')

        await ctx.send(embed=em)

# I put all the ugly code down here. It's really gross, just warning you.


    async def get_info_from_query(self, *, query: str):
        """Takes a query and gets info, including a URL.
        """
        opts = {
            'format': 'webm[abr>0]/bestaudio/best',
            'prefer_ffmpeg': True,
            'default_search': 'auto',
            'quiet': True,
        }
        ytdl = youtube_dl.YoutubeDL(opts)
        func = functools.partial(ytdl.extract_info, query, download=False)
        info = await self.bot.loop.run_in_executor(None, func)
        if 'entries' in info:
            info = info['entries'][0]

        data = {}
        data['url'] = info['url']
        data['views'] = info.get('view_count')
        data['likes'] = info.get('like_count')
        data['dislikes'] = info.get('dislike_count')
        data['duration'] = info.get('duration')
        data['uploader'] = info.get('uploader')
        data['title'] = info.get('title')
        data['description'] = info.get('description')
        data['id'] = info.get('id')
        data['info'] = info

        return data

    async def get_song(self, data):
        """Downloads a song with a URL.
        """

        guild = data['ctx'].guild
        if not os.path.exists(f'music_files/{guild.id}'):
            os.mkdir(f'music_files/{guild.id}')

        file_name = f'{data["id"]}.mp3'
        if file_name not in os.listdir(f'music_files/{guild.id}'):
            async with aiohttp.ClientSession() as s:
                async with s.get(data['url']) as resp:
                    with open('music_files/{}/{}.mp3'.format(guild.id, data['id']), 'wb') as fp:
                        fp.write(await resp.read())

        data['file'] = 'music_files/{}/{}.mp3'.format(guild.id, data['id'])
        return data

    def format_song_embed(self, data):
        """Formats a nice embed for song data.
        """
        em = discord.Embed()
        em.color = discord.Colour.blurple()

        em.title = '{} - {}'.format(data['title'], data['uploader'])

        m, s = divmod(data['duration'], 60)

        em.add_field(name='Views', value=data['views'])
        em.add_field(name='Likes', value=data['likes'])
        em.add_field(name='Dislikes', value=data['dislikes'])
        em.add_field(name='Duration', value=f'{m:0>2}:{s:0>2}')
        em.add_field(name='Requested By', value=str(data['ctx'].author))
        em.url = r'https://www.youtube.com/watch?v={}'.format(data['id'])
        try:
            em.set_image(url=data['info']['thumbnails'][0]['url'])
        except KeyError:
            pass

        return em

    async def on_voice_state_update(self, member, before, after):
        guild = member.guild
        me = guild.me
        if not after.channel and member.id == me.id:
            self.queues[guild.id] = [] # clear queue when we leave the channel
            self.now_playing[guild.id] = {} # clear now playing
            await asyncio.sleep(3)
            shutil.rmtree(f'music_files/{guild.id}')


def setup(bot):
    bot.add_cog(Music(bot))
