import asyncio
import time

import discord
from discord.ext import commands


class Helping:
    def __init__(self, bot_, show_hidden=False, show_check_failure=False):
        self.bot = bot_
        self.show_hidden = show_hidden
        self.show_check_failure = show_check_failure

    def categorise(self):

        categories = {}

        for name, command in self.bot.commands.items():
            if name in command.aliases:
                continue
            cog_name = command.cog_name if command.cog_name is not None else "No Category"
            if cog_name not in categories.keys():
                categories[cog_name] = []
            categories[cog_name].append(command)

        return categories

    @staticmethod
    def has_subcommands(command):
        """bool : Specifies if the command has subcommands."""
        return isinstance(command, commands.GroupMixin)

    def help_for(self, categories, command_or_cog):

        com_str = ""
        why_is_this_a_list = []

        for x in command_or_cog:
            why_is_this_a_list.append(x.capitalize())
        cog_ = ' '.join(why_is_this_a_list)

        if cog_ in categories.keys():
            response = discord.Embed(title="Help for {}".format(cog_),
                                     colour=discord.Colour.purple())

            for command in categories[cog_]:

                if not self.has_subcommands(command):

                    com_str += "{}{} {}  -  {}".format(self.bot.command_prefix,
                                                       command.name,
                                                       ' '.join("<{}>".format(x) for x in command.params if
                                                                x is not "self" and x is not "ctx" and x is not "context"),
                                                       command.short_doc if command.short_doc is not None else "")

                else:
                    for name, subcommand in command.commands.items():

                        if name in subcommand.aliases:
                            continue

                        com_str += "{}{} {} {}  -  {}\n".format(self.bot.command_prefix,
                                                                command.name,
                                                                subcommand.name,
                                                                ' '.join("<{}>".format(x) for x in subcommand.params if
                                                                         x is not "self" and x is not "ctx" and x is not "context"),
                                                                subcommand.short_doc if subcommand.short_doc is not None else "No Description")

            response.add_field(name=cog_, value=com_str)

            return response

        elif cog_.lower() in self.bot.commands.keys():

            print("thinks its a command")

            command = self.bot.commands[cog_.lower()]

            if self.has_subcommands(self.bot.commands[cog_.lower()]):

                response = discord.Embed(title="Help for {}".format(cog_.lower()),
                                         colour=discord.Colour.purple(),
                                         description=command.help)

                alias_str = ""

                for name, subcommand in command.commands.items():

                    if name in subcommand.aliases:
                        continue

                    com_str += "{}{} {} {}  -  {}\n".format(self.bot.command_prefix,
                                                            command.name,
                                                            subcommand.name,
                                                            ' '.join("<{}>".format(x) for x in subcommand.params if
                                                                     x is not "self" and x is not "ctx"),
                                                            "{}".format(
                                                                subcommand.short_doc) if subcommand.short_doc is not None else "No Description")

                    aliases = " | ".join(subcommand.aliases)
                    alias_str += "[{}]\n".format(aliases) if aliases is not None else "\n"

                response.add_field(name="Subcommands", value=com_str)
                response.add_field(name="Aliases", value=alias_str, inline=False)

                return response

            else:

                response = discord.Embed(title="{}{} {}".format(self.bot.command_prefix,
                                                                command.name,
                                                                ' '.join("<{}>".format(x) for x in command.params if
                                                                         x is not "self" and x is not "ctx" and x is not "context")),
                                         colour=discord.Colour.purple())
                response.add_field(name="Description", value=command.help)
                aliases = "|".join(command.aliases)
                if aliases:
                    response.add_field(name="Command Aliases", value="[{}]".format(aliases))

                return response

    @commands.command(name="help", aliases=["info"], pass_context=True)
    async def help(self, ctx, *command_or_category):
        """welp

        what's going on"""

        reaction_list = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '❌', '🏘']

        categories = self.categorise()

        main_str = ""

        if not command_or_category:

            response_embeds = {}

            for cog_name, emoji in zip(categories.keys(), reaction_list):
                print(cog_name)
                response_embeds[emoji] = self.help_for(categories,
                                                       tuple(item for item in cog_name.split(' ') if item.strip()))
                print(len(response_embeds))
                main_str += "{} - {}\n\n".format(emoji, cog_name)

            print(response_embeds)

            parent_embed = discord.Embed(
                title="Butty",
                colour=discord.Colour.purple(),
                description="Okay so sorry about the low quality of this I'll make it better soon, do [help <category> to jump straight to it")
            parent_embed.set_thumbnail(url=self.bot.user.avatar_url)
            uptime = (time.time() - self.bot.startup_time)
            days, uptime = divmod(uptime, 86400)
            hours, uptime = divmod(uptime, 3600)
            mins, uptime = divmod(uptime, 60)
            total = 0
            for server in self.bot.servers:
                total += len(server.members)
            parent_embed.add_field(name="Stats",
                                   value="Servers - {}\n\nUsers - {}\n\nUptime = {}d{}h{}m\n\n\nᅠᅠ".format(len(self.bot.servers),
                                                                                                           total, days, hours,
                                                                                                           mins))
            parent_embed.add_field(name="Info",
                                   value="to be added sorry\n\nversion_no - 0.0.1\n\nsomething else to put here\n\n\nᅠᅠ")

            parent_embed.add_field(name="Commands", value=main_str)

            parent_embed.add_field(name="FAQ",
                                   value="**Wow butty what a stupid name for a bot**\n- yes\n\n**Why is the quality so terrible**\n- because we can't afford to host\nso many, help us by donating\n(link to be added)\n\n**Why is this FAQ so terrible**\n- Because no one has actually asked us\nquestions. Ask them here: link")

            msg = await self.bot.say(embed=parent_embed)

            for x, y in zip(response_embeds.keys(), reaction_list):
                await self.bot.add_reaction(msg, y)

            response_embeds['🏘'] = parent_embed

            await self.bot.add_reaction(msg, reaction_list[10])
            await self.bot.add_reaction(msg, reaction_list[9])

            await asyncio.sleep(2)

            reac_loop = True

            while reac_loop:
                for x in msg.reactions:
                    print(x.emoji)
                reac = await self.bot.wait_for_reaction(reaction_list, message=msg, timeout=60.0)
                print("looping")
                if reac:

                    if reac[0].emoji != reaction_list[9]:
                        await self.bot.edit_message(msg, embed=response_embeds[reac[0].emoji])

                    elif reac[0].emoji == reaction_list[9]:
                        await self.bot.delete_message(ctx.message)
                        await self.bot.delete_message(msg)
                        break


                else:
                    await self.bot.delete_message(ctx.message)
                    await self.bot.delete_message(msg)
                    break

        elif command_or_category:

            response_embed = self.help_for(categories, command_or_category)
            msg = await self.bot.say(embed=response_embed)

            await self.bot.add_reaction(msg, reaction_list[9])
            await asyncio.sleep(2)
            await self.bot.wait_for_reaction(reaction_list[9], message=msg)
            await self.bot.delete_message(ctx.message)
            await self.bot.delete_message(msg)


def setup(bot):
    bot.add_cog(Helping(bot))
