#!/usr/bin/env python
import sqlite3
import logging
import os

import discord
from discord.ext import commands


def get_prefix(bot_, message):
    if message.server is not None and '{0.me.mention} '.format(message.server) in message.content:
        return '{0.me.mention} '.format(message.server)
    elif '{0.user.mention} '.format(bot_) in message.content:
        return '{0.user.mention} '.format(bot_)

    prefix = c.execute("SELECT prefix FROM prefixes WHERE id=?", (message.server.id,)).fetchone()
    if not prefix:
        return '?'
    return prefix[0]

real_path = os.path.dirname(os.path.realpath(__file__)) + "/"
os.chdir(real_path)

database = sqlite3.connect("cogs/buttybot.db")
cursor = database.cursor()
c = cursor

c.execute('''CREATE TABLE IF NOT EXISTS prefixes
             (id text, prefix text)''')

description = '''Butty. All you need, and more, less some things you need'''
bot = commands.Bot(command_prefix=get_prefix, description=description)

# add cogs here after putting them in cogs folder (format cogs.<name of file without extension>)
startup_extensions = ["cogs.reminders", "cogs.voice"]


logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
if not os.path.exists('extras/metalogs'):
    os.makedirs('extras/metalogs')
handler = logging.FileHandler(filename='extras/metalogs/discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name='who ping'))
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))

try:
    with open("extras/token", 'r') as Token:
        token = Token.read()
        bot.run(token)
except FileNotFoundError:
    print("token not found\nplease create a file called \"token\" in the \"extras\" folder and put the token in that")
