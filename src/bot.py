import os
import json

import discord

bot = discord.Bot()

SECRETS = json.load(open("secrets.json"))

@bot.event
async def on_ready():
    pass

@bot.slash_command(
    guild_ids=SECRETS["guild_ids"], name="disapprove",
    description="Express your disapproval."
)
async def disapprove(ctx):
    text = {
        "img_link": ctx.author.avatar.url,
        "name": ctx.author.display_name,
        "command": "disapprove"
    }

    await ctx.respond("Thank you for your feedback.")


bot.run(SECRETS["token"])

