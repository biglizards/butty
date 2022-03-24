import asyncio
import math
import random
import time
from functools import wraps

import discord
import discord.ext.commands as commands
import youtube_dl
from discord.ext.commands import command
from youtubesearchpython import SearchVideos

import cogs.voice_lib.parser as parser
from error import send_error_log
from .misc import is_admin

quips = {"stop": "B-b-but I haven't even got started...",
         "queue": "queue is empty, use [play to play something",
         "remove": "I tried to remove the silence from the queue, but it keeps coming back",
         "playing": "Currently playing: `John Cage's 4'33`",
         "leave": "Can't leave if I've never joined :taphead:",
         "loop": "Don't worry, the currently playing silence is already looping",
         "volume": "I'm not sure I can change the volume of silence",
         "shuffle": "I can do a dance, but there's nothing in the queue",
         "pause": "Wow you sure have nothing playing right now. Why would you pause nothing, "
                  "that doesn't even make sense",
         "resume": "DW nothing was paused to begin with"
         }


def is_author(ctx, song=None):
    if song is None:
        song = ctx.voice_client.song
    return is_admin(ctx) or song.author == ctx.author


def requires_voice_client(func):
    @wraps(func)
    async def temp(*args, **kwargs):
        ctx = args[1]
        if not hasattr(ctx.voice_client, "ready"):
            quip = quips.get(ctx.command.name, "Butty needs to be in voice to do this; use [play to play something")
            return await ctx.send(quip)
        return await func(*args, **kwargs)

    return temp


def requires_playing(func):
    @wraps(func)
    async def temp(*args, **kwargs):
        ctx = args[1]
        if not (ctx.voice_client and ctx.voice_client.is_playing()):
            quip = quips.get(ctx.command.name, "Butty needs to be playing to do this; use [play to play something")
            return await ctx.send(quip)
        return await func(*args, **kwargs)

    return temp  # TODO DRY ?


