import inspect
import os
import random
import sys
import urllib
from io import StringIO

import discord
from discord.ext import commands

import cogs.prefix as prefix


def is_owner(ctx):
    return ctx.author.id in [135496683009081345, 135483608491229184]


def is_admin(ctx):
    if is_owner(ctx):
        return True
    return ctx.author.guild_permissions.manage_guild


class Misc:
    def __init__(self, bot_):
        self.bot = bot_
        self.prefix = prefix.Prefix()

    def should_remove(self, message):
        prefix_ = self.prefix.get_prefix(self.bot, message, False)
        if message.content.startswith(prefix_) or message.author == self.bot.user:
            return True
        return False

    @commands.command(name="stats", hidden=True)
    async def misc_stats(self, ctx):
        """Shows how many guilds butty's in, and how many people are in those guilds"""
        total = 0
        for guild in self.bot.guilds:
            total += len(guild.members)
        await ctx.send("I am currently being a sandwich in {} guilds, feeding {} users".format(
            len(self.bot.guilds), total))

    @commands.check(is_owner)
    @commands.command(name="oinvite", hidden=True)
    async def misc_other_invite(self, ctx, name):
        guild = discord.utils.get(self.bot.guilds, name=name)
        if not guild:
            return
        await ctx.send(len(guild.members))
        await ctx.send(await guild.create_invite())

    @commands.command(name="invite")
    async def misc_invite(self, ctx):
        """Show's Butty's invite link

         Just in case you want to add it to your guild"""
        await ctx.send("https://discordapp.com/oauth2/authorize?client_id=229223616217088001&scope=bot&permissions="
                       "3271713")

    @commands.check(is_admin)
    @commands.command(name="clean", aliases=['purge'])
    async def misc_clean(self, ctx, number: int = 0):
        """<limit>  -  removes butty's commands and spam

        Removes any messages sent by butty, as well as any
        messages starting with butty's command prefix. 200 message limit"""
        if number == 0:
            await ctx.send("You need to set a limit, I can't just remove everything")
            return None
        elif number > 200:
            await ctx.send("That's too many, calm down")
            return None

        await ctx.channel.purge(limit=number, check=self.should_remove)

    @commands.command(name="flip")
    async def misc_flip(self, ctx):
        """Flip a coin

        For, you know, picking something randomly
        (as long as there's only two things to choose from)"""

        await ctx.send("\\*flips coin* ... {}!".format(random.choice(['Heads', 'Tails'])))

    @commands.command(name="roll")
    async def misc_roll(self, ctx, number_of_dice: int, number_of_sides: int):
        """<x> <y>  -  where x and y are integers, rolls x dice with y sides

        Rolls some dice, for when just two choices aren't enough"""
        diceno = ""
        if number_of_sides <= 0 or number_of_dice <= 0:
            await ctx.send("Number of sides and number of dice must be greater than 0")
            return
        if not number_of_sides > 100000000000 and not number_of_dice > 10:
            print("yay")
            for x in range(0, number_of_dice):
                diceno += "For dice {} you rolled {}\n".format(x + 1, random.randint(1, number_of_sides))
            await ctx.send(diceno)
        else:
            await ctx.send("The side limit is 100000000000 and the dice limit is 10")

    @commands.command(name="say")
    async def misc_say(self, ctx, *message):
        if is_admin(ctx):
            await ctx.send(' '.join(message))
        else:
            await ctx.send('{} said: {}'.format(ctx.message.author.mention, ' '.join(message)))

    @commands.command(name="duck")
    async def misc_duck(self, ctx, *message):
        """<query>  -  makes a lmddgtfy link for your <query>

        lmddgtfy = Let Me Duck Duck Go That For You"""
        query = urllib.parse.quote(' '.join(message))
        await ctx.send("http://lmddgtfy.net/?q=" + query)

    @commands.check(is_owner)
    @commands.command(name="restart", aliases=["getout"], hidden=True)
    async def misc_restart(self):
        os.system("git pull && systemctl restart butty")

    @commands.check(is_owner)
    @commands.command(name="presence", aliases=["statuschange"], hidden=True, pass_context=False)
    async def misc_statuschange(self, *new_game: str):
        await self.bot.change_presence(game=discord.Game(name=' '.join(new_game)))

    @commands.check(is_owner)
    @commands.command(name="vdbug", hidden=True)
    async def voice_debug(self, ctx):
        """Stop letting people use commands they shouldn't you bastard"""

        await ctx.send("```Python\n" + ctx.message.content[7:] + "```")
        code = ctx.message.content[7:].strip("`")
        codeobj = compile(code, '', 'exec')

        buffer = StringIO()
        sys.stdout = buffer

        exec(codeobj, globals(), locals())

        sys.stdout = sys.__stdout__

        await ctx.send(buffer.getvalue())

    @commands.check(is_owner)
    @commands.command(pass_context=True, hidden=True)
    async def debug(self, ctx, *, code: str):
        """Evaluates code."""

        code = code.strip('` ')
        python = '```py\n{}\n```'
        result = None

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'message': ctx.message,
            'guild': ctx.message.guild,
            'channel': ctx.message.channel,
            'author': ctx.message.author
        }

        env.update(globals())
        env.update(locals())

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            await ctx.send(python.format(type(e).__name__ + ': ' + str(e)))
            return

        await ctx.send(python.format(result))

    @commands.check(is_owner)
    @commands.command(name="gitpull", hidden=True)
    async def misc_gitpull(self, ctx):
        os.system("git pull")
        await ctx.send("done")

    @commands.check(is_owner)
    @commands.command(name="reload2", hidden=True)
    async def reload_cog2(self, ctx, cog):
        self.bot.unload_extension(cog)
        self.bot.load_extension(cog)
        await ctx.send("done")
    
    @commands.command(name="invites", hidden=True)
    async def invites(self, ctx):
        invs = await self.bot.invites_from(ctx.message.guild)
        t = 0
        for x in invs:
            if x.inviter == ctx.message.author:
                t += x.uses
        await ctx.send("{} has {} invites".format(ctx.message.author.name, t))


def setup(bot):
    bot.add_cog(Misc(bot))
