#! /usr/bin/env python3

from collections import defaultdict
from discord import channel, Embed, File, Intents, utils
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
_BOT_TOKEN = os.getenv('SSS_BOT_TOKEN')

intents = Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='sss ', intents=intents)

global STATE, SANTA_IMG, SANTA_EMOJI
SANTA_IMG = File('santa.png')
SANTA_EMOJI = '🎅'
STATE = {
    'waiting_for_reacts': False,
}

@bot.event
async def on_ready():
    print('Secret Santa Services reporting for duty')


@bot.command(name='start')
async def start(ctx):
    global STATE, SANTA_IMG, SANTA_EMOJI
    santa_role = await ctx.guild.create_role(name='Secret Santa {}'.format(SANTA_EMOJI), colour=0xef2929, mentionable=True)
    STATE['santa_role'] = santa_role
    STATE['guild'] = ctx.guild

    embed = Embed(title='Secret Santa Services', description='hoe hoe hoe SSS reporting for duty\nReact with :santa: to take part in Secret Santa :D', color=0xef2929)
    embed.set_thumbnail(url='attachment://santa.png')

    message = await ctx.send(file=SANTA_IMG, embed=embed)
    await message.add_reaction(SANTA_EMOJI)
    STATE['message'] = message
    STATE['waiting_for_reacts'] = True
    print('waiting for reactions')
    

def act_on_react(payload):
    global STATE, SANTA_EMOJI
    user_id = payload.user_id
    user = STATE['guild'].get_member(user_id)
    reaction = payload.emoji.name
    message_id = payload.message_id
    if user == bot.user:
        return False

    if not STATE['waiting_for_reacts']:
        print('wait')
        return False
    if message_id != STATE['message'].id:
        print('m')
        return False
    if reaction != SANTA_EMOJI:
        print('e')
        return False

    return True


@bot.event
async def on_raw_reaction_add(payload):
    if not act_on_react(payload):
        return
    global STATE
    user_id = payload.user_id
    user = STATE['guild'].get_member(user_id)
    if STATE['santa_role'] in user.roles:
        return
    await user.add_roles(STATE['santa_role'])
    print('role added: {}'.format(user))

    channel = await user.create_dm()
    await channel.send('hoe hoe hoe welcome to Secret Santa Services :santa:, hoe\nType `help` to get a list of commands')


@bot.event
async def on_raw_reaction_remove(payload):
    if not act_on_react(payload):
        return
    global STATE
    user_id = payload.user_id
    user = STATE['guild'].get_member(user_id)
    if not STATE['santa_role'] in user.roles:
        return
    await user.remove_roles(STATE['santa_role'])
    print('role removed: {}'.format(user))

    channel = await user.create_dm()
    await channel.send('hoe hoe hoe you have withdrawn from Secret Santa. Thank you for using Secret Santa Services :santa:, hoe')


global ADDRESS_BOOK
ADDRESS_BOOK = defaultdict(str)
@bot.event
async def on_message(message):
    if not isinstance(message.channel, channel.DMChannel):
        await bot.process_commands(message)
        return
    global STATE
    if not STATE['waiting_for_reacts']:
        print('Secret Santa Services is not handling any Secret Santa event right now. Ask your admin to start an event by sending `sss start` in server')
        return
    if message.content.strip() == 'help':
        await message.channel.send('hoe hoe hoe here is a list of commands:\n`set <address>` to set your address\n`get` to get your address\n`clear` to clear your address')
    global ADDRESS_BOOK
    if message.content.strip().split()[0] == 'set':
        ADDRESS_BOOK['{}'.format(message.author)] = message.content.strip().lstrip('set ')
        await message.channel.send('hoe hoe hoe your address has been set as:\n{}'.format(ADDRESS_BOOK['{}'.format(message.author)]))
    if message.content.strip() == 'get':
        address = ADDRESS_BOOK['{}'.format(message.author)]
        if address == '':
            await client.send_message('you haven\'t set an address yet, dumbhoe. set address by sending `set <address>`')
            return
        await message.channel.send('hoe hoe hoe your address is set as:\n{}'.format(address))
    if message.content.strip() == 'clear':
        del(ADDRESS_BOOK['{}'.format(message.author)])
        await message.channel.send('hoe hoe hoe your address has been deleted from the address book')


@bot.event
async def on_error(event):
    global STATE
    await STATE['santa_role'].delete()


@bot.event
async def on_disconnect():
    global STATE
    await STATE['santa_role'].delete()


if __name__ == '__main__':
    bot.run(_BOT_TOKEN)
