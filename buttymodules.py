import urllib.request
import urllib.parse
import urllib
import os
import time
import sys
import re
import random
import math
import itertools
#from cleverbot import Cleverbot
#import threading
#import asyncio
#from bs4 import BeautifulSoup
#import discord


def is_admin(message):
    member = message.server.get_member(message.author.id)
    if message.channel.permissions_for(member).administrator:
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


def restart(message):
    if message.author.id == "135496683009081345" or message.author.id == '135483608491229184':
        os.system("cd extras && rm buttybot.db && cd ../ && git pull && python3 butty.py")


def youtube(search, result_number=1):
    results = []
    query_string = urllib.parse.urlencode({"search_query": search})
    html_content = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)
    search_results = re.findall(r'href=\"/watch\?v=(.{11})', html_content.read().decode())
    resultno = result_number * 2
    try:
        for x in range(0, resultno):
            if x % 2 == 0:
                results.append("https://www.youtube.com/watch?v=" + search_results[x] + "\n")
        return ''.join(results)
    except IndexError:
        return "failed"


async def cleverchat(message, client, cb):
    if message.author.bot:
        pass
    elif should_remove(message):
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


async def anagram(words, words_sorted, client, message, mode):
    if mode == 1:
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
                        if not before in lis:
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
                reply = "I can't do **%s**. Sorry about that." % word
                continue
            await client.send_message(message.channel, reply)
            print(word, "-->", reply, time.clock() - start)
            break
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
