import sqlite3


class Prefix:
    def __init__(self):
        self.database = sqlite3.connect("cogs/buttybot.db")
        self.c = self.database.cursor()

        self.c.execute('''CREATE TABLE IF NOT EXISTS prefixes
                          (id text, prefix text)''')
        self.prefixes = {}
        for server, prefix in self.c.execute("SELECT * FROM prefixes").fetchall():
            self.prefixes[server] = prefix

    def get_prefix(self, bot, message, check_db=False):

        # if it's a pm: return '['
        # if '@butty ' is at the start of the message, return '@butty ' (note the space)
        # else get prefix from db (or cache)

        if not message.server:
            return '['

        if message.content.startswith('{} '.format(message.server.me.mention)):
            return '{0.me.mention} '.format(message.server)
        elif message.content.startswith('{} '.format(bot.user.mention)):
            return '{0.user.mention} '.format(bot)  # because sometimes a mention has an ! in it for no reason

        if check_db:
            prefix = self.c.execute("SELECT prefix FROM prefixes WHERE id=?", (message.server.id,)).fetchone()
        else:
            prefix = self.prefixes.get(message.server.id)

        if not prefix:
            return '['
        if prefix[0] != self.prefixes.get(message.server.id):
            self.prefixes[message.server.id] = prefix[0]

        return prefix[0]
