#!/usr/bin/env python
import sqlite3
import logging
import os

import discord
from discord.ext import commands
import cogs.prefix

real_path = os.path.dirname(os.path.realpath(__file__)) + "/"
os.chdir(real_path)


description = '''BAM VOICE TEST HERE'''
bot = commands.Bot(command_prefix='?', description=description)

# add cogs here after putting them in cogs folder (format cogs.<name of file without extension>)
# startup_extensions = ["cogs.reminders", "cogs.voice", "cogs.misc", "cogs.logs"]

voice = ''


@bot.event
async def on_ready():
    global voice
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.event
async def on_message(message):
    global voice
    if message.content == '?join':
        voice = await bot.join_voice_channel(message.author.voice_channel)
try:
    with open("extras/token", 'r') as Token:
        token = Token.read()
        bot.run(token)
except FileNotFoundError:
    print("token not found\nplease create a file called \"token\" in the \"extras\" folder and put the token in that")
