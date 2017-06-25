#!/usr/bin/env python3
import traceback
import time
from collections import defaultdict
from functools import wraps

import discord
from discord.ext import commands
import cogs.prefix

# setup for "secret" (server specific) stuff


def event(self, coro):
    @wraps(coro)
    async def wrapper(*args, **kwargs):
        func = self.secrets.get(coro.__name__, [])
        for command in func:
            await command(*args, **kwargs)
        await coro(*args, **kwargs)
    return self.event_dec(wrapper)


def secret(self, func):
    self.secrets[func.__name__].append(func)

commands.Bot.event_dec = commands.Bot.event
commands.Bot.secret = secret
commands.Bot.event = event


prefix = cogs.prefix.Prefix()

description = '''Butty. All you need, and more, less some things you need'''
bot = commands.Bot(command_prefix=prefix.get_prefix, description=description)

bot.voice_reload_cache = None
bot.startup_time = time.time()
bot.secrets = defaultdict(list)

bot.remove_command("help")  # TODO: wtf harru why is this here

# add cogs here after putting them in cogs folder (format cogs.<name> of file without extension>)
startup_extensions = ["cogs.reminders", "cogs.voice", "cogs.misc", "cogs.ascii", "cogs.help", "cogs.secret"]
# TODO: remove cogs.secret from startup?
# I don't want any differences between git and live version
# i guess just don't sync secret.py?


@bot.event
async def on_command_error(exception, context):
    if type(exception) == discord.ext.commands.errors.CommandNotFound:
        return

    message = context.message
    tb = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))

    reply = "COMMAND **{}** IN **{}** ({})".format(message.content, message.server.name, message.server.id)
    reply += "\n```py\n{}```".format(tb[len(reply)-1988:])
    await bot.send_message(discord.Object('259634295256121345'), reply)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    await bot.change_presence(game=discord.Game(name='"[help" for help'))

    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))


@bot.event
async def on_message(message):
    await bot.process_commands(message)


# defined here so it can't be accidentally unloaded
@bot.command(name="reload", hidden=True, pass_context=True)
async def reload_module(ctx, module):
    if ctx.message.author.id == '135483608491229184' or ctx.message.author.id == '135496683009081345':
        bot.unload_extension(module)
        bot.load_extension(module)
        await bot.say("done")

try:
    with open("extras/token", 'r') as Token:
        token = Token.read()
        bot.run(token)
except FileNotFoundError:
    print('token not found\nplease create a file called "token" in the "extras" folder and put the token in that')
