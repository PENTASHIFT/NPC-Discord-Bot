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

load_dotenv()

class Commands(commands.Cog):
    """ 
    All of the Discord bot's commands are collected here and all defined as
    slash commands or application commands. 
    See: https://discord.com/developers/docs/interactions/application-commands
    """
    # Pulled from .env file but only tested with a single id.
    guilds: list[str] = [os.environ.get("guild_id")]

    def __init__(self, bot, tqueue: queue.Queue):
        """
        Create an initialization of the Commands class which will eventually 
        be attached to bot via `bot.add_cog(...)`.

        :param bot: The Discord bot itself.
        :param tqueue: A queue that will be shared between the Discord bot
            thread and the main, Tkinter or UI thread as a mechanism of
            communication.
        """
        self.bot = bot
        self.tqueue = tqueue

    @slash_command(guild_ids = guilds, name = "approve", description = "Express your approval.")
    async def approve(self, ctx):
        """
        Invoked via a member of `guilds` sending a '/approve' command. In this
        we gather the user's information (i.e., avatar, username), pack it into
        a dict, and push it to the shared Queue along with the message we would
        like to see appear on screen. We then respond to the command message.

        :param ctx: The context of the message itself.
        """
        img_url: str = ctx.author.avatar.url
        author_name: str = ctx.author.display_name

        self.tqueue.put({
            "img_url": img_url,
            "overlay_msg": f"{ author_name } approves."
        })

        await ctx.respond("Thank you for your feedback.")

    @slash_command(guild_ids = guilds, name = "disapprove", description = "Express your disapproval.")
    async def disapprove(self, ctx):
        """
        Invoked via a member of `guilds` sending a '/disapprove' command. In this
        we gather the user's information (i.e., avatar, username), pack it into
        a dict, and push it to the shared Queue along with the message we would
        like to see appear on screen. We then respond to the command message.

        :param ctx: The context of the message itself.
        """        
        img_url: str = ctx.author.avatar.url
        author_name: str = ctx.author.display_name

        self.tqueue.put({
            "img_url": img_url,
            "overlay_msg": f"{ author_name } disapproves." 
        })

        await ctx.respond("Thank you for your feedback.")

    @slash_command(guild_ids = guilds, name = "remember", description = "You will remember this.")
    async def remember(self, ctx):
        """
        Invoked via a member of `guilds` sending a '/remember' command. In this
        we gather the user's information (i.e., avatar, username), pack it into
        a dict, and push it to the shared Queue along with the message we would
        like to see appear on screen. We then respond to the command message.

        :param ctx: The context of the message itself.
        """
        img_url: str = ctx.author.avatar.url
        author_name: str = ctx.author.display_name

        self.tqueue.put({
            "img_url": img_url,
            "overlay_msg": f"{ author_name } will remember that." 
        })

        await ctx.respond("Thank you for your feedback.")

class WebImage:
    """
    A utility class to be accessed via `Overlay`. It is used to recieve a user's
    Discord avatar via the url provided by the API, resize it, and apply a mask
    to make it circular. This image will then be displayed on the screen by the
    `Overlay` class next to a relevant message.
    """
    def __init__(self, width: int, height: int):
        """
        Initialize the class and create circle mask.

        :param width: The specified output width of the image in px.
        :param height: The specified output height of the image in px.
        """
        self.width: int = width
        self.height: int = height

        # Create the image mask.
        self.mask = Image.new("L", (self.width, self.height), 0)
        draw = ImageDraw.Draw(self.mask)
        draw.ellipse((0, 0, self.width, self.height), fill=255)

    def get(self, url: str):
        """
        Access the raw avatar image data via a Discord CDN url and apply the
        circle image mask.

        :param url: The Discord CDN url for a user's avatar.
        """
        request = urllib.request.Request(
            url = url,
            headers = { "User-Agent": "Mozilla/5.0" }   # Forbidden otherwise.
        )
        raw_data = urllib.request.urlopen(request).read()

        # Read, resize, and apply mask.
        image = Image.open(io.BytesIO(raw_data)).resize((self.width, self.height))
        image.putalpha(self.mask)
        self.image = ImageTk.PhotoImage(image)
        return self.image

