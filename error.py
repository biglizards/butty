import traceback
import urllib

import discord
import youtube_dl

from cogs.misc import is_owner


def get_traceback_from_exception(exception, message):
    tb = ''.join(traceback.format_exception(exception,
                                            value=exception,
                                            tb=exception.__traceback__))

    if message.guild:
        location = "**{0.name}** ({0.id})".format(message.guild)
    else:
        location = "DM"

    header = "COMMAND **{}** IN {}\n".format(message.content, location)
    error = "```py\n{}```".format(tb[len(header) - 1988:])
    return header + error


async def send_error_log(ctx, e, bot, is_voice=False):
    tb = get_traceback_from_exception(e, ctx.message)
    c_id = 956590975688507422 if is_voice else 956591141434826772
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
