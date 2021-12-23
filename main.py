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
intents.guilds = True
bot = commands.Bot(command_prefix='sss ', intents=intents)

global INIT, STATE, SANTA_IMG_PATH, SANTA_EMOJI
INIT = False
SANTA_EMOJI = '🎅'
SANTA_IMG_PATH = 'santa.png'
STATE = {
    'waiting_for_reacts': False,
}

def bot_init(guild_id):
    global STATE, INIT
    guild = bot.get_guild(guild_id)
    STATE['guild'] = guild

    santa_role = utils.get(guild.roles, name='Secret Santa {}'.format(SANTA_EMOJI))
    if not santa_role:
        print('role not found')
        santa_role = guild.create_role(name='Secret Santa {}'.format(SANTA_EMOJI), colour=0xef2929, mentionable=True)
        print('role created')
    STATE['santa_role'] = santa_role
    INIT = True


@bot.event
async def on_ready():
    print('Secret Santa Services reporting for duty')


def dump_message_id():
    with open('message_id', 'w+') as f:
        f.write(str(STATE['message']))


def load_message_id():
    global STATE
    try:
        with open('message_id', 'r') as f:
            STATE['message'] = int(f.read().strip())
            STATE['waiting_for_reacts'] = True
        print('loaded message id: {}'.format(STATE['message']))
    except:
        pass


@bot.command(name='start')
async def start(ctx):
    print('command called: start')
    global STATE, SANTA_IMG, SANTA_EMOJI
    global INIT
    if not INIT:
        bot_init(message.guild.id)

    if STATE.get('message', '') == '':
        print('event message not found, creating')
        embed = Embed(title='Secret Santa Services', description='hoe hoe hoe SSS reporting for duty\nReact with :santa: to take part in Secret Santa :D', color=0xef2929)
        embed.set_thumbnail(url='attachment://santa.png')

        santa_img = File(SANTA_IMG_PATH)
        message = await ctx.send(file=santa_img, embed=embed)
        await message.add_reaction(SANTA_EMOJI)
        print('message id: {}'.format(message.id))
        STATE['message'] = message.id
        STATE['waiting_for_reacts'] = True

        dump_message_id()
    else:
        print('event message exists')
        await ctx.send('Another Secret Santa event is active. Cancel that event first by sending `sss cancel`')
    print('waiting for reacts')


@bot.command(name='cancel')
async def cancel(ctx):
    print('command called: cancel')

    global STATE, PARTICIPANTS
    if not STATE['waiting_for_reacts']:
        print('no active event')
        await ctx.send('No active event found. Start an event by sending `sss start`')
        return

    STATE['message'] = ''
    STATE['waiting_for_reacts'] = False
    dump_message_id()
    print('unset message id')
    PARTICIPANTS = defaultdict(bool)
    dump_participants()
    print('unset participants')
    await ctx.send('Event cancelled')


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
    if message_id != STATE['message']:
        print('m')
        return False
    if reaction != SANTA_EMOJI:
        print('e')
        return False

    return True


global PARTICIPANTS
PARTICIPANTS = defaultdict(bool)

def dump_participants():
    global PARTICIPANTS
    content = '\n'.join(['{} {}'.format(i, v) for i, v in PARTICIPANTS.items()])
    with open('participants', 'w+') as f:
        f.write(content)


def load_participants():
    global PARTICIPANTS
    try:
        with open('participants', 'r') as f:
            for line in f.readlines():
                line = line.strip().split()
                PARTICIPANTS[int(line[0])] = line[1]=='True'
        print('loaded participants: ', PARTICIPANTS)
    except:
        pass


