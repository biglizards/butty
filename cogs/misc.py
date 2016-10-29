import asyncio
import random
import urllib

from discord.ext import commands

import cogs.prefix as prefix


def is_admin(context):
    if context.message.author.id == "135496683009081345" or context.message.author.id == '135483608491229184':
        return True
    return context.message.author.server_permissions.manage_server


class Misc:
    def __init__(self, bot_):
        self.bot = bot_
        self.prefix = prefix.Prefix()

    def should_remove(self, m):
        prefix_ = self.prefix.get_prefix(self.bot, m, False)
        if m.content.startswith(prefix_) or m.author.id == "229223616217088001":
            return True
        return False

    @commands.command(name="stats", hidden=True)
    async def misc_stats(self):
        """shows how many servers butty's in, and how many people are in those servers"""
        total = 0
        for server in self.bot.servers:
            total += len(server.members)

        await self.bot.say("I am currently being a sandwich in {} servers, feeding {} users".format(
            len(self.bot.servers), total)
        )

    @commands.command(name="invite")
    async def misc_invite(self):
        """Show Butty's invite link

         Just in case you want to add it to your server"""
        await self.bot.say("https://harru.club/invite")

    @commands.command(name="clean", aliases=['purge'], pass_context=True)
    async def misc_clean(self, context, number: int = 0):
        """Remove butty's messages and command spam

        Removes any messages sent by butty, as well as any
        messages starting with butty's command prefix"""
        if not is_admin(context):
            await self.bot.say("Sorry, only server admins can use this command")
            return None
        elif not number:
            await self.bot.say("You need to set a limit, I can't just remove everything")
            return None
        elif number > 200:
            await self.bot.say("That's too many, calm down")
            return None

        await self.bot.purge_from(context.message.channel, limit=number, check=self.should_remove)

    @commands.command(name="flip")
    async def misc_flip(self):
        """Flip a coin

        For, you know, picking something randomly
        (as long as there's only two things to choose from)"""
        await self.bot.say("\\*flips coin* ... {}!".format(random.choice(['Heads', 'Tails'])))

    @commands.command(name="roll")
    async def misc_roll(self, number_of_sides, ):
        """roll x dice with y sides
        Also accepts xdy format"""
        pass

    @commands.command(name="duck")
    async def misc_duck(self, *message):
        query = urllib.parse.quote(' '.join(message))
        await self.bot.say("http://lmddgtfy.net/?q=" + query)


def setup(bot):
    bot.add_cog(Misc(bot))
