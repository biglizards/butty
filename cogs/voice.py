import asyncio
import math
import random
import time
from functools import wraps

import discord
import discord.ext.commands as commands
import youtube_dl
from youtubesearchpython import SearchVideos

import cogs.voice_lib.parser as parser
from cogs.misc import is_admin, slash_command
from error import send_error_log

quips = {'skip': "B-b-but I haven't even got started...",
         'queue': 'The queue is empty, use /play to play something',
         'remove': 'I tried to remove the silence from the queue, but it keeps coming back',
         'playing': "Currently playing: `John Cage's 4'33`",
         'leave': "Can't leave if I've never joined :taphead:",
         'loop': "Don't worry, the currently playing silence is already looping",
         'volume': "I'm not sure I can change the volume of silence",
         'shuffle': "I can do a dance, but there's nothing in the queue",
         'pause': "Wow you sure have nothing playing right now. Why would you pause nothing, "
                  "that doesn't even make sense",
         'resume': 'DW nothing was paused to begin with'
         }


def is_author(ctx, song=None):
    if song is None:
        song = ctx.voice_client.song
    return is_admin(ctx) or song.author == ctx.author


def requires_voice_client(func):
    @wraps(func)
    async def temp(*args, **kwargs):
        ctx = args[1]
        if not hasattr(ctx.voice_client, 'ready'):
            quip = quips.get(ctx.command.name, 'I need to be in voice to do this; use /play to play something')
            return await ctx.respond(quip, ephemeral=True)
        return await func(*args, **kwargs)

    return temp


