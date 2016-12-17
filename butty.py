#!/usr/bin/env python
import sqlite3
import logging
import os
import traceback

import discord
from discord.ext import commands
import cogs.prefix

prefix = cogs.prefix.Prefix()

real_path = os.path.dirname(os.path.realpath(__file__)) + "/"
os.chdir(real_path)

database = sqlite3.connect("cogs/buttybot.db")
c = database.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS prefixes
             (id text, prefix text)''')

description = '''Butty. All you need, and more, less some things you need'''
bot = commands.Bot(command_prefix=prefix.get_prefix, description=description)

# add cogs here after putting them in cogs folder (format cogs.<name of file without extension>)
startup_extensions = ["cogs.reminders", "cogs.voice", "cogs.misc", "cogs.logs"]


logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
if not os.path.exists('extras/metalogs'):
    os.makedirs('extras/metalogs')
handler = logging.FileHandler(filename='extras/metalogs/discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

@bot.event
async def on_command_error(exception, context):
    message = context.message
    tb = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    await bot.send_message(discord.Object('259634295256121345'), "COMMAND **{}** IN **{}** ({}) \n```Python\n{}```".format(message.content, message.server.name, message.server.id, tb))

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
    if message.server and message.server.id == '204621105720328193' and ('nsfw' in message.content or 'NSFW' in message.content):
        await bot.send_message(message.channel, "(not safe for women)")
    
    await bot.process_commands(message)
    
    if message.content.startswith('['):
        await bot.send_message(discord.Object('237608005166825474'), "**{}** ({})\n**{}** ({})\n{}".format(message.server.name, message.server.id, message.author.name, message.author.id, message.content))
        
try:
    with open("extras/token", 'r') as Token:
        token = Token.read()
        bot.run(token)
except FileNotFoundError:
    print("token not found\nplease create a file called \"token\" in the \"extras\" folder and put the token in that")
