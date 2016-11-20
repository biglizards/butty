import sqlite3
import time
import datetime
import asyncio
import discord
from discord.ext import commands
import tempfile


# print(time.mktime(message.timestamp.timetuple()))


class Logs:
    def __init__(self, bot):
        self.bot = bot

        self.database = sqlite3.connect("cogs/messages.db")
        self.c = self.database.cursor()

        #self.c.execute('DROP TABLE IF EXISTS messages')
        self.c.execute('''CREATE TABLE IF NOT EXISTS messages
                          (id INTEGER UNIQUE ON CONFLICT IGNORE, timestamp INTEGER, author INTEGER, channel INTEGER,
                          server INTEGER, content TEXT, attachments TEXT, authorName TEXT)''')

    async def test(self):
        '''
        start_time = time.time()
        self.c.execute('select * from messages').fetchall()
        print("--- {} seconds --- select *".format(time.time() - start_time))

        start_time = time.time()
        self.c.execute('select * from messages where server=? ORDER BY id DESC LIMIT 1', (204621105720328193,)).fetchall()
        print("--- {} seconds --- select * rpi ORDER BY id DESC LIMIT 1".format(time.time() - start_time))
        '''

        start_time = time.time()
        logs = []
        data_list = self.c.execute('select premade from messages where server=?', (204621105720328193,)).fetchall()
        for data in data_list:
            logs.append(data)
        print("--- {} seconds --- build logs this thing".format(time.time() - start_time))

    @commands.command(name="logs", aliases=['getlogs'], pass_context=True)
    async def logs_getlogs(self, context):
        start_time = time.time()

        real_message = context.message

        last_message_in_logs = self.c.execute('select id from messages where server=? ORDER BY id DESC LIMIT 1',
                                              (real_message.server.id,)).fetchone()
        log_list = []
        async for message in self.bot.logs_from(real_message.channel, limit=999999999999999):
            if last_message_in_logs and int(message.id) <= last_message_in_logs[0]:
                break

            log_list.append((message.id, time.mktime(message.timestamp.timetuple()), message.author.id,
                             message.channel.id, message.server.id, message.content,
                             ' '.join([x['url'] for x in message.attachments]), message.author.name))

        self.c.executemany('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)', log_list)
        self.database.commit()

        print("--- {} seconds --- build logs".format(time.time() - start_time))
        start_time = time.time()

        response = b''

        data_list = self.c.execute('select timestamp, content, attachments, authorName from messages where channel=? '
                                   'ORDER BY id ASC', (real_message.channel.id,)).fetchall()
        for data in data_list:
            start = "{} {}: ".format(datetime.datetime.fromtimestamp(data[0]).strftime('%Y-%m-%d %H:%M:%S'),
                                     data[3])
            indent = " " * len(start)

            content = ''
            if data[1]:
                content += data[1].replace('\n', '\r\n' + indent) + "\r\n"
            if data[2]:
                if data[1]:
                    content += indent
                content += data[2].replace(' ', '\r\n' + indent) + "\r\n"

            response += (start + content).encode()

        file = tempfile.SpooledTemporaryFile(mode='rb+')
        file.write(response)
        file.seek(0)

        filename = real_message.channel.name + ".log.txt"
        if 'bam' in real_message.content:
            await self.bot.send_file(discord.Object('249845334350495744'), file._file, filename=filename, content="here're the results")
        else:
            await self.bot.send_file(real_message.channel, file._file, filename=filename, content="here're the results")

        print("--- {} seconds --- send logs".format(time.time() - start_time))



def setup(bot):
    bot.add_cog(Logs(bot))
