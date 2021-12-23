#! /usr/bin/env python3

from discord import Embed, File
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
_BOT_TOKEN = os.getenv('SSS_BOT_TOKEN')

bot = commands.Bot(command_prefix='sss ')


@bot.event
async def on_ready():
    print('Secret Santa Services reporting for duty')


@bot.command(name='start')
async def start(ctx):
    embed = Embed(title='Secret Santa Services', description='hoe hoe hoe SSS reporting for duty\nReact with :santa: to take part in Secret Santa :D', color=0xef2929)
    santa = File('santa.png')
    embed.set_thumbnail(url='attachment://santa.png')
    await ctx.send(file=santa, embed=embed)

if __name__ == '__main__':
    bot.run(_BOT_TOKEN)
