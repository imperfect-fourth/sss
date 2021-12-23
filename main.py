#! /usr/bin/env python3

from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
_BOT_TOKEN = os.getenv('SSS_BOT_TOKEN')

bot = commands.Bot(command_prefix='sss ')


@bot.event
async def on_ready():
    print('Secret Santa Services reporting for duty')


if __name__ == '__main__':
    bot.run(_BOT_TOKEN)