class Overlay:
    """
    Class in charge of creating the Overlay UI via Tkinter. Will pull
    information from the queue it shares with the Discord bot and display the
    relevant information.
    """
    def __init__(self, tqueue: queue.Queue, width: int, height: int, y: int = 0, padding: int = 0):
        """
        Initialize the class and set up the Tkinter instance and its parameters.

        :param tqueue: A queue that will be shared between the Discord bot
            thread and the main, Tkinter or UI thread as a mechanism of
            communication.
        :param width: The width of the overlay screen in px.
        :param height: The height of the overlay screen in px.
        :param y: The distance from the top of the screen to the top of the
            overlay window in px. Default is 0.
        :param padding: The distance from the right of the screen to the right
            edge of the overlay window in px. Default is 0.
        """

        self.tqueue = tqueue

        self.root = tk.Tk()
        self.root.title("NPC Discord Overlay")

        screen_width = self.root.winfo_screenwidth()    # Get the screen's width in px
        distance = screen_width - (width + padding)
        self.root.geometry(f"{ width }x{ height }+{ distance }+{ y }")

        self.root.overrideredirect(True)    # Get rid of window borders.
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "gray")    # Set gray as transparent
        self.root.config(bg="gray")         # Make window transparent.

        self.web_img = WebImage(48, 48)

        # Create an empty label to modify upon pulling from the queue.
        self.label = tk.Label(
            self.root,
            font = ("Georgia", 14),
            fg = "white",
            bg = "gray",
            compound = "left",
        )
        self.label.pack(anchor = "e")       # Anchor the label to the right.

    def _fade_out(self, increment: float):
        """
        Creates a fade out animation for the window so we aren't stuck with a
        single user's message.

        :param increment: Value to subtract from the window's alpha value.
        """
        alpha: float = self.root.attributes("-alpha")   # Current alpha of window.

        if (alpha - increment) >= 0.0:
            self.root.attributes("-alpha", alpha - increment)
            self.root.after(100, self._fade_out, increment)
        else:
            self.root.attributes("-alpha", 0.0)

    def _update(self, overlay_msg: str, img):
        """
        Updates the label defined in `__init__` to include the relevant user's
        avatar image already resized etc. and the relevant message.

        :param overlay_msg: The message to be displayed on the overlay (i.e.,
            '<username> disapproves.')
        :param img: The user's avatar image after passed through `WebImage` and
            resized etc.
        """
        # Update the window's label.
        self.label.configure(
            image = img,
            text = f"   { overlay_msg }"
        )
        self.label.pack(anchor = "e")   # Anchor the label to the right.

        self.root.attributes("-alpha", 1)
        self.root.after(2000, self._fade_out, 0.05)
    
    def _loop(self):
        """
        Loop through and flush the shared queue to get information as it is
        populated and update the overlay window.
        """
        while True:
            try:
                msg = self.tqueue.get(block=True, timeout=0.1)
                img = self.web_img.get(msg["img_url"])
                self._update(msg["overlay_msg"], img)
            except queue.Empty:
                break

        self.root.after(100, self._loop)
        
    def run(self):
        """
        The public entry point for starting and running the overlay.
        """
        self.root.after(0, self._loop)  # Immediately start looping through the queue.
        self.root.mainloop()        # Start the overlay window.

if __name__ == "__main__":
    token = os.environ.get("token")
    tqueue = queue.Queue()

    bot = discord.Bot()
    bot.add_cog(Commands(bot, tqueue))

    overlay = Overlay(tqueue, 512, 64, y=96, padding=64)

    # Start the Discord bot thread.
    bot_thread = threading.Thread(target=bot.run, args=(token,), daemon=True)
    bot_thread.start()

    overlay.run()
