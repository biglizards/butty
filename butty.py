#!/usr/bin/env python
import asyncio
import logging
import os
import sqlite3
from datetime import datetime
import random
import math
import itertools

import discord
import parsedatetime.parsedatetime
from cleverbot import Cleverbot
from dateutil.relativedelta import relativedelta
from pytz import timezone

from buttymodules import *

# to do list:
# oh god the text is highlighted what
# repeated + deleting alerts
# finish game
# update the help section
# fix code

real_path = os.path.dirname(os.path.realpath(__file__)) + "/"
os.chdir(real_path)

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='extras/metalogs/discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

valid_commands = ['help', 'bet', 'balance', 'invite', 'yt', 'voice', 'v', 'duck', 'flip', 'roll', 'todo', 't', 'gt',
                  'chat', 'foo', 'logs', 'find', 'restart', 'purge', 'clean', 'say', 'bug', 'stats',
                  'stats_secret', 'anagram', 'remindme', 'reminders']


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
    await client.change_presence(game=discord.Game(name="[help for help [bug for bug reports | harru.club"))
    await timecheck()
    # with open("butty.png", "rb") as file:
    # await client.edit_profile(avatar=file.read())
    # this changes the avatar


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.server.id not in servers:
        servers[message.server.id] = Server(message)
    server = servers[message.server.id]
    if message.channel.id not in server.channels:
        server.channels[message.channel.id] = Channel(message)
    channel = server.channels[message.channel.id]

    msg = message.content.split(" ")
    command = msg[0].lower()[1:]
    args = msg[1:]

    if not channel.blacklisted:
        # react to non-command messages.
        if channel.cb:
            await cleverchat(message, client, channel.cb)
        await butty(message)

        if message.content[0] == '[' and command in valid_commands:
            command = eval(command)
            await command(message, args)

    if msg[0] == "[togglecommands" and is_admin(message):
        blacklisted = channel.toogle_blacklist()
        if blacklisted:
            await client.send_message(message.channel, "Commands Disabled")
        else:
            await client.send_message(message.channel, "Commands enabled")


async def reminders(message, args):
    reminder_list = cursor.execute("SELECT message FROM alert WHERE user=?", (message.author.id,)).fetchall()
    x = 0
    reply = ''
    for reminder in reminder_list:
        x += 1
        reply += str(x) + ": " + reminder[0] + "\n"
    await client.send_message(message.channel, "<@" + message.author.id + ">'s reminders:\n" + reply)


async def chat(message, args):
    server = servers[message.server.id]
    channel = server.channels[message.channel.id]
    if args[0] == "start":
        channel.cb = Cleverbot()
    elif args[0] == "stop":
        channel.cb = False


async def anagram(message, args):
    await client.send_message(message.channel, "final check")
    while True:
        word = random.choice(words)
        print(word)
        # word = "scuttles"
        # word = input().strip(",.!?'" + '"( )').lower().replace(" ", "").replace("'", "")
        letters = sorted(word)
        # print(word)
        matches = []
        start = time.clock()
        if words_sorted.count(letters) > 1:
            for x in words:
                if letters == sorted(x) and word != x:
                    matches.append(x)
        if matches:
            print(matches)
            continue
        else:
            # print("generating, please wait")
            length = len(letters)
            before_matches = []
            after_matches = []
            end = 0
            for space in range(1, math.ceil((length + 1) / 2)):
                # print(space, "out of", math.ceil((length+1)/2)-1)
                if end:
                    break
                lis = []
                for bs in itertools.combinations(letters, space):
                    before = sorted(bs)
                    if before not in lis:
                        lis.append(before)  # get every unique combination
                    else:
                        continue
                    after = letters[:]  # this is dumb
                    for x in before:
                        after.remove(x)
                    if not sorted(after + before) == letters:
                        print("ERROR: sorted(after + before) == letters FAILED")
                    if not (after in words_sorted and before in words_sorted):
                        continue  # at least one of them is not a valid word

                    # ok we've got the words now, so we _could_ stop here
                    # but i won't, because obviously we need additional complexity

                    after_indexes = [i for i, x in enumerate(words_sorted) if x == after]
                    before_indexes = [i for i, x in enumerate(words_sorted) if x == before]
                    temp_before_matches = []
                    temp_after_matches = []
                    for x in after_indexes:
                        temp_after_matches.append(words[x])
                    for x in before_indexes:
                        temp_before_matches.append(words[x])
                    if time.clock() - start > 5 and after_matches and before_matches:
                        print("going home early")
                        end = True
                        break
                        # pass
                    if temp_before_matches or temp_after_matches:
                        before_matches.append(temp_before_matches)
                        after_matches.append(temp_after_matches)
        try:
            for x in range(len(before_matches)):
                if sorted("".join(before_matches[x][0]) + "".join(after_matches[x][0])) != letters:
                    print("".join(before_matches[x][0]), "".join(after_matches[x][0]), letters)
                    # reply += str(before_matches[x]) + " " + str(after_matches[x]) + "\n"
        except UnboundLocalError:
            pass
        try:
            choice = random.randrange(int(len(before_matches) / 2))
            reply = random.choice(before_matches[choice]) + " " + random.choice(
                after_matches[choice])  # + "   (%i others)" % len(before_matches)
            # word + " --> " +
            if not sorted(reply.replace(" ", "")) == letters:
                reply = "ERROR ERROR SOMETHING WENT WRONG"
        except:
            continue
        await client.send_message(message.channel, reply)
        print(word, "-->", reply, time.clock() - start)
        break
    '''
    else:
        word = random.choice(words)
        print(word)
        letters = []
        for letter in word:
            letters.append(letter)
        anagramy = []
        for x in range(0, len(letters)):
            y = random.randint(0, len(letters) - 1)
            anagramy.append(letters[y])
            del letters[y]
            anagram = ''.join(anagramy)
        await client.send_message(message.channel, anagram)
        '''


