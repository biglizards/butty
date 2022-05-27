import traceback
import urllib

import discord
import youtube_dl

from cogs.misc import is_owner


def get_traceback_from_exception(exception, guild, message):
    tb = ''.join(traceback.format_exception(exception,
                                            value=exception,
                                            tb=exception.__traceback__))

    if guild:
        location = f'**{guild.name}** ({guild.id})'
    else:
        location = 'DM'

    header = f'COMMAND **{message}** IN {location}\n'
    error = "```py\n{}```".format(tb[len(header) - 1988:])
    return header + error


async def send_error_log(ctx, e, bot, is_voice=False):
    if ctx.message is not None and ctx.message.content is not None:
        message = ctx.message.content
    elif ctx.command is not None:
        # todo: pretty print selected_options
        message = f'/{ctx.command.name} {ctx.selected_options}'
    else:
        message = '[unknown]'

    tb = get_traceback_from_exception(e, ctx.guild, message)
    c_id = 957299024782831657 if is_voice else 957299045141991515
    channel = discord.utils.get(bot.get_all_channels(), id=c_id)

    await channel.send(tb)

    # if it's easy to format, then print the actual error instead
    nice_errors = (youtube_dl.utils.DownloadError, urllib.error.HTTPError)
    if isinstance(e, nice_errors):
        return await ctx.send(e)

    if is_owner(ctx):
        await ctx.send(f'**Error**\ntype: {type(e)}\nvalue: {e}')
    else:
        await ctx.send(
            "An unhandled error occurred! Big sad :("
        )
