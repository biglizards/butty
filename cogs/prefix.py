import sqlite3

import discord


# TODO rewrite prefix so it's actually a module and not some strange object thing

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

        if isinstance(message.channel, discord.abc.PrivateChannel):
            return '['

        if message.content.startswith(message.guild.me.mention + ' '):
            return '{0.me.mention} '.format(message.guild)
        elif message.content.startswith(bot.user.mention + ' '):
            return '{0.user.mention} '.format(bot)  # because sometimes a mention has an ! in it for no reason
        # TODO replace with nicer looking regex

        if check_db:
            prefix = self.c.execute("SELECT prefix FROM prefixes WHERE id=?", (message.guild.id,)).fetchone()
        else:
            prefix = self.prefixes.get(message.guild.id)

        if not prefix:
            return '['
        if prefix[0] != self.prefixes.get(message.guild.id):
            self.prefixes[message.guild.id] = prefix[0]

        return prefix[0]
        # TODO i'm sure you can make this look nicer
        # maybe replace guild.id with guild (i think it would work)