async def stats(message, args):
    total = 0
    for server in client.servers:
        total += len(server.members)
    await client.send_message(message.channel, ("I am currently being a sandwich in " + str(len(client.servers))
                                                + " servers, feeding " + str(total) + " users"))


async def stats_secret(message, args):
    if not is_admin(message):
        return
    reply = ""
    for server in client.servers:
        try:
            reply += "**%s:**" % server.name + " `" + str(await client.create_invite(server)).replace("/", "/ ") + "`\n"
        except discord.HTTPException:
            reply += "**%s:**" % server.name + " `" + "[no perms]" + "`\n"
    await client.send_message(message.channel, reply)


async def voice(message, args):
    server = servers[message.server.id]
    voice = server.voice
    if args[0] == "join" or args[0] == "j":
        voice_channel = 0
        if voice:
            await client.send_message(message.channel, "You're already in a voice channel")
        else:
            if len(args) == 2:
                if len(args[1]) == 18:
                    voice_channel = client.get_channel(str(args[1]))
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
                        await client.send_message(message.channel, ("No voice channels could be found. "
                                                                    "Does butty have the required perms?"))
            # discord.opus.load_opus("extras/opus.dll")
            discord.opus.load_opus("extras/opus.so")
            if not voice_channel:
                return None
            voice = await client.join_voice_channel(voice_channel)
            server.voice = voice

    elif args[0] == "leave" or args[0] == "l":
        if voice:
            try:
                server.player.stop()
            except AttributeError:
                pass
            await server.voice.disconnect()
            server.voice = False
        else:
            await client.send_message(message.channel, "You aren't connected to a voice channel\nhint do [v j")
    elif args[0] == "play" or args[0] == "p":
        if server.searching:
            await client.send_message(message.channel, "You're already playing something")
        else:
            if server.voice:
                server.searching = True
                if server.player and server.player.is_playing():
                    await client.send_message(message.channel, "You're already playing something")
                    server.searching = False
                else:
                    res = str(' '.join(args[1:]))
                    result = youtube(res)
                    server.player = await server.voice.create_ytdl_player(result)
                    server.player.start()
                    server.searching = False
                    await client.send_message(message.channel, "Now playing: `" + server.player.title + "`")
            else:
                await client.send_message(message.channel, "You haven't joined a voice channel\nhint do [v j")

    elif args[0] == "stop" or args[0] == "s":
        if server.player:
            server.player.stop()
            server.searching = False
        else:
            await client.send_message(message.channel, "You aren't playing anything")


async def bug(message, args):
    if is_admin(message):
        bug_channel = client.get_channel("233699709846290432")
        await client.send_message(bug_channel,
                                  "**" + str(message.server) + "**: " + message.server.id + "\n**" + str(
                                      message.author) + "**: " + message.author.id + "\n" + ' '.join(args[0:]))
        await client.send_message(message.channel, "Bug report sent, thank you")
    else:
        await client.send_message(message.channel, ("Please report the bug to a Server Admin so they can report it,"
                                                    "just so this doesn't get spammed"))


async def v(message, args):
    await voice(message, args)


async def say(message, args):
    await client.send_message(message.channel, ' '.join(args[0:]))


async def todo(message, args):
    if args[0] == "add" or args[0] == "a":
        task = ' '.join(args[1:])
        user = message.author.id
        if task != "":
            todoid = cursor.execute("SELECT * FROM todolist WHERE id=?", (user,))
            todoid = len(todoid.fetchall()) + 1
            cursor.execute("INSERT INTO todolist VALUES(?, ?, ?)", (user, todoid, task))
            database.commit()
            await client.send_message(message.channel, "Added **" + task + "** to your list")
        else:
            await client.send_message(message.channel, "You tried to add nothing; I'm not gonna do it")
    elif args[0] == "show" or args[0] == "s":
        newlist = []
        try:
            user = args[1]
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
    elif args[0] == "clear" or args[0] == "c":
        user = message.author.id
        cursor.execute("DELETE FROM todolist WHERE id=?", (user,))
        database.commit()
        await client.send_message(message.channel, "Your list has been cleared")
    elif args[0] == "remove" or args[0] == "r":
        ids = int(args[1])
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


async def t(message, args):
    await todo(message, args)


