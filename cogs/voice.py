import asyncio
import traceback

from discord.ext import commands

import cogs.misc as misc

class Song:
    def __init__(self, player, message, loop=False):
        self.player = player

        self.message = message
        self.user = message.author
        self.channel = message.channel
        
        self.title = self.player.title
        self.url = self.player.url
        
        self.loop = loop

        try:
            m, s = divmod(self.player.duration, 60)
            h, m = divmod(m, 60)

            if h:
                self.duration = "{}:{}:{}".format(h,m,s)
            elif m:
                self.duration = "{}:{}".format(m, s)
            else:
                self.duration = "{}".format(s)
        except:
            self.duration = "it's a stream"
            self.title = self.url.split("/")[2].split(":")[0]



class VoiceClient:
    def __init__(self, channel, bot_):
        self.bot = bot_

        self.channel = channel
        self.server = channel.server

        self.current_song = None
        self.player = None
        self.volume = 0.2
        self.queue = []

        self.loop = self.bot.loop.create_task(self.main_loop())

    @property
    def client(self):
        return self.bot.voice_client_in(self.server)

    async def play_next_in_queue(self):
        options = {
            'default_search': 'auto',
            'quiet': True,
            'ignoreerrors': True,
        }
        try:
            song = self.queue[0]
            if not song.loop:
                del self.queue[0]
        except IndexError:
            print("error: Nothing next in queue")
            return None

        self.player = await self.client.create_ytdl_player(song.url, ytdl_options=options)
        self.player.volume = self.volume
        self.current_song = Song(self.player, song.message)

        await self.bot.send_message(self.current_song.channel, "now playing `{}` ({})".format(
            self.current_song.title, self.current_song.duration))

        self.player.start()

    async def add_to_queue(self, name, message, loop=False):
        options = {
            'default_search': 'auto',
            'quiet': True,
            'ignoreerrors': True,
            # 'skip_download': True,
        }

        if not self.client:
            await self.bot.join_voice_channel(self.channel)

        song = Song(await self.client.create_ytdl_player(name, ytdl_options=options, before_options='-help'), message, loop)
        song.player = None
        self.queue.append(song)

        if self.player and self.player.is_playing():
            await self.bot.send_message(song.channel, "`{}` added to queue ({})".format(song.title, song.duration))

    async def main_loop(self):
        while True:
            try:
                await asyncio.sleep(1)
                if self.queue and (not self.player or not self.player.is_playing()):
                    await self.play_next_in_queue()
            except Exception as e:
                print(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
    

class Voice:
    def __init__(self, bot_):
        self.bot = bot_
        self.voice_clients = {}
        if self.bot.voice_reload_cache is not None:
            self.voice_clients = self.bot.voice_reload_cache.copy()
            self.bot.voice_reload_cache = None

    def __unload(self):
        self.bot.voice_reload_cache = self.voice_clients


    '''
    @commands.group(pass_context=True)
    async def voice(self, context):
        if not context.invoked_subcommand:
            context.invoked_with = "help"
            await commands.bot._default_help_command(context, "voice")
    '''
    @commands.command(name="play", aliases=['add', 'p'], pass_context=True)
    async def voice_play(self, context, *song: str):
        """Search for and play something

        Examples:
          play relaxing flute sounds
          play https://www.youtube.com/watch?v=y_gknRMZ-OU
        """
        if not song:
            context.invoked_with = "help"
            await commands.bot._default_help_command(context, "play")
        message = context.message

        voice = self.voice_clients.get(message.server.id)

        if not voice or not voice.client:
            if message.author.voice_channel:
                voice = VoiceClient(message.author.voice_channel, self.bot)
                self.voice_clients[message.server.id] = voice
            else:
                await self.bot.say("You aren't connected to a voice channel")
                return

        await voice.add_to_queue(' '.join(song), message)

    @commands.command(name="stop", aliases=['skip', 's'], pass_context=True)
    async def voice_stop(self, context):
        """Skips the currently playing song"""
        voice = self.voice_clients.get(context.message.server.id)
        if voice.current_song.user != context.message.author and not misc.is_admin(context):
            await self.bot.say("You can't stop the music~~\n(you're not the person who put this on)")
            return None
        voice.player.stop()

    @commands.command(name="queue", aliases=['q'], pass_context=True)
    async def voice_queue(self, context):
        """Show the songs currently in the queue

        Because discord only allows 2000 characters per message,
        sometimes not all songs in the queue can be shown"""
        message = context.message

        voice = self.voice_clients.get(message.server.id)
        if not voice:
            self.bot.say("You haven't joined a voice channel; there is not queue")
            return None

        reply = "Current queue:"
        counter = 1
        for song in voice.queue:
            reply += "\n{}: `{}` ({})".format(counter, song.title, song.duration)
            counter += 1
        await self.bot.say(reply)

    @commands.command(name="remove", aliases=['qr'], pass_context=True)
    async def voice_remove(self, context, number):
        voice = self.voice_clients.get(context.message.server.id)
        song = voice.queue[int(number)-1]
        if song.user != context.message.author and not misc.is_admin(context):
            await self.bot.say("You can't stop the music~~\n(you're not the person who put this on)")
            return None
        await self.bot.say("Removed `{}` from the queue".format(song.title))
        del voice.queue[int(number)-1]

    @commands.command(name="playing", aliases=['cp', 'pl'], pass_context=True)
    async def voice_playing(self, context):
        voice = self.voice_clients.get(context.message.server.id)
        song = voice.current_song
        await self.bot.say("now playing `{}` ({})".format(song.title, song.duration))

    @commands.command(name="leave", aliases=['l'], pass_context=True)
    async def voice_leave(self, context):
        voice = self.voice_clients[context.message.server.id]
        if not misc.is_admin(context):
            for song in voice.queue:
                if song.user != context.message.author:
                    await self.bot.say("You can't stop the music~~\n(someone else still has something queued)")
                    return None
            if voice.current_song.user != context.message.author:
                await self.bot.say("You can't stop the music~~\n(someone else is playing something)")
        await voice.client.disconnect()
        voice.client = None
        voice.queue = []
        voice.player.stop()
        del self.voice_clients[context.message.server.id]
        
    @commands.command(name="loop", aliases=['loopadoop'], pass_context=True)
    async def voice_loop(self, context):
        if not misc.is_admin(context):
            return None
        voice = self.voice_clients.get(context.message.server.id)
        await voice.add_to_queue(voice.current_song.url, context.message, True)
        
    @commands.command(name="volume", aliases=['v'], pass_context=True)
    async def voice_volume(self, context, volume:int):
        voice = self.voice_clients[context.message.server.id]
        voice.volume = volume / 100
        voice.player.volume = volume / 100
        

def setup(bot):
    bot.add_cog(Voice(bot))

    # Todo:
    # Fix any bugs that pop up
    # Pause/resume

