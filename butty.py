#!/usr/bin/env python3
import time
import traceback
from collections import defaultdict
from functools import wraps
import sqlite3

import discord
from discord.ext import commands

import cogs.prefix
from cogs.misc import is_owner


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

description = '''Butty. All you need, and more, less some things you need'''
bot = commands.Bot(command_prefix=prefix.get_prefix, description=description)

bot.voice_reload_cache = None
bot.startup_time = time.time()
bot.secrets = defaultdict(list)

# add cogs here after putting them in cogs folder (format cogs.<name> of file without extension>)
startup_extensions = ["cogs.voice", "cogs.misc", "cogs.secret", "cogs.reminders", "cogs.ascii"]
# TODO: remove cogs.secret from startup?
# I don't want any differences between git and live version


def get_traceback_from_exception(exception, message):
    tb = ''.join(traceback.format_exception(etype=type(exception),
                                            value=exception,
                                            tb=exception.__traceback__))

    if message.guild:
        location = "**{0.name}** ({0.id})".format(message.guild)
    else:
        location = "DM"

    header = "COMMAND **{}** IN {}\n".format(message.content, location)
    error = "```py\n{}```".format(tb[len(header)-1988:])
    return header + error


@bot.event
async def on_command_error(context, exception):
    print("oh no an error", exception)
    if type(exception) == discord.ext.commands.errors.CommandNotFound:
        return

    if type(exception) == discord.ext.commands.errors.CheckFailure:
        await context.send("Sorry, this command is admin only. Try asking someone with manage server perms")
        return

    tb = get_traceback_from_exception(exception, context.message)
    channel = discord.utils.get(bot.get_all_channels(), id=332200389074223105)  # TODO change back to old error channel

    await channel.send(tb)
    await context.send("An unhandled error occured! Tell stalin to check the logs (unless you're just being dumb)")


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    await bot.change_presence(game=discord.Game(name='[help for help'))

    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n  {}'.format(extension, exc))


# defined here so it can't be accidentally unloaded
@commands.check(is_owner)
@bot.command(name="reload", hidden=True)
async def reload_cog(ctx, cog):
    bot.unload_extension(cog)
    bot.load_extension(cog)
    await ctx.send("done")

try:
    with open("extras/token", 'r') as Token:
        token = Token.read().replace('\n', '')
        bot.run(token)
except FileNotFoundError:
    print('token not found\nplease create a file called "token" in the "extras" folder and put the token in that')
