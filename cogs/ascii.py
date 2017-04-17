import numpy as np
import PIL
import PIL.Image as Image
import PIL.ImageFont
import PIL.ImageOps
import PIL.ImageDraw
import discord
from discord.ext import commands
import traceback
import aiohttp
import os


class Ascii:


    def __init__(self, bot_):
        self.bot = bot_
        self.gscalelist = ['@%#*+=-:. ', "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "]

    def getAverageL(sefl, image):
         # get image as numpy array
         im = np.array(image)
         # get the dimensions
         w,h = im.shape
         # get the average
         return np.average(im.reshape(w*h))

    def covertImageToAscii(self, fileName, cols, scale, gscale):
        image = Image.open(fileName).convert('L')
        W, H = image.size[0], image.size[1]
        w = W/cols
        h = w/scale
        rows = int(H/h)
        if cols > W or rows > H:
            return False

        aimg = []
        for j in range(rows):
            y1 = int(j*h)
            y2 = int((j+1)*h)
            if j == rows-1:
               y2 = H
            aimg.append("")
            for i in range(cols):
                x1 = int(i*w)
                x2 = int((i+1)*w)
                if i == cols-1:
                   x2 = W
                img = image.crop((x1, y1, x2, y2))
                avg = int(self.getAverageL(img))
                gsval = self.gscalelist[gscale-1][int((avg*9)/255)]
                aimg[j] += gsval
        return aimg

    def text_image(self, text_path, font_path=None):
        PIXEL_ON = 0  # PIL color to use for "on"
        PIXEL_OFF = 255  # PIL color to use for "off"
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
        font_path = font_path or 'cour.ttf'  # Courier New. works in windows. linux may need more explicit path
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
        image = PIL.Image.new(grayscale, (width, height), color=PIXEL_OFF)
        draw = PIL.ImageDraw.Draw(image)

        # draw each line of text
        vertical_position = 5
        horizontal_position = 5
        line_spacing = int(round(max_height * 0.8))  # reduced spacing seems better
        for line in lines:
            draw.text((horizontal_position, vertical_position),
                      line, fill=PIXEL_ON, font=font)
            vertical_position += line_spacing
        # crop the text
        c_box = PIL.ImageOps.invert(image).getbbox()
        image = image.crop(c_box)
        return image

    @commands.command(name="axy", pass_context=True)
    async def ascii(self, ctx, cols, url=None):
        if not url:
            try:
                url = ctx.message.attachments[0]['url']
            except IndexError:
                await self.bot.say("Okay first of all you need to give me an image")
        filename = "pictures/" + ctx.message.id
        with aiohttp.ClientSession() as session:
            with open(filename, 'wb') as f:
                r = await session.get(url)
                f.write(await r.read())
        aimg = self.covertImageToAscii(filename, int(cols), 0.5, 1)
        if not aimg:
            await self.bot.say("o heck that's too many columns try saying less than the resolution")
        else:
            msg = "```"
            for row in aimg:
                msg += (row + "\n")
            msg += "```"
            othernewfilename = "{}.txt".format(filename)
            with open(othernewfilename, "w") as f:
                f.write(msg)
            try:
                await self.bot.say(msg)
            except discord.errors.HTTPException:
                asciiimage = self.text_image(othernewfilename)
                newfilename = "{}.png".format(filename)
                asciiimage.save(newfilename)
                await self.bot.say("Welp, those dimensions were too big. Here it is in an image format.")
                await self.bot.send_file(ctx.message.channel, newfilename)
                await self.bot.send_file(ctx.message.channel, othernewfilename)
                os.system("del {} && del {}".format(newfilename, othernewfilename))

def setup(bot):
    bot.add_cog(Ascii(bot))