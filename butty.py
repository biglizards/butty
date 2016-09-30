import discord
from foaas import fuck
# import asyncio
# import random
from cleverbot import Cleverbot
# import time
import sqlite3
from buttymodules import *
# from bs4 import BeautifulSoup
# import urllib
import os
# import sys
# import re
# import threading


# to do list:
# oh god the text is highlighted what
# alerts
# finish random fuck yous
# finish anagram game
# update the help section
# whole server to do lists
# aaaa it highlighted again


class Server:
    def __init__(self, message):
        self.id = message.server.id
        self.channels = {message.channel.id: Channel(message)}
        self.voice = False
        self.player = False


class Channel:
    def __init__(self, message):
        self.id = message.channel.id
        self.channel = message.channel
        self.blacklisted = False
        self.check_blacklist()
        self.cb = False

    def check_blacklist(self):
        bl = cursor.execute("SELECT channelid FROM blacklist where channelid=?", (self.id,)).fetchall()
        if bl:
            self.blacklisted = True
        else:
            self.blacklisted = False

    def toogle_blacklist(self):
        if not self.blacklisted:
            cursor.execute("INSERT INTO blacklist VALUES (?)", (self.id,))
            database.commit()
            # await client.send_message(self.channel, "Commands disabled") FIX THIS
        else:
            cursor.execute("DELETE FROM blacklist WHERE channelid=?", (self.id,))
            database.commit()
            # await client.send_message(self.channel, "Commands enabled")
        self.check_blacklist()
        return self.blacklisted


def get_channel(message):
    server = servers[message.server.id]
    return server.channels[message.channel.id]

async def buttyhelp(message):
    await client.send_message(message.channel, '**Here are the commands:**, <@%s>\n\n' % message.author.id
                              + '**[help** - Show command list\n\n'
                              + '**[bet** or **[balance** - Bet or view my balance using betty\n\n'
                              + '**[invite** - Get the invite link\n\n'
                              + '**[yt (search)** - Search Youtube\n\n'
                              + '**[voice (join/play/stop/leave) (join: voice channel id / play: name of video)** - Join a voice channel/play from youtube/stop playback/leave voice channel\n\n'
                              + '**[duck (search)** - Duck Duck Go it for you\n\n'
                              + '**[flip** - Flip a coin\n\n'
                              + '**[roll (number of sides) [number of dice, default 1]** - Roll (number of dice) each with (number of sides)\n\n'
                              + '**[todo (add/show/remove/clear) (add: thing to add/remove: number to remove)** - Add to todo list/Show todo list/Remove entry from todo list/Clear todo list\n\n'
                              + '**[chat (start/stop)** - Start or stop chat mode\n\n'
                              + '**Any word with butty in** - I say "yes"\n\n'
                              + '**Anything while chat mode is enabled** - I will talk back')

async def makeLogs(message, send=True):
    global logs
    logs = []
    if not os.path.exists('extras/' + message.server.name):
        os.makedirs('extras/' + message.server.name)
    filename = ("extras/" + message.server.name
                + "/"
                + message.channel.name
                + ".new.log")
    if not os.path.isfile(filename):
        line = None
    else:
        with open(filename, "rb") as f:
            first = f.readline()  # Read the first line.
            f.seek(-2, 2)  # Jump to the second last byte.
            while True:
                while f.read(1) != b"\n":  # Until EOL is found...
                    f.seek(-2, 1)  # ...jump back the read byte plus one more.
                last = f.read(1)  # Read first char
                if last != b' ':  # ie if it has the timestamp on it
                    f.seek(-1, 1)
                    line = f.readline()  # read line
                    break
                else:
                    f.seek(-3, 1)  # go back past the newline
    foundit = False
    async for message2 in client.logs_from(message.channel, limit=999999999999999):
        tolog = (message2.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                 + message2.timestamp.strftime('.%f')[0:-3]  # miliseconds
                 + " "
                 + str(message2.author)
                 + ": ")

        if tolog in str(line):
            foundit = True
            break
        ind = " " * len(tolog)
        tolog += str(message2.content).replace("\n", "\n" + ind)
        if message2.attachments:
            if message2.content:
                tolog += " "
            for at in message2.attachments:
                tolog += at['url'] + "\n"
        else:
            tolog += "\n"
        logs.append(tolog)
    if not foundit and line:
        await client.send_message(message.channel,
                                  'something went wrong: last message not found\nsomeone probably deleted it\n(the bot now needs someone to press enter; it\'s frozen)')
        input()
    file = open(filename, mode="a", encoding='utf-8')
    for message2 in reversed(logs):
        file.write(message2)
    file.close()
    if send:
        file = open(filename, mode='rb')
        await client.send_file(message.channel,
                               file,
                               filename=(str(message.timestamp.strftime('%Y-%m-%d')) + ".log"),
                               content="here's your logs.\nstop making me do this\nit hurts so much inside")
        file.close()
    else:
        return filename

