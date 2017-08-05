import os
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

    @commands.command()
    async def play(self, ctx, *, query: str):
        """Plays a URL from YouTube."""
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

            if data['duration'] > 600:
                return await ctx.send('Song is too long.')

            em = self.format_song_embed(data)
            a_url = ctx.author.avatar_url_as(format='png', size=1024)
            em.set_footer(text=f'{ctx.author} added a song to the queue.', icon_url=a_url)

            await ctx.send(embed=em)

            queue = self.queues.get(ctx.guild.id, [])
            self.queues[ctx.guild.id] = queue
            path = await self.get_song(data, ctx.guild)
            queue.append(path)
            return

        def end_music(e):
            queue = self.queues.get(ctx.guild.id, [])
            try:
                next_song = queue.pop(0)
            except IndexError:
                self.bot.loop.create_task(curr_voice.disconnect())
                return
            self.queues[ctx.guild.id] = queue

            vol = self.volumes.get(ctx.guild.id, 0.5)
            audio_src = YoutubeSource(next_song)
            volume_src = discord.PCMVolumeTransformer(audio_src, volume=vol)
            curr_voice.play(volume_src, after=end_music)

        vol = self.volumes.get(ctx.guild.id, 0.5)

        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.description = 'Downloading song...'
        msg = await ctx.send(embed=em)

        data = await self.get_info_from_query(query=query)

        if data['duration'] > 600:
            return await ctx.send('Song is too long.')

        url = data['url']

        song = await self.get_song(data, ctx.guild)
        em = self.format_song_embed(data)
        a_url = ctx.author.avatar_url_as(format='png', size=1024)
        em.set_footer(text=f'{ctx.author} started playing a song.', icon_url=a_url)
        await msg.edit(embed=em)

        audio_src = YoutubeSource(song)
        volume_src = discord.PCMVolumeTransformer(audio_src, volume=vol)
        curr_voice.play(volume_src, after=end_music)

    @commands.command(name='next')
    async def _next(self, ctx):
        """Plays the next song in the queue.
        """
        voice = ctx.guild.voice_client
        if not voice:
            return

        if not self.queues.get(ctx.guild.id, []):
            await ctx.send('no songs are queued')
            return

        voice.stop()

    @commands.command()
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

    @commands.command()
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

    @commands.command()
    async def stop(self, ctx):
        """Stops playing music.
        """
        voice = ctx.guild.voice_client
        if not voice:
            return

        if voice.is_playing():
            self.queues[ctx.guild.id] = []
            voice.stop()

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Sets the volume of the audio."""
        if not 1 <= volume <= 100:
            await ctx.send('Volume must be a number 1-100.')
            return

        volume = volume/100
        self.volumes[ctx.guild.id] = volume

        voice = ctx.guild.voice_client
        if voice and voice.is_playing():
            src = voice.source
            src.volume = volume

    @commands.command(aliases=['summon'])
    async def join(self, ctx):
        """Joins a voice channel.

        If the bot is already in a voice channel, it will move the bot.
        """
        voice = ctx.author.voice
        if not voice:
            return
        channel = voice.channel

        curr_voice = ctx.guild.voice_client
        if curr_voice and channel.id != curr_voice.channel.id:
            await curr_voice.move_to(channel)
            return

        await channel.connect()

    @commands.command(aliases=['dc', 'disconnect'])
    async def leave(self, ctx):
        """Leave the voice channel and disconnect from all voice.
        """
        curr_voice = ctx.guild.voice_client
        if not curr_voice:
            return

        if curr_voice.is_playing():
            curr_voice.stop()

        await curr_voice.disconnect()


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

    async def get_song(self, data, guild):
        """Downloads a song with a URL.
        """

        if not os.path.exists(f'music_files/{guild.id}'):
            os.mkdir(f'music_files/{guild.id}')

        if data['id'] not in os.listdir(f'music_files/{guild.id}'):
            async with aiohttp.ClientSession() as s:
                async with s.get(data['url']) as resp:
                    with open('music_files/{}/{}.mp3'.format(guild.id, data['id']), 'wb') as fp:
                        fp.write(await resp.read())

        file_ = 'music_files/{}/{}.mp3'.format(guild.id, data['id'])
        return file_

    def format_song_embed(self, data):
        """Formats a nice embed for song data.
        """
        em = discord.Embed()
        em.color = discord.Colour.blurple()

        em.title = '{} - {}'.format(data['title'], data['uploader'])
        em.add_field(name='Views', value=data['views'])
        em.add_field(name='Likes', value=data['likes'])
        em.add_field(name='Dislikes', value=data['dislikes'])
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
            await asyncio.sleep(3)
            shutil.rmtree(f'music_files/{guild.id}')


def setup(bot):
    bot.add_cog(Music(bot))
