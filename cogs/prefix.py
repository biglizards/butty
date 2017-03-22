import sqlite3
import os

class Prefix:
    def __init__(self):
        self.prefixes = {}
        self.database = sqlite3.connect("cogs/buttybot.db")
        self.c = self.database.cursor()

        self.c.execute('''CREATE TABLE IF NOT EXISTS prefixes
                          (id text, prefix text)''')

    def get_prefix(self, bot, message, check_db=True):
        if not message.server:
            return '['
        if '{0.me.mention} '.format(message.server) in message.content:
            return '{0.me.mention} '.format(message.server)
        elif '{0.user.mention} '.format(bot) in message.content:
            return '{0.user.mention} '.format(bot) # because sometimes a memtion has an ! in it for no reason

        if check_db:
            prefix = self.c.execute("SELECT prefix FROM prefixes WHERE id=?", (message.server.id,)).fetchone()
        else:
            prefix = self.prefixes.get(message.server.id)

        if not prefix:
            return '['
        if prefix[0] != self.prefixes.get(message.server.id):
            self.prefixes[message.server.id] = prefix[0]

        return prefix[0]
