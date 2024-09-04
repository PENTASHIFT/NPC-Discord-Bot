import json
import queue
import threading
from urllib.request import Request, urlopen

import discord
import tkinter as tk
from dotenv import load_dotenv
from PIL import ImageTk, Image, ImageDraw

# TODO(josh): Just make this a single file repo and remove ./src/

if __name__ == "__main__":
   load_dotenv() 
