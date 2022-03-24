import asyncio
import sqlite3
import time
from datetime import datetime

import parsedatetime.parsedatetime
from discord.ext import commands
from pytz import timezone


class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = sqlite3.connect("cogs/reminders.db")
        self.cursor = self.database.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS alerts
                          (user, channel, time, message, repeat, id)''')
        self.loop = self.bot.loop.create_task(self.reminder_loop())

    async def reminder_loop(self):
        while not self.bot.is_closed():
            now = datetime.now(timezone('UTC'))
            now = format(now, '%Y-%m-%d %H:%M:%S')
            alerts = self.cursor.execute("SELECT user, channel, message, id FROM alerts WHERE time < ?",
                                         (now,)).fetchall()

            for user_id, channel, message, index in alerts:
                try:
                    await self.bot.get_channel(channel).send("<@{}> {}".format(user_id, message))
                    self.cursor.execute("DELETE FROM alerts WHERE time < ? AND id=?", (now, index))
                    tofix = self.cursor.execute("SELECT * FROM alerts WHERE user=?", (user_id,)).fetchall()
                    self.cursor.execute("DELETE FROM alerts WHERE user=?", (user_id,))
                    for x, alert in enumerate(tofix):
                        self.cursor.execute("INSERT INTO alerts VALUES(?, ?, ?, ?, ?, ?)",
                                            (user_id, alert[1], alert[2], alert[3], alert[4], x))
                    self.database.commit()

                except:
                    pass

            self.database.commit()
            await asyncio.sleep(5)

    @commands.group(aliases=['r'], brief='do "help r" for more detail')
    async def remindme(self, ctx):
        """Because you need to not forget stuff

        EG:
        [remindme add 2 hours, remove the cake from hell
        [remindme show or [r show
        """
        pass

    @remindme.command(aliases=['a'], brief="e.g. [remindme add 1 hour, open the door")
    async def add(self, ctx, *args):
        msg = " ".join(args).split(", ", 1)
        cal = parsedatetime.Calendar()
        alertid = len(self.cursor.execute("SELECT * FROM alerts WHERE user=?", (ctx.author.id,)).fetchall())
        dontusemodulesasvariablenames = cal.parse(msg[0], datetime.now(timezone('UTC')))
        alert_time = time.strftime('%Y-%m-%d %H:%M:%S', dontusemodulesasvariablenames[0])
        self.cursor.execute("INSERT INTO alerts VALUES(?, ?, ?, ?, ?, ?)",
                            (ctx.author.id, ctx.channel.id, alert_time, msg[1], "no", alertid))
        self.database.commit()
        await ctx.send("Reminder set for " + alert_time + " UTC")

    @remindme.command(aliases=['d', 'r'])
    async def delete(self, ctx, ids: int):
        moveup = []
        user_id = ctx.author.id
        removed = self.cursor.execute("SELECT message FROM alerts WHERE user=? AND id=?", (user_id, ids)).fetchall()
        self.cursor.execute("DELETE FROM alerts WHERE user=? AND id=?", (user_id, ids))
        tofix = self.cursor.execute("SELECT * FROM alerts WHERE user=?", (user_id,)).fetchall()
        self.cursor.execute("DELETE FROM alerts WHERE user=?", (user_id,))
        for x, alert in enumerate(tofix):
            self.cursor.execute("INSERT INTO alerts VALUES(?, ?, ?, ?, ?, ?)",
                                (user_id, alert[1], alert[2], alert[3], alert[4], x))
        self.database.commit()
        await ctx.send("Deleted **" + removed[0][0] + "** from your reminder list")

    @remindme.command(aliases=['c'])
    async def clear(self, ctx):
        self.cursor.execute("DELETE FROM alerts WHERE user=?", (ctx.author.id,))
        self.database.commit()
        await ctx.send("Your reminders have been cleared")

    @remindme.command(aliases=['s'])
    async def show(self, ctx):
        reminder_list = self.cursor.execute("SELECT message, id FROM alerts WHERE user=?", (ctx.author.id,)).fetchall()
        reply = ''
        for reminder in reminder_list:
            reply += "{}: {}\n".format(reminder[1], reminder[0])
        await ctx.send("<@{}>'s reminders:\n{}".format(ctx.author.id, reply))


def setup(bot):
    bot.add_cog(Reminders(bot))
