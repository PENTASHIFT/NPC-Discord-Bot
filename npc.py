import io
import os
import threading
import urllib.request
import queue

import discord
from discord.ext import commands
from discord.commands import slash_command
import tkinter as tk
from dotenv import load_dotenv
from PIL import ImageTk, Image, ImageDraw

# TODO(josh): Be more consistant with type hints and COMMENT!!
# TODO(josh): Figure out what to do with 'remember' command.

load_dotenv()   # FIXME(josh): Testing only!

# TODO(josh): Join all these disparate commands into one or two function.
class Commands(commands.Cog):
    guilds = [os.environ.get("guild_id")]   # FIXME(josh): Testing only!

    def __init__(self, bot, tqueue: queue.Queue):
        self.bot = bot
        self.tqueue = tqueue

    @slash_command(guild_ids = guilds, name = "approve", description = "Express your approval.")
    async def approve(self, ctx):
        img_url = ctx.author.avatar.url
        author_name = ctx.author.display_name

        self.tqueue.put({
            "img_url": img_url,
            "overlay_msg": f"{ author_name } approves."
        })

        await ctx.respond("Thank you for your feedback.")

    @slash_command(guild_ids = guilds, name = "disapprove", description = "Express your disapproval.")
    async def disapprove(self, ctx):
        img_url = ctx.author.avatar.url
        author_name = ctx.author.display_name

        self.tqueue.put({
            "img_url": img_url,
            "overlay_msg": f"{ author_name } disapproves." 
        })

        await ctx.respond("Thank you for your feedback.")

    @slash_command(guild_ids = guilds, name = "remember", description = "You will remember this.")
    async def remember(self, ctx):
        img_url = ctx.author.avatar.url
        author_name = ctx.author.display_name

        self.tqueue.put({
            "img_url": img_url,
            "overlay_msg": f"{ author_name } will remember that." 
        })

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
    def __init__(self, tqueue: queue.Queue, width: int, height: int, y: int = 0, padding: int = 0):
        self.tqueue = tqueue

        self.root = tk.Tk()
        self.root.title("NPC Discord Overlay")

        screen_width = self.root.winfo_screenwidth()
        distance = screen_width - (width + padding)
        self.root.geometry(f"{ width }x{ height }+{ distance }+{ y }")

        self.root.overrideredirect(True)    # Get rid of window borders.
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "gray")    # Set gray as transparent
        self.root.config(bg="gray")         # Make window transparent.

        self.web_img = WebImage(48, 48)
        self.label = tk.Label(
            self.root,
            font = ("Georgia", 14),
            fg = "white",
            bg = "gray",
            compound = "left",
        )
        self.label.pack(anchor = "e")

    def _fade_out(self, increment: float) -> None:
        alpha = self.root.attributes("-alpha")

        if (alpha - increment) >= 0:
            self.root.attributes("-alpha", alpha - increment)
            self.root.after(100, self._fade_out, increment)
        else:
            self.root.attributes("-alpha", 0)

    def _update(self, overlay_msg: str, img):
        self.label.configure(
            image = img,
            text = f"   { overlay_msg }"
        )

        self.label.pack(anchor = "e")
        self.root.attributes("-alpha", 1)
        self.root.after(2000, self._fade_out, 0.05)
    
    def _loop(self):
        while True:
            try:
                msg = self.tqueue.get(block=True, timeout=0.1)
                img = self.web_img.get(msg["img_url"])
                self._update(msg["overlay_msg"], img)
            except queue.Empty:
                break

        self.root.after(100, self._loop)
        
    def run(self):
        print("Now running overlay class!")

        self.root.after(0, self._loop)
        self.root.mainloop()

if __name__ == "__main__":
    token = os.environ.get("token")

    tqueue = queue.Queue()

    bot = discord.Bot()
    bot.add_cog(Commands(bot, tqueue))

    overlay = Overlay(tqueue, 512, 64, y=96, padding=64)
    bot_thread = threading.Thread(target=bot.run, args=(token,), daemon=True)
    bot_thread.start()

    overlay.run()