def requires_playing(func):
    @wraps(func)
    async def temp(*args, **kwargs):
        ctx = args[1]
        if not (ctx.voice_client and ctx.voice_client.is_playing()):
            quip = quips.get(ctx.command.name, 'I need to be playing to do this; use /play to play something')
            return await ctx.respond(quip, ephemeral=True)
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
            return ''

        m, s = divmod(int(duration), 60)
        h, m = divmod(m, 60)

        if h:
            length = f'({h}:{m:02d}:{s:02d})'
        else:
            length = f'({m}:{s:02d})'

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
    async def join_voice(ctx) -> bool:
        if not ctx.author.voice:
            await ctx.respond('Join a voice channel first, smh', ephemeral=True)
            return False

        if not ctx.author.voice.channel.permissions_for(ctx.me).connect:
            await ctx.respond("I don't have permission to join that channel; ask a moderator to let me in")
            return False

        await ctx.author.voice.channel.connect()
        ctx.voice_client.queue = []
        ctx.voice_client.queue_loop = None
        ctx.voice_client.looping = False
        ctx.voice_client.song = None
        ctx.voice_client.ready = True
        # allow opus? when false, forces transcoding.
        ctx.voice_client.use_opus = ctx.guild.id != 165800036557520896

        return True

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
            await next_song.ctx.channel.send(
                f"I couldn't play `{next_song.name}`, sorry\n"
                f"If you think this is a bug, feel free to report it"
            )
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
                # if song.first, we already responded to the command, and if we're looping, it must not be a new song
                if not (song.first or ctx.voice_client.looping):
                    await ctx.send(f'Now playing: `{song.name}` {song.length}')
            except Exception as e:
                await send_error_log(ctx, e, bot=self.bot, is_voice=True)

    def start_queue_loop(self, ctx):
        if not ctx.voice_client.queue_loop or ctx.voice_client.queue_loop.done():
            ctx.voice_client.queue_loop = self.bot.loop.create_task(self.do_loop(ctx))
            return not ctx.voice_client.is_playing()
        return False

    @slash_command(name='play', aliases=['p'])
    async def voice_play(self, ctx, song_name):
        # song_name = ' '.join(song_name)

        if not ctx.voice_client:
            if not await self.join_voice(ctx):
                # we failed to join voice, and already gave an error message
                return

        if not hasattr(ctx.voice_client, 'ready'):  # can happen if someone plays two songs before butty can join
            await ctx.respond("Woah, I'm still trying to join from the first command\ngive me a minute", ephemeral=True)
            return

        reply = await ctx.respond('<a:loading:957285111118843984>')

        try:
            info = await self.bot.loop.run_in_executor(
                None, lambda: self.get_info(song_name, search='auto', ctx=ctx)
            )
            song = Song(info, ctx, module=self)
        except Exception as e:
            return await send_error_log(ctx, e, bot=self.bot, is_voice=True)

        ctx.voice_client.queue.append(song)
        song.first = self.start_queue_loop(ctx)

        msg = (f'Now playing: `{song.name}` {song.length}' if song.first
               else f'`{song.name}` {song.length} added to queue')
        await reply.edit_original_message(content=msg)

    @slash_command(name='current_song', aliases=['cp'])
    @requires_voice_client
    async def voice_playing(self, ctx):
        if not ctx.voice_client.is_playing() and ctx.voice_client.song:
            song = ctx.voice_client.song
            reply = f'Nothing is playing, but the last played song was `{song.name}` {song.length}'
        else:
            try:
                song = ctx.voice_client.source.song
            except AttributeError:
                try:
                    song = ctx.voice_client.song
                except AttributeError:
                    return  # it actually wasn't playing (thanks d.py)
            reply = f'Currently playing: `{song.name}` {song.length} {"on loop" if ctx.voice_client.looping else ""}'
        await ctx.respond(reply)

    @slash_command(name='queue', aliases=['q'])
    @requires_voice_client
    async def voice_queue(self, ctx):
        contents = '\n'.join(f'{i + 1}: `{song.name}`'
                             for i, song in enumerate(ctx.voice_client.queue))
        if not contents:
            reply = 'Queue is empty, use /play to play something'
        else:
            reply = f'Queue:\n{contents}'
        if len(reply) > 2000:
            reply = f'{reply[:1963]}`\nalso more, but the list is too full'
        await ctx.respond(reply)

    @slash_command(name='loop')
    @requires_voice_client
    async def voice_loop(self, ctx):
        if ctx.voice_client.song is None:
            await ctx.respond(quips.get('loop'))
            return
        ctx.voice_client.looping = not ctx.voice_client.looping
        if ctx.voice_client.looping:
            self.start_queue_loop(ctx)
        await ctx.respond(f'looping is now {"on" if ctx.voice_client.looping else "off"}')

    @slash_command(name='shuffle')
    @requires_voice_client
    async def voice_shuffle(self, ctx):
        random.shuffle(ctx.voice_client.queue)
        ctx.respond('queue shuffled')

    @slash_command(name='remove', aliases=['qr'])
    @requires_voice_client
    async def voice_remove(self, ctx, i):
        try:
            i = int(i)
            song = ctx.voice_client.queue[i - 1]
        except IndexError:
            return await ctx.respond("Grandmother error: that's not in the queue")
        except ValueError:
            return await ctx.respond("Grandmother error: that's not a number")
        if not is_author(ctx, song):
            return await ctx.respond("You didn't put this on; you can't stop someone else's song")

        ctx.voice_client.queue.pop(i - 1)
        await ctx.respond(f'Removed `{song.name}` from the queue')

    @slash_command(name='clear')
    @requires_voice_client
    async def voice_clear(self, ctx):
        if not all(is_author(ctx, song) for song in ctx.voice_client.queue):
            return await ctx.respond(f"can't clear the queue "
                                     f"(it has someone else's songs in, it would be rude to skip them)")

        ctx.voice_client.queue = []
        await ctx.respond('queue cleared')

    @slash_command(name='leave', aliases=['l'])
    @requires_voice_client
    async def voice_leave(self, ctx):
        if not all(is_author(ctx, song) for song in ctx.voice_client.queue):
            return await ctx.respond('no u')
        await ctx.voice_client.disconnect()
        await ctx.respond(':thumbsup:', ephemeral=True)

    @slash_command(name='skip')
    @requires_voice_client
    async def voice_skip(self, ctx):
        song = ctx.voice_client.song
        if is_author(ctx):
            await ctx.respond(':thumbsup:', delete_after=10)
            return ctx.voice_client.stop()

        votes_needed = math.ceil((len(ctx.voice_client.channel.members) - 1) / 2)

        if ctx.author in song.skips:
            # don't allow double skips
            return await ctx.respond(f'`{song.name}` {song.length} added to queue')

        song.skips.append(ctx.author)
        if votes_needed <= len(song.skips):
            await ctx.respond(f'Song has been skipped by {len(song.skips)} users')
            ctx.voice_client.song.skips = []
            ctx.voice_client.stop()
        else:
            await ctx.respond(f'Voting to skip `{song.name}` ({len(song.skips)}/{votes_needed} votes needed)')

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
            # sometimes this returns None (usually if two people try to play something at once)
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:
                info = info['entries'][0]

            return info
        except (youtube_dl.DownloadError, TypeError) as e:
            if not url.startswith('http://') and not url.startswith('https://') and retry:
                return self.get_info(SearchVideos(url, mode='list', max_results=1).result()[0][2], ytdl_opts=ytdl_opts,
                                     search=search, retry=False)
            raise e


def setup(bot):
    bot.add_cog(Voice(bot))
