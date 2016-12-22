from discord.ext import commands
from datetime import datetime
from dateutil.relativedelta import relativedelta
import parsedatetime.parsedatetime
from pytz import timezone
import sqlite3
import asyncio


async def reminder_loop(self):
    while not self.bot.is_closed:
        now = str(datetime.now(timezone('UTC')))[:-16]
        alerts = self.cursor.execute("SELECT message FROM alert WHERE time=?", (now,)).fetchall()
        users = self.cursor.execute("SELECT user FROM alert WHERE time=?", (now,)).fetchall()
        channels = self.cursor.execute("SELECT channel FROM alert WHERE time=?", (now,)).fetchall()
        if len(alerts) != 0:
            for x in range(0, len(alerts)):
                channel = self.bot.get_channel(channels[x][0])
                await self.bot.send_message(channel, "<@" + users[x][0] + ">" + alerts[x][0])
                self.cursor.execute("DELETE FROM alert WHERE time=?", (now,))
                self.database.commit()
        await asyncio.sleep(5)


class Reminders:

    def __init__(self, bot):
        self.bot = bot
        self.database = sqlite3.connect("cogs/buttybot.db")
        self.cursor = self.database.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS alert
                          (user, channel, time, message, repeat, id)''')
        self.loop = self.bot.loop.create_task(reminder_loop(self))

    @commands.group(aliases=['r'], brief='do "help r" for more detail')
    async def reminder(self):
        """Because you need to not forget stuff

        EG:
        [reminder add 2 hours, remove the cake from hell
        [r show
        """
        pass

    @reminder.command(aliases=['a'], pass_context="True")
    async def add(self, context):
        # oh god what is this shit
        # harru why you do this
        # fuck off it works probably
        message = " ".join(context.message.content.split(" ")[2:])
        msg = message.split(",", 1)
        cal = parsedatetime.Calendar()
        time = datetime.now(timezone('UTC'))
        currenttime = cal.parse(str(time))[0]
        newtime = cal.parse(msg[0], currenttime)[0]
        print(newtime)
        list = []
        alertid = len(self.cursor.execute("SELECT * FROM alert WHERE user=?", (context.message.author.id,)).fetchall()) + 1
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
        time = str(time)[:-16]
        self.cursor.execute("INSERT INTO alert VALUES(?, ?, ?, ?, ?, ?)", (context.message.author.id, context.message.channel.id, time, msg[1], "no", alertid))
        self.database.commit()
        await self.bot.say("Reminder set for " +  time + " UTC")

    @reminder.command(aliases=['d', 'r'],pass_context=True)
    async def delete(self, context):
        args = context.message.content.split(" ")
        ids = int(args[2])
        moveup = []
        user = context.message.author.id
        removed = (self.cursor.execute("SELECT message FROM alert WHERE user=? AND id=?", (user, ids))).fetchall()
        self.cursor.execute("DELETE FROM alert WHERE user=? AND id=?", (user, ids))
        newid = (self.cursor.execute("SELECT id FROM alert WHERE id=?", (user,))).fetchall()
        for x in range(0, len(newid)):
            if newid[x][0] > ids:
                moveup.append(newid[x][0])
        for x in range(0, len(moveup)):
            self.cursor.execute("UPDATE alert SET id=? WHERE id=? AND user=?", ((moveup[x] - 1), moveup[x], user))
        self.database.commit()
        await self.bot.say("Deleted **" + removed[0][0] + "** from your reminder list")

    @reminder.command(aliases=['c'], pass_context=True)
    async def clear(self, context):
        user = context.message.author.id
        self.cursor.execute("DELETE FROM alert WHERE user=?", (user,))
        self.database.commit()
        await self.bot.say("Your reminders have been cleared")

    @reminder.command(aliases=['s', 'l'], pass_context=True)
    async def show(self, context):
        reminder_list = self.cursor.execute("SELECT message FROM alert WHERE user=?", (context.message.author.id,)).fetchall()
        x = 0
        reply = ''
        for reminder in reminder_list:
            x += 1
            reply += str(x) + ": " + reminder[0] + "\n"
        await self.bot.say("<@" + context.message.author.id + ">'s reminders:\n" + reply)


def setup(bot):
    bot.add_cog(Reminders(bot))