async def purge(message, client, channel, limit):
    if is_admin(message):
        if limit > 200:
            await client.send_message(channel, "That's too many, calm down")
        else:
            await client.purge_from(channel, limit=limit, check=should_remove)

async def butty(message):
    if message.author.id != "229223616217088001" and "butty" in message.content:
        await client.send_message(message.channel, "yes")

async def lmddgtfy(message):
    query = urllib.parse.quote(message.content[6:])
    result = "http://lmddgtfy.net/?q=" + query
    await client.send_message(message.channel, result)
    await client.delete_message(message)

cb = Cleverbot()
clever_chatting = {}

client = discord.Client()

servers = {}

if not os.path.exists('extras'):
    os.makedirs('extras')

with open('extras/corncob_lowercase.txt', 'r') as file:
    words = file.read().splitlines()
words_sorted = [sorted(word) for word in words]

database = sqlite3.connect("extras/buttybot.db")
cursor = database.cursor()
# print(cursor.execute("select name from sqlite_master where type='table'").fetchall())
# cursor.execute('CREATE TABLE todolist(id, ids, task)')
# database.commit()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_status(game=discord.Game(name="type [help for help"))


@client.event
async def on_message(message):
    try:
        channel = get_channel(message)
    except KeyError:
        servers[message.server.id] = Server(message)
        channel = get_channel(message)
    msg = message.content.split(" ")
    command = msg[0].lower()
    args = msg[1:]
    #fuckin = random.randint(1, 10)
    #if fuckin == 1:
    #    await client.send_message(message.channel, (fuck.random(name='Tom', from_='Chris').text))
    if not channel.blacklisted:
        if channel.cb:
            await cleverchat(message, client, channel.cb)

        await butty(message)

        if command == "[help":
            await buttyhelp(message)

        elif command == "[bet":
            number = random.randint(100, 5000)
            await client.send_message(message.channel, "$bet " + str(number))

        elif command == "[logs":
            await makeLogs(message)

        elif command == "[balance":
            await client.send_message(message.channel, "$balance")

        elif command == "[invite":
            reply = 'https://discordapp.com/oauth2/authorize?client_id=229223616217088001&scope=bot&permissions=60'
            await client.send_message(message.channel, reply)

        elif command == "[yt":
            if message.server.id == "204621105720328193":
                result_no = 1
                newmsg = ' '.join(msg[1:])
            else:
                try:
                    result_no = int(msg[-1])
                    del msg[-1]
                    newmsg = ' '.join(msg[1:])
                except ValueError:
                    newmsg = ' '.join(msg[1:])
                    result_no = 1
            results = youtube(newmsg, result_no)
            if results != "failed":
                await client.send_message(message.channel, "Here are the results for: " + newmsg + "\n" + results)
            else:
                await client.send_message(message.channel, "There were no results for " + newmsg)

        elif command == "[quit":
            restart(message)

        elif command == "[clean":
            try:
                limit = int(msg[1])
                await purge(message, client, message.channel, limit)
            except IndexError:
                await client.send_message(message.channel, "You need to set a limit, I can't just remove everything")

        elif command == "[duck":
            await lmddgtfy(message)

        elif command == "[flip":
            coin = random.randint(1, 2)
            if coin == 1:
                await client.send_message(message.channel, "\\*flips coin* ... Heads!")
            elif coin == 2:
                await client.send_message(message.channel, "\\*flips coin* ... Tails!")

        elif command == "[roll":
            if msg[1] == "x":
                await client.send_message(message.channel, "by 'x' I meant a number")
            if int(msg[1]) > 100000000000000000000000000000000000000000000000:
                client.send_message(message.channel, "Hmm, that's too big. Please try again.")
            else:
                try:
                    if int(msg[2]) > 10:
                        await client.send_message(message.channel, "That's too many dice")
                    else:
                        for x in range(0, int(msg[2])):
                            rollno = int(msg[1])
                            result = random.randint(1, rollno)
                            await client.send_message(message.channel,
                                                      "For die " + str(x + 1) + " you rolled: " + str(result))
                except IndexError:
                    rollno = int(msg[1])
                    result = str(random.randint(1, rollno))
                    await client.send_message(message.channel, "You rolled: " + result)

        elif command == "[todo" or command == "[t":
            if msg[1] == "add" or msg[1] == "a":
                task = ' '.join(msg[2:])
                user = message.author.id
                if task != "":
                    todoid = cursor.execute("SELECT * FROM todolist WHERE id=?", (user,))
                    todoid = len(todoid.fetchall()) + 1
                    cursor.execute("INSERT INTO todolist VALUES(?, ?, ?)", (user, todoid, task))
                    database.commit()
                    await client.send_message(message.channel, "Added **" + task + "** to your list")
                else:
                    await client.send_message(message.channel, "You tried to add nothing; I'm not gonna do it")
            elif msg[1] == "show" or msg[1] == "s":
                newlist = []
                try:
                    user = msg[2]
                    user = user.replace("<@", "")
                    user = user.replace(">", "")
                    print(user)
                    tasks = cursor.execute("SELECT task FROM todolist WHERE id=?", (user,))
                except IndexError:
                    user = message.author.id
                    print(user)
                    tasks = cursor.execute("SELECT task FROM todolist WHERE id=?", (user,))
                tasks = tasks.fetchall()
                for x in range(0, len(tasks)):
                    newlist.append(tasks[x][0])
                for x in range(0, len(newlist)):
                    newlist[x] = str(x + 1) + ": " + newlist[x] + "\n"
                await client.send_message(message.channel, "To Do:\n" + ''.join(newlist))
            elif msg[1] == "clear" or msg[1] == "c":
                user = message.author.id
                cursor.execute("DELETE FROM todolist WHERE id=?", (user,))
                database.commit()
                await client.send_message(message.channel, "Your list has been cleared")
            elif msg[1] == "remove" or msg[1] == "r":
                ids = int(msg[2])
                moveup = []
                user = message.author.id
                removed = (cursor.execute("SELECT task FROM todolist WHERE id=? AND ids=?", (user, ids))).fetchall()
                cursor.execute("DELETE FROM todolist WHERE id=? AND ids=?", (user, ids))
                newid = (cursor.execute("SELECT ids FROM todolist WHERE id=?", (user,))).fetchall()
                print(newid)
                for x in range(0, len(newid)):
                    if newid[x][0] > ids:
                        moveup.append(newid[x][0])
                for x in range(0, len(moveup)):
                    cursor.execute("UPDATE todolist SET ids=? WHERE ids=?", ((moveup[x] - 1), moveup[x]))
                database.commit()
                await client.send_message(message.channel, "Removed **" + removed[0][0] + "** from your list")

        elif command == "[chat":
            if msg[1] == "start":
                channel.cb = Cleverbot()
            elif msg[1] == "stop":
                channel.cb = False

        elif command == "[voice" or command == "[v":
            server = servers[message.server.id]
            voice = server.voice
            if msg[1] == "join" or msg[1] == "j":
                voice_channel = 0
                if voice:
                    await client.send_message(message.channel, "You're already in a voice channel")
                else:
                    if len(args) == 2:
                        if len(args[2]) == 18:
                            voice_channel = client.get_channel(str(msg[2]))
                        else:
                            await client.send_message(message.channel, "That's not a valid voice channel id")
                    else:
                        for x in message.server.channels:
                            if str(x.type) == 'voice' and x.position == 0:
                                voice_channel = x
                        if not voice_channel:
                            await client.send_message(message.channel, "No voice channels could be found. Does butty have the required perms?")
                    # discord.opus.load_opus("/usr/lib/x86_64-linux-gnu/libopus.so")
                    #discord.opus.load_opus("extras/opus.dll")
                    discord.opus.load_opus("extras/opus.so")
                    if not voice_channel:
                        return None
                    voice = await client.join_voice_channel(voice_channel)
                    server.voice = voice

            elif msg[1] == "leave" or msg[1] == "l":
                if voice:
                    try:
                        server.player.stop()
                    except AttributeError:
                        pass
                    await server.voice.disconnect()
                    server.voice = False
                else:
                    await client.send_message(message.channel, "You aren't connected to a voice channel")
            elif msg[1] == "play" or msg[1] == "p":
                if server.voice:
                    if server.player and server.player.is_playing():
                        await client.send_message(message.channel, "You're already playing something")
                    else:
                        res = str(' '.join(msg[2:]))
                        result = youtube(res)
                        server.player = await server.voice.create_ytdl_player(result)
                        server.player.start()
                        await client.send_message(message.channel, "Now playing: `" + res + "`")
                else:
                    await client.send_message(message.channel, "You haven't joined a voice channel")

            elif msg[1] == "stop" or msg[1] == "s":
                if server.player:
                    server.player.stop()
                else:
                    await client.send_message(message.channel, "You aren't playing anything")

        elif command == "[stats":
            await client.send_message(message.channel, "I am currently being a sandwich in " + str(len(client.servers)) + " servers")

        elif command == "[anagram":
            mode = random.randint(1,2)
            if mode == 1:
                await anagram(words, words_sorted, client, message, "stalin")
            else:
                await anagram(words, words_sorted, client, message, "notstalin")

        elif command == '[test':
            pass

    if command == "[togglecommands" and is_admin(message):
        channel.toogle_blacklist()



try:
    with open("extras/token", 'r') as Token:
        token = Token.read()
        client.run(token)
except:
    print("token not found\nplease create a file called \"token\" in the \"extras\" folder and put the token in that")
    input()
