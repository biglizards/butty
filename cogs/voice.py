import asyncio
import collections
import random
import time

import youtube_dl
from discord.ext.commands import command

import cogs.voice_lib.parser as parser


class Song:
    def __init__(self, info, author):
        self.length = self.get_length(info.get('duration'))
        self.page_url = info.get('webpage_url')
        self.media_url = info.get('url')
        self.codec = info.get('acodec')
        self.name = info.get('title')
        self.author = author

        self.made_at = time.time()

    @staticmethod
    def get_length(duration):
        if not duration:
            return ""

        m, s = divmod(duration, 60)
        h, m = divmod(m, 60)

        if h:
            length = '({}:{}:{})'.format(h, m, s)
        else:
            length = '({}:{})'.format(m, s)

        return length

    def refresh_info(self):
        if time.time() < self.made_at + 5:
            return

        print("refreshing")
        info = get_info(self.page_url)
        self.__init__(info, self.author)


class Voice:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def join_voice(ctx):
        if not ctx.author.voice:
            await ctx.send("Join a voice channel")
            return
        await ctx.author.voice.channel.connect()
        ctx.voice_client.queue = []
        ctx.voice_client.queue_loop = None
        ctx.voice_client.looping = False

    @staticmethod
    def play_next_in_queue(voice_client):
        if voice_client.looping:
            next_song = voice_client.source.song
        else:
            next_song = voice_client.queue.pop(0)

        source = parser.get_source(next_song)
        voice_client.play(source)

        return next_song

    async def loop_task(self, ctx):
        while ctx.voice_client.queue:
            try:
                if ctx.voice_client.is_playing():
                    await asyncio.sleep(1)
                    continue
                song = self.play_next_in_queue(ctx.voice_client)
                await ctx.send('Now playing: `{0.name}`'.format(song))
            except IndexError:
                print("pretty sure this should never happen")
                break
            except:
                print("ok this REALLY should never happen")
                raise

    @command("play")
    async def voice_play(self, ctx, *song_name):
        song_name = ' '.join(song_name)

        async with ctx.typing():
            info = get_info(song_name, search="auto")
            song = Song(info, ctx.author)

        if not ctx.voice_client:
            await self.join_voice(ctx)

        if not ctx.voice_client.queue_loop or ctx.voice_client.queue_loop.done():
            ctx.voice_client.queue_loop = self.bot.loop.create_task(self.loop_task(ctx))

        ctx.voice_client.queue.append(song)
        if ctx.voice_client.is_playing():
            await ctx.send("`{0.name}` added to queue".format(song))

    @command("stop")
    async def voice_stop(self, ctx):
        ctx.voice_client.stop()  # TODO check if admin etc

    @command("playing")
    async def voice_playing(self, ctx):
        if ctx.voice_client and ctx.voice_client.source:
            song = ctx.voice_client.source.song
            await ctx.send("Currently playing: `{0.name}`".format(song))
        else:
            await ctx.send("Now playing: `John Cage's 4'33` (use [play)")

    @command("queue")
    async def voice_queue(self, ctx):

        reply = "Queue:" + '\n'.join("{0}: `{1.name}`".format(i, song)
                                     for i, song in enumerate(ctx.voice_client.queue))
        await ctx.send(reply)

    @command("loop")
    async def voice_loop(self, ctx):
        ctx.voice_client.looping = not ctx.voice_client.looping

    @command("shuffle")
    async def voice_shuffle(self, ctx):
        random.shuffle(ctx.voice_client.queue)

    @command("remove")
    async def voice_remove(self, ctx, i):
        song = ctx.voice_client.queue.pop(i-1)
        await ctx.send("removed `{0.name}` from the queue".format(song))

    @command("clear")
    async def voice_clear(self, ctx):
        ctx.voice_client.queue = []

    @command("volume")
    async def voice_volume(self, ctx, volume):
        await ctx.send("TODO implement volume for opus")

    @command("leave")
    async def voice_leave(self, ctx):
        await ctx.voice_client.disconnect()


def get_info(url, ytdl_opts=None, search=None):
    opts = {
        'format': '249/250/251/webm[abr>0]/bestaudio/best',
        'quiet': True,
        'default_search': search,
    }

    if ytdl_opts:
        opts.update(ytdl_opts)

    ydl = youtube_dl.YoutubeDL(opts)
    info = ydl.extract_info(url, download=False)

    if "entries" in info:
        info = info['entries'][0]

    return info


def setup(bot):
    bot.add_cog(Voice(bot))


