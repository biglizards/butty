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
import logging
# import sys
# import re
# import threading
import parsedatetime.parsedatetime
from pytz import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta
import asyncio


# to do list:
# oh god the text is highlighted what
# repeated + deleting alerts
# finish anagram game
# update the help section


logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename='extras/discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


class Server:
    def __init__(self, message):
        self.id = message.server.id
        self.channels = {message.channel.id: Channel(message)}
        self.voice = False
        self.player = False
        self.searching = False


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
        else:
            cursor.execute("DELETE FROM blacklist WHERE channelid=?", (self.id,))
            database.commit()
        self.check_blacklist()
        return self.blacklisted


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


async def makeLogs(message, search="", send=True):
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
        results = []
        with open(filename, "r", encoding='utf-8') as file:
            for line in file:
                if search in line:
                    results.append(line)
        filename = ("extras/" + message.server.name
                        + search
                        + ".search")
        with open(filename, "w", encoding='utf-8') as file:
            for result in results:
                file.write(result + "\n")
        await client.send_file(message.channel, filename, content="here're the results")


async def future(message, repeat):
    msg = message.content.split(",", 1)
    cal = parsedatetime.Calendar()
    time = datetime.now(timezone('UTC'))
    currenttime = cal.parse(str(time))[0]
    newtime = cal.parse(msg[0], currenttime)[0]
    list = []
    alertid = len(cursor.execute("SELECT * FROM alert WHERE user=?", (message.author.id,)).fetchall()) + 1
    for x in range(0, len(currenttime)):
        if newtime[x] - currenttime[x] == 0:
            list.append(0)
        else:
            list.append(newtime[x] - currenttime[x])
    for x in range(0, len(list)):
        if x == 0:
            time += relativedelta(years=list[x])
        if x == 1:
            time += relativedelta(months=list[x])
        if x == 2:
            time += relativedelta(days=list[x])
        if x == 3:
            time += relativedelta(hours=list[x])
        if x == 4:
            time += relativedelta(minutes=list[x])
        else:
            pass
    time = str(time)[:-16]
    cursor.execute("INSERT INTO alert VALUES(?, ?, ?, ?, ?, ?)", (message.author.id, message.channel.id, time, msg[1], repeat, alertid))
    database.commit()
    await client.send_message(message.channel, "Reminder set for " +  time + " UTC")


async def timecheck():
    now = str(datetime.now(timezone('UTC')))[:-16]
    alerts = cursor.execute("SELECT message FROM alert WHERE time=?", (now,)).fetchall()
    users = cursor.execute("SELECT user FROM alert WHERE time=?", (now,)).fetchall()
    channels = cursor.execute("SELECT channel FROM alert WHERE time=?", (now,)).fetchall()
    if len(alerts) != 0:
        for x in range(0, len(alerts)):
            channel = client.get_channel(channels[x][0])
            await client.send_message(channel, "<@" + users[x][0] + "> " + alerts[x][0])
            cursor.execute("DELETE FROM alert WHERE time=?", (now,))
            database.commit()
    else:
        pass
    await asyncio.sleep(59)
    await timecheck()


async def fuckin(message):
    fuckin = random.randint(1, 500)
    if fuckin == 1:
        users1 = []
        users = message.server.members
        for user in users:
            users1.append(user)
        user1, user2 = random.choice(users1).name, random.choice(users1).name
        await client.send_message(message.channel, (fuck.random(name=user1, from_=user2).text))


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
# print(cursor.execute("select * from sqlite_master where type='table'").fetchall())
# cursor.execute('CREATE TABLE alert(user, channel, time, message, repeat)')
# cursor.execute('ALTER TABLE alert ADD COLUMN id')
# database.commit()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(game=discord.Game(name="[help for help | harru.club"))
    await timecheck()
    #with open("butty.png", "rb") as file:
        #await client.edit_profile(avatar=file.read())
        #this changes the avatar


