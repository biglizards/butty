import os
import re
import time
import urllib
import urllib.parse
import urllib.request


#from cleverbot import Cleverbot
#import threading
#import asyncio
#from bs4 import BeautifulSoup
#import discord


def is_admin(message):
    if message.author.server_permissions.manage_server:
        return True
    elif message.author.id == "135496683009081345" or message.author.id == '135483608491229184':
        return True
    else:
        return False


def should_remove(m):
    if m.content.startswith("["):
        return True
    elif m.author.id == "229223616217088001":
        return True
    else:
        return False


def youtube(search, result_number=1):
    results = []
    query_string = urllib.parse.urlencode({"search_query": search})
    html_content = urllib.request.urlopen("htts://www.youtube.com/results?" + query_string)
    search_results = re.findall(r'href=\"/watch\?v=(.{11})', html_content.read().decode())
    resultno = result_number * 2
    try:
        for x in range(0, resultno):
            if x % 2 == 0:
                results.append("http://www.youtube.com/watch?v=" + search_results[x] + "\n")
        return ''.join(results)
    except IndexError:
        return "failed"


async def cleverchat(message, client, cb):
    if message.author.bot:
        pass
    if should_remove(message):
        pass
    else:
        response = cb.ask(message.content)
        await client.send_typing(message.channel)
        time.sleep(1.5)
        await client.send_message(message.channel, response)


async def togglecommand(client, command, message, cursor, database, blacklist):
    if command == "[togglecommands":
        if is_admin(message):
            if message.channel.id not in blacklist:
                cursor.execute("INSERT INTO blacklist VALUES(?)", (message.channel.id,))
                await client.send_message(message.channel, "Commands disabled")
            else:
                cursor.execute("DELETE FROM blacklist WHERE channelid=?", (message.channel.id,))
                await client.send_message(message.channel, "Commands enabled")
            database.commit()
        else:
            await client.send_message(message.channel, "You don't have permission to do this")
        await client.delete_message(message)
