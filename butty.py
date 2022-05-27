#!/usr/bin/env python3
import logging
import time
import traceback
from collections import defaultdict
from functools import wraps
from pathlib import Path

import discord
from discord.ext import commands

import cogs.prefix
from cogs.misc import is_owner
from error import send_error_log

Path('logs').mkdir(exist_ok=True)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='logs/discord.{}.log'.format(int(time.time())), encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


# note that isinstance(ctx.guild.me, discord.user.User) == False
# i don't know why you would care about that

# setup for "secret" (guild specific) stuff
# this is a horrible hack, TODO improve
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

# begin main butty
prefix = cogs.prefix.Prefix()

intent = discord.Intents.all()
description = '''Butty. All you need, and more, less some things you need'''
bot = commands.Bot(command_prefix=prefix.get_prefix, description=description, intents=intent)

bot.voice_reload_cache = None
bot.startup_time = time.time()
bot.secrets = defaultdict(list)

# add cogs here after putting them in cogs folder (format cogs.<name> of file without extension>)
startup_extensions = ["cogs.voice", "cogs.misc", "cogs.secret", "cogs.reminders", "cogs.ascii"]


# TODO: remove cogs.secret from startup?
# I don't want any differences between git and live version

@bot.event
async def on_command_error(context, exception):
    if type(exception) == discord.ext.commands.errors.CommandNotFound:
        return

    if type(exception) == discord.ext.commands.errors.CheckFailure:
        await context.send("Sorry, this command is admin only. Try asking someone with manage server perms")
        return

    await send_error_log(context, exception, bot)


@bot.event
async def on_connect():
    pass


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    await bot.change_presence(activity=discord.Game(name='loading...'))

    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n  {}'.format(extension, exc))

    print('pending:', bot.pending_application_commands)
    try:
        await bot.sync_commands(force=False)
    except discord.errors.HTTPException:
        # i think this might happen on timeout?
        print('error during load:', bot.pending_application_commands)
    print('LOAD FINISHED')
    await bot.change_presence(activity=discord.Game(name='there is no help command, sorry'))


# defined here so it can't be accidentally unloaded
@commands.check(is_owner)
@bot.command(name="reload", hidden=True)
async def reload_cog(ctx, cog):
    try:
        bot.unload_extension(cog)
    except:
        pass
    bot.load_extension(cog)
    await bot.sync_commands()
    await ctx.send("done")


try:
    with open("extras/token", 'r') as Token:
        token = Token.read().replace('\n', '')
        bot.run(token)
except FileNotFoundError:
    print('token not found\nplease create a file called "token" in the "extras" folder and put the token in that')