@client.event
async def on_message(message):
    try:
        server = servers[message.server.id]
    except KeyError:
        servers[message.server.id] = Server(message)
        server = servers[message.server.id]
    try:
        channel = server.channels[message.channel.id]
    except KeyError:
        server.channels[message.channel.id] = Channel(message)
        channel = server.channels[message.channel.id]
    msg = message.content.split(" ")
    command = msg[0].lower()
    args = msg[1:]
    if not channel.blacklisted:
        if channel.cb:
            await cleverchat(message, client, channel.cb)

        await fuckin(message)

        await butty(message)

        if command == "[help":
            await buttyhelp(message)

        elif command == "[getlogs":
            if message.author.id == "135483608491229184" or message.author.id == "135496683009081345":
                await client.send_file(message.channel, "extras/discord.log")

        elif command == "[bet":
            number = random.randint(100, 5000)
            await client.send_message(message.channel, "$bet " + str(number))

        elif command == "[logs":
            await makeLogs(message)

        elif command == "[find":
            await makeLogs(message, search=' '.join(args), send=False)

        elif command == "[balance":
            await client.send_message(message.channel, "$balance")

        elif command == "[invite":
            reply = 'https://harru.club/invite'
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

        elif command == "[getout.avi":
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
                    user1 = user.replace("<@", "")
                    user1 = user1.replace(">", "")
                    tasks = cursor.execute("SELECT task FROM todolist WHERE id=?", (user1,))
                except IndexError:
                    user = "<@" + message.author.id + ">"
                    user1 = message.author.id
                    tasks = cursor.execute("SELECT task FROM todolist WHERE id=?", (user1,))
                tasks = tasks.fetchall()
                for x in range(0, len(tasks)):
                    newlist.append(tasks[x][0])
                for x in range(0, len(newlist)):
                    newlist[x] = str(x + 1) + ": " + newlist[x] + "\n"
                await client.send_message(message.channel, "To Do list for " + user + ":\n" + ''.join(newlist))
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
                for x in range(0, len(newid)):
                    if newid[x][0] > ids:
                        moveup.append(newid[x][0])
                for x in range(0, len(moveup)):
                    cursor.execute("UPDATE todolist SET ids=? WHERE ids=?", ((moveup[x] - 1), moveup[x]))
                database.commit()
                await client.send_message(message.channel, "Removed **" + removed[0][0] + "** from your list")

        elif command == "[gtodo" or command == "[gt":
            if msg[1] == "add" or msg[1] == "a":
                if is_admin(message):
                    task = ' '.join(msg[2:])
                    servertodo = message.server.id
                    if task != "":
                        todoid = cursor.execute("SELECT * FROM todolistserver WHERE id=?", (servertodo,))
                        todoid = len(todoid.fetchall()) + 1
                        cursor.execute("INSERT INTO todolistserver VALUES(?, ?, ?)", (servertodo, todoid, task))
                        database.commit()
                        await client.send_message(message.channel, "Added **" + task + "** to your list")
                    else:
                        await client.send_message(message.channel, "You tried to add nothing; I'm not gonna do it")
                else:
                    await client.send_message(message.channel, "You don't have permission to edit the Guild's list")
            elif msg[1] == "show" or msg[1] == "s":
                newlist = []
                try:
                    user = msg[2]
                    user = user.replace("<@", "")
                    user = user.replace(">", "")
                    tasks = cursor.execute("SELECT task FROM todolistserver WHERE id=?", (user,))
                except IndexError:
                    user = message.server.id
                    tasks = cursor.execute("SELECT task FROM todolistserver WHERE id=?", (user,))
                tasks = tasks.fetchall()
                for x in range(0, len(tasks)):
                    newlist.append(tasks[x][0])
                for x in range(0, len(newlist)):
                    newlist[x] = str(x + 1) + ": " + newlist[x] + "\n"
                await client.send_message(message.channel, "Guild To Do:\n" + ''.join(newlist))
            elif msg[1] == "clear" or msg[1] == "c":
                if is_admin(message):
                    user = message.server.id
                    cursor.execute("DELETE FROM todolistserver WHERE id=?", (user,))
                    database.commit()
                    await client.send_message(message.channel, "The Guild list has been cleared")
                else:
                    await client.send_message(message.channel, "You don't have permission to edit the Guild's list")
            elif msg[1] == "remove" or msg[1] == "r":
                if is_admin(message):
                    ids = int(msg[2])
                    moveup = []
                    user = message.server.id
                    removed = (cursor.execute("SELECT task FROM todolistserver WHERE id=? AND ids=?", (user, ids))).fetchall()
                    cursor.execute("DELETE FROM todolistserver WHERE id=? AND ids=?", (user, ids))
                    newid = (cursor.execute("SELECT ids FROM todolistserver WHERE id=?", (user,))).fetchall()
                    for x in range(0, len(newid)):
                        if newid[x][0] > ids:
                            moveup.append(newid[x][0])
                    for x in range(0, len(moveup)):
                        cursor.execute("UPDATE todolistserver SET ids=? WHERE ids=?", ((moveup[x] - 1), moveup[x]))
                    database.commit()
                    await client.send_message(message.channel, "Removed **" + removed[0][0] + "** from the Guild's list")
                else:
                    await client.send_message(message.channel, "You don't have permission to edit the Guild's list")

        elif command == "[chat":
            if msg[1] == "start":
                channel.cb = Cleverbot()
            elif msg[1] == "stop":
                channel.cb = False

        elif command == "[say":
            await client.send_message(message.channel, ' '.join(msg[1:]))
                
        elif command == "[voice" or command == "[v":
            server = servers[message.server.id]
            voice = server.voice
            if msg[1] == "join" or msg[1] == "j":
                voice_channel = 0
                if voice:
                    await client.send_message(message.channel, "You're already in a voice channel")
                else:
                    if len(args) == 2:
                        if len(args[1]) == 18:
                            voice_channel = client.get_channel(str(msg[2]))
                        else:
                            await client.send_message(message.channel, "That's not a valid voice channel id")
                    else:
                        try:
                            userchan = message.server.get_member(message.author.id).voice.voice_channel.id
                            voice_channel = client.get_channel(userchan)
                        except AttributeError:
                                for x in message.server.channels:
                                    if str(x.type) == 'voice' and x.position == 0:
                                        voice_channel = x
                                if not voice_channel:
                                    await client.send_message(message.channel, "No voice channels could be found. Does butty have the required perms?")
                    # discord.opus.load_opus("extras/opus.dll")
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
                if server.searching:
                    await client.send_message(message.channel, "You're already playing something")
                else:
                    if server.voice:
                        server.searching = True
                        if server.player and server.player.is_playing():
                            await client.send_message(message.channel, "You're already playing something")
                            server.searching = False
                        else:
                            res = str(' '.join(msg[2:]))
                            result = youtube(res)
                            server.player = await server.voice.create_ytdl_player(result)
                            server.player.start()
                            server.searching = False
                            await client.send_message(message.channel, "Now playing: `" + res + "`")
                    else:
                        await client.send_message(message.channel, "You haven't joined a voice channel")

            elif msg[1] == "stop" or msg[1] == "s":
                if server.player:
                    server.player.stop()
                    server.searching = False
                else:
                    await client.send_message(message.channel, "You aren't playing anything")

        elif command == "[stats":
            await client.send_message(message.channel, "I am currently being a sandwich in " + str(len(client.servers)) + " servers")

        elif command == "[anagram":
            mode = random.randint(1,2)
            await anagram(words, words_sorted, client, message, mode)

        elif command == '[remindme':
            await future(message, "no")
        elif command == "[showreminders":
            list = []
            reminders = cursor.execute("SELECT message FROM alert WHERE user=?", (message.author.id,)).fetchall()
            for x in range(0, len(reminders)):
                list.append(reminders[x][0])
            for x in range(0, len(list)):
                list[x] = str(x + 1) + ": " + list[x] + "\n"
            await client.send_message(message.channel, "<@" + message.author.id + ">'s reminders:\n" + ''.join(list))

    if command == "[togglecommands" and is_admin(message):
        blacklisted = channel.toogle_blacklist()
        if blacklisted:
            await client.send_message(message.channel, "Commands Disabled")
        else:
            await client.send_message(message.channel, "Commands enabled")



try:
    with open("extras/token", 'r') as Token:
        token = Token.read()
        client.run(token)
except FileNotFoundError:
    print("token not found\nplease create a file called \"token\" in the \"extras\" folder and put the token in that")
    input()
