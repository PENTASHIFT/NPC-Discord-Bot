import os
import json
import threading
import urllib.request
from queue import Queue

import discord
from discord.ext import commands
from discord.commands import slash_command
import tkinter as tk
from dotenv import load_dotenv
from PIL import ImageTk, Image, ImageDraw


# TODO(josh): Join all these disparate commands into one or two function.
class Commands(commands.Cog):
    def __init__(self, bot, tqueue: Queue):
        self.bot = bot
        self.tqueue = tqueue

    @slash_command(name = "disapprove", description = "Express your disapproval.")
    async def disapprove(self, ctx):
        print(ctx.command)
        await ctx.respond("Thank you for your feedback.")

    @slash_command(name = "approve", description = "Express your approval.")
    async def approve(self, ctx):
        await ctx.respond("Thank you for your feedback.")

    @slash_command(name = "remember", description = "You will remember this.")
    async def approve(self, ctx):
        await ctx.respond("Thank you for your feedback.")

class WebImage:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.mask = Image.new("L", (self.width, self.height), 0)
        draw = ImageDraw.Draw(self.mask)
        draw.ellipse((0, 0, self.width, self.height), fill=255)

    def get(self, url: str):
        """ Make image circular and of specified dimensions. """
        request = urllib.request.Request(
            url = url,
            headers = { "User-Agent": "Mozilla/5.0" }
        )
        raw_data = urllib.request.urlopen(request).read()

        image = Image.open(io.BytesIO(raw_data)).resize((self.width, self.height))
        image.putalpha(self.mask)
        self.image = ImageTk.PhotoImage(image)
        return self.image

class Overlay:
    def __init__(self, width, height, y=0, padding=0):
        self.root = tk.Tk()
        self.root.title("NPC Discord Overlay")

        screen_width = self.root.winfo_screenwidth()
        distance = screen_width - (width + padding)
        self.root.geometry(f"{ width }x{ height }+{ distance }+{ y }")

        self.root.overrideredirect(True)    # Get rid of window borders.
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "gray")    # Set gray as transparent
        self.root.config(bg="gray")         # Make window transparent.

        self.img = WebImage(48, 48)
        self.label = None

if __name__ == "__main__":
    load_dotenv()
    token = os.environ.get("token")

    tqueue = Queue()

    bot = discord.Bot()
    bot.add_cog(Commands(bot, tqueue))

    bot.run(token)
