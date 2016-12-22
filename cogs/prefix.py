import sqlite3
import os

real_path = os.path.dirname(os.path.realpath(__file__)) + "/"
os.chdir(real_path)


class Prefix:
    def __init__(self):
        self.prefixes = {}

    def get_prefix(self, bot, message, check_db=True):
        if not message.server:
            return '['
        if '{0.me.mention} '.format(message.server) in message.content:
            return '{0.me.mention} '.format(message.server)
        elif '{0.user.mention} '.format(bot) in message.content:
            return '{0.user.mention} '.format(bot) # because sometimes a memtion has an ! in it for no reason

        if check_db:
            prefix = c.execute("SELECT prefix FROM prefixes WHERE id=?", (message.server.id,)).fetchone()
        else:
            prefix = self.prefixes.get(message.server.id)

        if not prefix:
            return '['
        if prefix[0] != self.prefixes.get(message.server.id):
            self.prefixes[message.server.id] = prefix[0]

        return prefix[0]

database = sqlite3.connect("buttybot.db")
c = database.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS prefixes
             (id text, prefix text)''')
