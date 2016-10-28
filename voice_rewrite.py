import asyncio

import discord
from discord.ext import commands

if discord:
    asyncio.sleep(0)


class Song:
    def __init__(self, player, message):
        self.player = player

        self.message = message
        self.user = message.author
        self.channel = message.channel

        self.duration = self.player.duration
        self.title = self.player.title
        self.url = self.player.url


class VoiceClient:
    def __init__(self, client, bot_):
        self.bot = bot_
        self.client = client

        self.current_song = None
        self.player = None
        self.queue = []

        self.loop = self.bot.loop.create_task(self.main_loop())

    async def play_next_in_queue(self):
        options = {
            'default_search': 'auto',
            'quiet': True,
            'ignoreerrors': True,
        }
        try:
            song = self.queue[0]
        except IndexError:
            print("error: Nothing next in queue")
            return None

        self.player = await self.client.create_ytdl_player(song.url, ytdl_options=options)
        self.current_song = Song(self.player, song.message)

        await bot.send_message(self.current_song.channel, "very good, sir")

        self.player.start()

    async def add_to_queue(self, name, message):
        options = {
            'default_search': 'auto',
            'quiet': True,
            'ignoreerrors': True,
            'skip_download': True,
        }

        self.queue.append(
            Song(
                await self.client.create_ytdl_player(name, ytdl_options=options),
                message
            )
        )

    async def play(self):
        pass

    async def main_loop(self):
        while True:
            try:
                await asyncio.sleep(1)
                if self.queue and (not self.player or not self.player.is_playing()):
                    await self.play_next_in_queue()
            except Exception as e:
                print("error: ", e)

class Voice:
    def __init__(self, bot_):
        self.bot = bot_
        self.voice_clients = {}

    '''
    @commands.group(pass_context=True)
    async def voice(self, context):
        if not context.invoked_subcommand:
            context.invoked_with = "help"
            await commands.bot._default_help_command(context, "voice")
    '''
    @commands.command(name="play", pass_context=True)
    async def voice_play(self, context, *song: str):
        """Search for and play something.

        Examples:
          play relaxing flute sounds
          play https://www.youtube.com/watch?v=y_gknRMZ-OU
        """
        message = context.message

        voice = self.voice_clients.get(context.message.server.id)
        if not voice:
            if message.author.voice_channel:
                voice = VoiceClient(await self.bot.join_voice_channel(message.author.voice_channel), bot)
            else:
                await self.bot.say("You aren't connected to a voice channel\nhint do [v j")

        await voice.add_to_queue(' '.join(song), message)

        if voice.player and voice.player.is_playing():
            await bot.say("`{}` added to queue".format(voice.title))

bot = commands.Bot(command_prefix=commands.when_mentioned_or('?'), description='A playlist example for discord.py')
bot.add_cog(Voice(bot))


@bot.event
async def on_ready():
    print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))

bot.run('token')