@bot.event
async def on_raw_reaction_add(payload):
    global INIT
    if not INIT:
        bot_init(payload.guild_id)
    if not act_on_react(payload):
        return
    global STATE, PARICIPANTS
    user_id = payload.user_id
    user = STATE['guild'].get_member(user_id)
    print('react added: {}'.format(user))
    if not STATE['santa_role'] in user.roles:
        await user.add_roles(STATE['santa_role'])
        print('role added: {}'.format(user))
    else:
        print('role already present: {}'.format(user))
    PARTICIPANTS[user_id] = True
    print('participant added: {}'.format(user))

    channel = await user.create_dm()
    await channel.send('hoe hoe hoe welcome to Secret Santa Services :santa:, hoe\nType `help` to get a list of commands')

    dump_participants()


@bot.event
async def on_raw_reaction_remove(payload):
    global INIT
    if not INIT:
        bot_init(payload.guild_id)
    if not act_on_react(payload):
        return
    global STATE, PARTICIPANTS
    user_id = payload.user_id
    user = STATE['guild'].get_member(user_id)
    print('react removed: {}'.format(user))
    if STATE['santa_role'] in user.roles:
        await user.remove_roles(STATE['santa_role'])
        print('role removed: {}'.format(user))
    PARTICIPANTS[user_id] = False
    print('participant removed: {}'.format(user))

    channel = await user.create_dm()
    await channel.send('hoe hoe hoe you have withdrawn from Secret Santa. Thank you for using Secret Santa Services :santa:, hoe')

    dump_participants()


global ADDRESS_BOOK
ADDRESS_BOOK = defaultdict(str)

def dump_address_book():
    global ADDRESS_BOOK
    content = '\n'.join(['{} {}'.format(i, v) for i, v in ADDRESS_BOOK.items()])
    with open('address_book', 'w+') as f:
        f.write(content)


def load_address_book():
    global ADDRESS_BOOK
    try:
        with open('address_book', 'r') as f:
            for line in f.readlines():
                line = line.strip().split()
                ADDRESS_BOOK[int(line[0])] = ' '.join(line[1:])
        print('loaded address book: ', ADDRESS_BOOK)
    except:
        pass


@bot.event
async def on_message(message):
    global INIT
    if not INIT:
        bot_init(message)
    if message.author == bot.user:
        return
    if not isinstance(message.channel, channel.DMChannel):
        await bot.process_commands(message)
        return
    global STATE, PARTICIPANTS
    if not STATE['waiting_for_reacts']:
        await message.channel.send('Secret Santa Services is not handling any Secret Santa event right now. Ask your admin to start an event by sending `sss start` in server')
        return

    if message.content.strip() == 'help':
        await message.channel.send('hoe hoe hoe here is a list of commands:\n`set <address>` to set your address\n`get` to get your address\n`clear` to clear your address')

    if not PARTICIPANTS[message.author.id]:
        await message.channel.send('First react on the message in server to participate')
        return

    global ADDRESS_BOOK
    if message.content.strip().split()[0] == 'set':
        ADDRESS_BOOK[message.author.id] = message.content.strip().lstrip('set ')
        print('address added: {} {}'.format(message.author, ADDRESS_BOOK[message.author.id]))
        await message.channel.send('hoe hoe hoe your address has been set as:\n{}'.format(ADDRESS_BOOK[message.author.id]))
    if message.content.strip() == 'get':
        address = ADDRESS_BOOK[message.author.id]
        if address == '':
            await message.channel.send('you haven\'t set an address yet, dumbhoe. set address by sending `set <address>`')
            return
        await message.channel.send('hoe hoe hoe your address is set as:\n{}'.format(address))
    if message.content.strip() == 'clear':
        del(ADDRESS_BOOK[message.author.id])
        print('address removed: {}'.format(message.author))
        await message.channel.send('hoe hoe hoe your address has been deleted from the address book')

    dump_address_book()


@bot.event
async def on_error(event):
    global STATE
    await STATE['santa_role'].delete()


@bot.event
async def on_disconnect():
    global STATE
    await STATE['santa_role'].delete()


if __name__ == '__main__':
    load_message_id()
    load_participants()
    load_address_book()
    bot.run(_BOT_TOKEN)