async def gt(message, args):
    if args[0] == "add" or args[0] == "a":
        if is_admin(message):
            task = ' '.join(args[1:])
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
    elif args[0] == "show" or args[0] == "s":
        newlist = []
        try:
            user = args[1]
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
    elif args[0] == "clear" or args[0] == "c":
        if is_admin(message):
            user = message.server.id
            cursor.execute("DELETE FROM todolistserver WHERE id=?", (user,))
            database.commit()
            await client.send_message(message.channel, "The Guild list has been cleared")
        else:
            await client.send_message(message.channel, "You don't have permission to edit the Guild's list")
    elif args[0] == "remove" or args[0] == "r":
        if is_admin(message):
            ids = int(args[1])
            moveup = []
            user = message.server.id
            removed = (
                cursor.execute("SELECT task FROM todolistserver WHERE id=? AND ids=?", (user, ids))).fetchall()
            cursor.execute("DELETE FROM todolistserver WHERE id=? AND ids=?", (user, ids))
            newid = (cursor.execute("SELECT ids FROM todolistserver WHERE id=?", (user,))).fetchall()
            for x in range(0, len(newid)):
                if newid[x][0] > ids:
                    moveup.append(newid[x][0])
            for x in range(0, len(moveup)):
                cursor.execute("UPDATE todolistserver SET ids=? WHERE ids=?", ((moveup[x] - 1), moveup[x]))
            database.commit()
            await client.send_message(message.channel,
                                      "Removed **" + removed[0][0] + "** from the Guild's list")
        else:
            await client.send_message(message.channel, "You don't have permission to edit the Guild's list")


async def roll(message, args):
    try:
        no_of_sides = int(args[0])
        no_of_dice = int(args[1])
    except IndexError:
        no_of_dice = 1
    except ValueError:
        await client.send_message(message.channel, "by 'x' I meant a number")
        return
    if no_of_sides > 100000000000000000000000000000000000000000000000:
        client.send_message(message.channel, "Hmm, that's too big. Please try again.")
        return
    if no_of_dice > 10:
        await client.send_message(message.channel, "That's too many dice")
        return
    reply = "RESULTS:\n"
    for x in range(0, no_of_dice):
        result = random.randint(1, no_of_sides)
        reply += "For die %i you rolled: %i\n" % (x + 1, result)
    await client.send_message(message.channel, reply)


async def flip(message, args):
    coin_state = random.choice(['Heads', 'Tails'])
    await client.send_message(message.channel, "\\*flips coin* ... %s!" % coin_state)


async def clean(message, args):
    await purge(message, args)


async def purge(message, args):
    if is_admin(message):
        if not args:
            await client.send_message(message.channel, "You need to set a limit, I can't just remove everything")
            return
        limit = int(args[0])
        if limit > 200:
            await client.send_message(message.channel, "That's too many, calm down")
        else:
            await client.purge_from(message.channel, limit=limit, check=should_remove)


async def yt(message, args):
    if message.server.id == "204621105720328193":
        result_no = 1
        newmsg = ' '.join(args)
    else:
        try:
            result_no = int(args[-1])
            del args[-1]
            newmsg = ' '.join(args)
        except ValueError:
            newmsg = ' '.join(args)
            result_no = 1
    results = youtube(newmsg, result_no)
    if results != "failed":
        await client.send_message(message.channel, "Here are the results for: " + newmsg + "\n" + results)
    else:
        await client.send_message(message.channel, "There were no results for " + newmsg)


async def invite(message, args):
    reply = 'https://harru.club/invite'
    await client.send_message(message.channel, reply)


async def bet(message, args):
    number = random.randint(100, 5000)
    await client.send_message(message.channel, "$bet " + str(number))


async def balance(message, args):
    await client.send_message(message.channel, "$balance")


async def help(message, args):
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


async def logs(message, search="", send=True):
    logs_list = []
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
            logs_list.append(tolog)
    if not foundit and line:
        await client.send_message(message.channel,
                                  'something went wrong: last message not found\nsomeone probably deleted it')
    file = open(filename, mode="a", encoding='utf-8')
    for message2 in reversed(logs_list):
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
                        + "/"
                        + search
                        + ".search")
        with open(filename, "w", encoding='utf-8') as file:
            for result in results:
                file.write(result + "\n")
        await client.send_file(message.channel, filename, content="here're the results")


async def find(message, args):
    await logs(message, search=' '.join(args), send=False)


async def remindme(message, args):
    msg = message.content.split(",", 1)
    repeat = "no"
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


async def butty(message):
    if message.author.id != "229223616217088001" and "butty" in message.content:
        await client.send_message(message.channel, "yes")


async def duck(message, args):
    query = urllib.parse.quote(' '.join(args[0:]))
    result = "http://lmddgtfy.net/?q=" + query
    await client.send_message(message.channel, result)



try:
    with open("extras/token", 'r') as Token:
        token = Token.read()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.start(token))
        loop.close()
except FileNotFoundError:
    print("token not found\nplease create a file called \"token\" in the \"extras\" folder and put the token in that")
    input()