class Song:
    def __init__(self, info, ctx, module):
        self.length = self.get_length(info.get('duration'))
        self.page_url = info.get('webpage_url')
        self.media_url = info.get('url')
        self.codec = info.get('acodec')
        self.name = info.get('title')
        self.author = ctx.author
        self.skips = []

        self.made_at = time.time()
        self.ctx = ctx
        self.module = module

    @staticmethod
    def get_length(duration):
        if not duration:
            return ""

        m, s = divmod(int(duration), 60)
        h, m = divmod(m, 60)

        if h:
            length = '({}:{}:{})'.format(h, m, s)
        else:
            length = '({}:{})'.format(m, s)

        return length

    def refresh_info(self):
        if time.time() < self.made_at + 10:
            return

        info = self.module.get_info(self.page_url, ctx=self.ctx)
        self.__init__(info, self.ctx, self.module)


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def join_voice(ctx):
        if not ctx.author.voice:
            await ctx.send("Join a voice channel")
            return
        if not ctx.author.voice.channel.permissions_for(ctx.me).connect:
            await ctx.send("I don't have permission to join that channel; ask a moderator to let me in")

        await ctx.author.voice.channel.connect()
        ctx.voice_client.queue = []
        ctx.voice_client.queue_loop = None
        ctx.voice_client.looping = False
        ctx.voice_client.song = None
        ctx.voice_client.ready = True
        ctx.voice_client.use_opus = True  # allow opus? when false, forces transcoding.
        # previously ctx.guild.id != 165800036557520896

    @staticmethod
    def get_next_in_queue(voice_client, pop=False):
        if voice_client.looping:
            return voice_client.song
        elif pop:
            return voice_client.queue.pop(0)
        else:
            return voice_client.queue[0]

    def refresh_next_song(self, voice_client):
        next_song = self.get_next_in_queue(voice_client)
        if isinstance(voice_client.source, discord.FFmpegPCMAudio):
            return
        buffer = voice_client.source.buffer
        if not buffer.parser.is_alive() and len(buffer.packets) < 250:  # TODO check for race conditions
            next_song.refresh_info()

    async def play_next_in_queue(self, ctx):
        voice_client = ctx.voice_client
        next_song = self.get_next_in_queue(voice_client, pop=True)
        try:
            source = await self.bot.loop.run_in_executor(
                None, parser.get_source,
                # args:
                next_song, voice_client.use_opus
            )
        except ConnectionError:
            await next_song.ctx.channel.send("I couldn't play `{}`, sorry\n"
                                             "If you think this is a bug, feel free to report it"
                                             .format(next_song.name))
            raise
        voice_client.play(source)
        voice_client.song = next_song

        return next_song

    async def do_loop(self, ctx):
        while ctx.voice_client.queue or ctx.voice_client.looping:
            if ctx.voice_client.is_playing():
                self.refresh_next_song(ctx.voice_client)
                await asyncio.sleep(1)
                continue
            try:
                song = await self.play_next_in_queue(ctx)
                await ctx.send('Now playing: `{0.name}` {0.length}'.format(song))
            except Exception as e:
                await send_error_log(ctx, e, bot=self.bot, is_voice=True)

    def start_queue_loop(self, ctx):
        if not ctx.voice_client.queue_loop or ctx.voice_client.queue_loop.done():
            ctx.voice_client.queue_loop = self.bot.loop.create_task(self.do_loop(ctx))

    @command("play", aliases=['p'])
    async def voice_play(self, ctx, *song_name):
        song_name = ' '.join(song_name)

        if not ctx.voice_client:
            await self.join_voice(ctx)

        if not hasattr(ctx.voice_client, "ready"):  # can happen if someone plays two songs before butty can join
            await ctx.send("Woah, I'm still trying to join from the first command\ngive me a minute")
            return

        async with ctx.typing():
            try:
                info = await self.bot.loop.run_in_executor(
                    None, lambda: self.get_info(song_name, search="auto", ctx=ctx)
                )
                song = Song(info, ctx, module=self)
            except Exception as e:
                return await send_error_log(ctx, e, bot=self.bot, is_voice=True)

        self.start_queue_loop(ctx)

        ctx.voice_client.queue.append(song)
        if ctx.voice_client.is_playing():
            await ctx.send("`{0.name}` {0.length} added to queue".format(song))

    @command("stop", aliases=['s'])
    @requires_playing
    async def voice_stop(self, ctx):
        if not is_author(ctx):
            return await ctx.send("Only the person who put this on (or server admins) can do this")
        ctx.voice_client.stop()  # TODO check if admin etc

    @command("playing", aliases=['cp'])
    @requires_voice_client
    async def voice_playing(self, ctx):
        if not ctx.voice_client.is_playing() and ctx.voice_client.song:
            song = ctx.voice_client.song
            reply = "Nothing is playing, but the last played song was `{0.name}` {0.length}".format(song)
        else:
            try:
                song = ctx.voice_client.source.song
            except AttributeError:
                try:
                    song = ctx.voice_client.song
                except AttributeError:
                    return  # it actually wasn't playing (thanks d.py)
            reply = "Currently playing: `{0.name}` {0.length}".format(song)
            if ctx.voice_client.looping:
                reply += " on loop"
        await ctx.send(reply)

    @command("queue", aliases=['q'])
    @requires_voice_client
    async def voice_queue(self, ctx):
        contents = '\n'.join("{0}: `{1.name}`".format(i + 1, song)
                             for i, song in enumerate(ctx.voice_client.queue))
        if not contents:
            reply = "Queue is empty, use [play to play something"
        else:
            reply = "Queue:\n" + contents
        if len(reply) > 2000:
            reply = reply[:1963] + '`\nalso more, but the list is too full'
        await ctx.send(reply)

    @command("loop", aliases=['loopadoop'])
    @requires_voice_client
    async def voice_loop(self, ctx):
        if ctx.voice_client.song is None:
            await ctx.send(quips.get('loop'))
            return
        ctx.voice_client.looping = not ctx.voice_client.looping
        if ctx.voice_client.looping:
            self.start_queue_loop(ctx)

    @command("shuffle")
    @requires_voice_client
    async def voice_shuffle(self, ctx):
        random.shuffle(ctx.voice_client.queue)

    @command("remove", aliases=['qr'])
    @requires_voice_client
    async def voice_remove(self, ctx, i):
        try:
            i = int(i)
            song = ctx.voice_client.queue[i - 1]
        except IndexError:
            return await ctx.send("Grandmother error: that's not in the queue")
        except ValueError:
            return await ctx.send("Grandmother error: that's not a number")
        if not is_author(ctx, song):
            return await ctx.send("You didn't put this on; you can't stop someone else's song")

        ctx.voice_client.queue.pop(i - 1)
        await ctx.send("Removed `{0.name}` from the queue".format(song))

    @command("clear")
    @requires_voice_client
    async def voice_clear(self, ctx):
        for song in ctx.voice_client.queue:
            if not is_author(ctx, song):
                return await ctx.send("You didn't put `{}` on; you can't stop someone else's song".format(song.name))

        ctx.voice_client.queue = []

    @command("volume", aliases=['v'], hidden=True)
    @requires_voice_client
    async def voice_volume(self, ctx, volume):
        await ctx.send("Sorry, butty no longer supports volume (thanks discord)\n"
                       "feel free to complain about this at the support server")

    @command("leave", aliases=['l'])
    @requires_voice_client
    async def voice_leave(self, ctx):
        for song in ctx.voice_client.queue:
            if not is_author(ctx, song):
                return await ctx.send("no u")
        await ctx.voice_client.disconnect()

    @command("skip")
    @requires_voice_client
    async def voice_skip(self, ctx):
        song = ctx.voice_client.song
        votes_needed = math.ceil((len(ctx.voice_client.channel.members) - 1) / 2)
        if ctx.author in song.skips:
            return await ctx.send("`{0.name}` {0.length} added to queue /s".format(song))
        song.skips.append(ctx.author)
        if votes_needed <= len(song.skips):
            await ctx.send("Song has been skipped by {} users".format(len(song.skips)))
            ctx.voice_client.song.skips = []
            ctx.voice_client.stop()
        else:
            await ctx.send("Voting to skip `{}` ({}/{} votes needed)".format(song.name, len(song.skips), votes_needed))

    def get_info(self, url, ytdl_opts=None, search=None, retry=True, ctx=None):
        opts = {
            'format': '249/250/251/webm[abr>0]/bestaudio/best',
            'quiet': True,
            'default_search': search,
        }

        if ytdl_opts:
            opts.update(ytdl_opts)

        try:
            ydl = youtube_dl.YoutubeDL(opts)
            info = ydl.extract_info(url, download=False)

            if "entries" in info:
                info = info['entries'][0]

            return info
        except youtube_dl.DownloadError as e:
            if not (url.startswith("http://") or url.startswith("https://")) and retry:
                return self.get_info(SearchVideos(url, mode="list", max_results=1).result()[0][2], ytdl_opts=ytdl_opts,
                                     search=search, retry=False)
            raise e


def setup(bot):
    bot.add_cog(Voice(bot))
