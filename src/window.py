import io
import json
import time
from urllib.request import Request, urlopen

import tkinter as tk
from PIL import ImageTk, Image, ImageDraw

# TODO(josh): Better commenting.

class WebImage:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.mask = Image.new("L", (self.width, self.height), 0)
        draw = ImageDraw.Draw(self.mask)
        draw.ellipse((0, 0, self.width, self.height), fill=255)

    def get(self, url):
        """ Make image circular and of specified dimensions. """
        req = Request(
            url = url,
            headers = { "User-Agent": "Mozilla/5.0" }
        )
        raw_data = urlopen(req).read()

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

        # self.root.overrideredirect(True)    # Get rid of window borders.
        self.root.wm_attributes("-topmost", True)
        # self.root.wm_attributes("-transparentcolor", "gray")
        self.root.config(bg="gray")         # Make window transparent.

        self.img = WebImage(48, 48)
        self.label = None

    def _fade_out(self, increment):
        """ Decrement the alpha channel until it is invisible. """
        alpha = self.root.attributes("-alpha")

        if (alpha - increment) >= 0:
            self.root.attributes("-alpha", alpha - increment)
            self.root.after(100, self._fade_out, increment)
        else:
            self.root.attributes("-alpha", 0)

        return
    
    # TODO(josh): Rewrite _update and _get_input functions for multi-threaded
    #               Queues instead and better function calling.
    def _update(self, text, img):
        """ Update the contents of the label and schedule fade-out effect. """
        self.label.configure(
            image = img,
            text = f"   { text }."
        )

        self.label.pack(anchor = "e")
        self.root.attributes("-alpha", 1)
        self.root.after(2000, self._fade_out, 0.05)

    def _get_input(self):
        """ Get JSON input from stdin and update the contents of the label. """
        while True:
            # msg = json.loads(input())
            text = f"{ msg['name'] } { msg['command'] }"
            img = self.img.get(msg["img_link"])

            self._update(text, img)

    def run(self):
        """ Class entry point. """
        self.label = tk.Label(
            self.root,
            font = ("Georgia", 14),
            fg = "white",
            bg = "gray",
            compound = "left",
        )
        self.label.pack(anchor = "e")

        self.root.after(0, self._get_input)
        self.root.mainloop()

if __name__ == "__main__":
    overlay = Overlay(512, 64, y=96, padding=64)
    overlay.run()
