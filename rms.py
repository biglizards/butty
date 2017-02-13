#!/usr/bin/env python
import sqlite3
import logging
import os

import discord
from discord.ext import commands

description = '''RMS RMS RMS'''
bot = commands.Bot(command_prefix='FUCKYOU', description=description)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.event
async def on_message(message):
    if message.channel.id == '245591692772769793' and message.content.startswith('!kick'):
        dead = discord.Role(server=message.server, id=245593125056282625)
        await bot.add_roles(message.author, dead)


try:
    with open("extras/token", 'r') as Token:
        token = Token.read()
        bot.run(token)
except FileNotFoundError:
    print("token not found\nplease create a file called \"token\" in the \"extras\" folder and put the token in that")
