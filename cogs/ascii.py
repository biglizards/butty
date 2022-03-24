import asyncio
import os
import threading

import PIL
import PIL.Image as Image
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageOps
import aiohttp
import discord
import numpy as np
from discord.ext import commands


class Ascii:
    def __init__(self, bot_):
        self.bot = bot_
        self.gsarray = np.asarray(list(' .:-=+*#%@'))

    @commands.command(name="ascii")
    async def ascii(self, ctx, width: int, url: str = None):
        """
        give it a url or an image and make it a shockingly bad ascii image
        """
        if not url:
            try:
                url = ctx.message.attachments[0].url
            except IndexError:
                await self.bot.say("Okay first of all you need to give me an image")
                return
        elif url[0] == "<" and url[-1] == ">":
            url = url[1:-1]

        filename = "pictures/{}".format(ctx.message.id)

        with aiohttp.ClientSession() as session:
            with open(filename, 'wb') as f:
                r = await session.get(url)
                f.write(await r.read())

        ascii_image = []

        t = threading.Thread(target=self.create_ascii, args=(filename, width, ascii_image))
        t.start()

        while not ascii_image:
            await asyncio.sleep(0.5)

        ascii_image = ascii_image[0]
        txtfilename = "{}.txt".format(filename)
        with open(txtfilename, "w") as f:
            f.write(ascii_image)

        try:
            await ctx.send("```{}```".format(ascii_image))

        except discord.errors.HTTPException:

            new_image = []

            t = threading.Thread(target=text_image, args=(txtfilename, new_image))
            t.start()

            while not new_image:
                await asyncio.sleep(0.5)

            width, height = new_image[0].size[0], new_image[0].size[1]

            if width < 10000 and height < 10000:
                pngfilename = "{}.png".format(filename)
                new_image[0].save(pngfilename)
                filebois = [
                    discord.File(pngfilename, pngfilename),
                    discord.File(txtfilename, txtfilename)
                ]
                await ctx.send("That had too many characters; here it is in image form", files=filebois)
                os.remove(pngfilename)

            else:
                await ctx.send("You madman, that file was over 10000 pixels tall/wide. I couldn't embed the image.",
                               file=discord.File(txtfilename, txtfilename))

        os.remove(txtfilename)
        os.remove(filename)

    def create_ascii(self, filename, width, ascii_image):
        image = Image.open(filename)
        cols = width if 0 < width <= 1000 else 50
        width, height = image.size[0], image.size[1]
        w = width / cols
        h = w / 0.5
        rows = height / h
        newsize = int(cols), int(rows)
        image = np.sum(np.asarray(image.resize(newsize)), axis=2)
        image -= image.min()
        image = (1.0 - image / image.max()) * (self.gsarray.size - 1)
        ascii_image.append("\n".join("".join(r) for r in self.gsarray[image.astype(int)]))


def text_image(text_path, ascii_image):
    """stolen from a stackexchange, i think"""
    pixel_on = 0  # PIL color to use for "on"
    pixel_off = 255  # PIL color to use for "off"
    """Convert text file to a grayscale image with black characters on a white background.
    arguments:
    text_path - the content of this file will be converted to an image
    font_path - path to a font file (for example impact.ttf)
    """
    grayscale = 'L'
    # parse the file into lines
    with open(text_path) as text_file:  # can throw FileNotFoundError
        lines = tuple(l.rstrip() for l in text_file.readlines())

    # choose a font (you can see more detail in my library on github)
    large_font = 20  # get better resolution with larger size
    font_path = 'cour.ttf'  # Courier New. works in windows. linux may need more explicit path
    try:
        font = PIL.ImageFont.truetype(font_path, size=large_font)
    except IOError:
        font = PIL.ImageFont.load_default()
        print('Could not use chosen font. Using default.')

    # make the background image based on the combination of font and lines
    pt2px = lambda pt: int(round(pt * 96.0 / 72))  # convert points to pixels
    max_width_line = max(lines, key=lambda s: font.getsize(s)[0])
    # max height is adjusted down because it's too large visually for spacing
    test_string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    max_height = pt2px(font.getsize(test_string)[1])
    max_width = pt2px(font.getsize(max_width_line)[0])
    height = max_height * len(lines)  # perfect or a little oversized
    width = int(round(max_width + 40))  # a little oversized
    image = PIL.Image.new(grayscale, (width, height), color=pixel_off)
    draw = PIL.ImageDraw.Draw(image)

    # draw each line of text
    vertical_position = 5
    horizontal_position = 5
    line_spacing = int(round(max_height * 0.8))  # reduced spacing seems better
    for line in lines:
        draw.text((horizontal_position, vertical_position),
                  line, fill=pixel_on, font=font)
        vertical_position += line_spacing
    # crop the text
    c_box = PIL.ImageOps.invert(image).getbbox()
    image = image.crop(c_box)
    ascii_image.append(image)


def setup(bot):
    bot.add_cog(Ascii(bot))
