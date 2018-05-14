import sqlite3
import discord
from discord.ext import commands
import shutil
import gzip
import os

class Logs:
    def __init__(self, bot):
        self.bot = bot

        self.database = sqlite3.connect("cogs/messages.db")
        self.c = self.database.cursor()

        self.c.execute('''CREATE TABLE IF NOT EXISTS messages
                          (id INTEGER UNIQUE ON CONFLICT IGNORE, timestamp TEXT, authorid INTEGER, channelid INTEGER,
                          serverid INTEGER, content TEXT, attachments TEXT, authorName TEXT)''')

    @commands.command(name="logs")
    async def get_logs(self, ctx):
        last_message_id = self.c.execute('select id from messages where channelid=? ORDER BY id DESC LIMIT 1',
                                         (ctx.channel.id,)).fetchone()
        try:
            last_message = await ctx.get_message(last_message_id[0]) if last_message_id else None
        except discord.errors.NotFound:
            last_message = None
            print("ohno")
        logs = []
        async for message in ctx.channel.history(limit=None,
                                                 after=last_message):
            logs.append((message.id, message.created_at.strftime("%Y-%m-%d %H:%M"), message.author.id,
                         message.channel.id, message.guild.id, message.content.encode(),
                         ', '.join([x.url for x in message.attachments]), message.author.name))
            print(message.id)
            if last_message_id and message.id < last_message_id[0]:
                break
        self.c.executemany('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)', logs)
        self.database.commit()
        print("got thing")
        return

        data_list = self.c.execute('select timestamp, content, attachments, authorName from messages where channelid=? '
                                   'ORDER BY id ASC', (ctx.channel.id,)).fetchall()
        print("fetchedall")
        file = open("extras/logs.txt", "w", encoding="utf-8")
        for timestamp, content, attachments, author in data_list:
            message = []
            message.append("{} - {}: ".format(timestamp, author))
            if content:
                message.append(content.decode())
            if attachments:
                message.append("\nAttachments: {}".format(attachments))
            message.append("\n")
            file.write("".join(message))
        file.close()
        print("gonna send it")
        try:
            await ctx.send("here", file=discord.File("extras/logs.txt", filename="logs.txt"))
            os.remove('extras/logs.txt')
        except discord.errors.HTTPException:
            with open('extras/logs.txt', 'rb') as f_in:
                with gzip.open('extras/logs.txt.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            await ctx.send("here", file=discord.File("extras/logs.txt.gz", filename="logs.txt.gz"))
#            os.remove('extras/logs.txt')
#            os.remove('extras/logs.txt.gz')

#     @commands.command(name="logs", aliases=['getlogs', 'etest'], pass_context=True)
#     async def logs_getlogs(self, context):
#         start_time = time.time()
#
#         real_message = context.message
#
#         last_message_in_logs = self.c.execute('select timestamp from messages where server=? ORDER BY id DESC LIMIT 1',
#                                               (real_message.server.id,)).fetchone()
#         print(last_message_in_logs)
#         log_list = []
#         async for message in self.bot.logs_from(real_message.channel, limit=999999999999999):
#             if last_message_in_logs and time.mktime(message.timestamp.timetuple()) <= last_message_in_logs[0]:
#                 break
#
#             log_list.append((message.id, time.mktime(message.timestamp.timetuple()), message.author.id,
#                              message.channel.id, message.server.id, message.content.encode(),
#                              b' '.join([x['url'].encode() for x in message.attachments]), message.author.name))
#
#         self.c.executemany('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)', log_list)
#         self.database.commit()
#
#         print("--- {} seconds --- build logs".format(time.time() - start_time))
#         start_time = time.time()
#
#         response = b''
#
#         data_list = self.c.execute('select timestamp, content, attachments, authorName from messages where channel=? '
#                                    'ORDER BY id ASC', (real_message.channel.id,)).fetchall()
#         for data in data_list:
#             start = "{} {}: ".format(datetime.datetime.fromtimestamp(data[0]).strftime('%Y-%m-%d %H:%M:%S'),
#                                      data[3])
#             indent = b" " * len(start)
#
#             content = b''
#             if data[1]:
#                 content += data[1].replace(b'\n', b'\r\n' + indent) + b"\r\n"
#             if data[2]:
#                 if data[1]:
#                     content += indent
#                 content += data[2].replace(b' ', b'\r\n' + indent) + b"\r\n"
#
#             response += start.encode() + content
#
#         file = tempfile.SpooledTemporaryFile(mode='rb+')
#         file.write(response)
#         file.seek(0)
#
#         filename = real_message.channel.name + ".log.txt"
#         if 'bam' in real_message.content:
#             await self.bot.send_file(discord.Object('249845334350495744'), file._file, filename=filename, content="here're the results")
#         else:
#             await self.bot.send_file(real_message.channel, file._file, filename=filename, content="here're the results")
#
#         print("--- {} seconds --- send logs".format(time.time() - start_time))
#
#     @commands.command(name="stalin", pass_context=True, hidden=True)
#     async def logs_stalin(self, context, id:int):
#         if context.message.author.id != '135483608491229184':
#             return
#         messages = self.c.execute('select content from messages where author=?', (id,)).fetchall()
#         with io.open("stalin.txt", 'w', encoding='utf8') as file:
#             for x in messages:
#                 if not x[0] or x[0].startswith('['):
#                     continue
#                 file.write(x[0]+'\n')
#         with open('stalin.txt', 'rb') as file:
#              await self.bot.send_file(context.message.channel, file, filename='logs.{}.logs'.format(id), content="here're the results")
#
#
#     async def test(self):
#         '''
#         start_time = time.time()
#         self.c.execute('select * from messages').fetchall()
#         print("--- {} seconds --- select *".format(time.time() - start_time))
#
#         start_time = time.time()
#         self.c.execute('select * from messages where server=? ORDER BY id DESC LIMIT 1', (204621105720328193,)).fetchall()
#         print("--- {} seconds --- select * rpi ORDER BY id DESC LIMIT 1".format(time.time() - start_time))
#         '''
#
#         start_time = time.time()
#         logs = []
#         data_list = self.c.execute('select premade from messages where server=?', (204621105720328193,)).fetchall()
#         for data in data_list:
#             logs.append(data)
#         print("--- {} seconds --- build logs this thing".format(time.time() - start_time))
#
#     @commands.command(name="getall", pass_context=True, hidden=True)
#     async def logs_getall(self, context):
#         if context.message.author.id != '135483608491229184':
#             return
#         for sv in self.bot.servers:
#             for ch in sv.channels:
#                 try:
#                     log_list = []
#                     await self.bot.say(ch.name)
#                     async for message in self.bot.logs_from(ch, limit=999999999999999):
#                         #if last_message_in_logs and int(message.id) <= last_message_in_logs[0]:
#                         #    break
#
#                         log_list.append((message.id, time.mktime(message.timestamp.timetuple()), message.author.id,
#                                          message.channel.id, message.server.id, message.content.encode(),
#                                          ' '.join([x['url'] for x in message.attachments]), message.author.name))
#
#                     self.c.executemany('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)', log_list)
#                     self.database.commit()
#                 except:
#                     pass
#         await self.bot.say('done')
#
def setup(bot):
    bot.add_cog(Logs(bot))
