#! /usr/bin/env python3

from collections import defaultdict
from discord import channel, Embed, File, Intents, utils
from discord.ext import commands
from dotenv import load_dotenv
import random
import os

load_dotenv()
_BOT_TOKEN = os.getenv('SSS_BOT_TOKEN')

intents = Intents.default()
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix='sss ', intents=intents, help_command=None)

global INIT, STATE, SANTA_IMG_PATH, SANTA_EMOJI
INIT = False
SANTA_EMOJI = '🎅'
SANTA_IMG_PATH = 'santa.png'
STATE = {
    'waiting_for_reacts': False,
}

async def bot_init(guild_id):
    global STATE, INIT
    guild = bot.get_guild(guild_id)
    STATE['guild'] = guild

    santa_role = utils.get(guild.roles, name='Secret Santa {}'.format(SANTA_EMOJI))
    if not santa_role:
        print('role not found')
        santa_role = await guild.create_role(name='Secret Santa {}'.format(SANTA_EMOJI), colour=0xef2929, mentionable=True)
        print('role created')
    STATE['santa_role'] = santa_role
    INIT = True


def is_me_or_admin():
    def predicate(ctx):
        return (ctx.message.author.id == 565550897220943902) or (ctx.message.author.guild_permissions.administrator)
    return commands.check(predicate)

@bot.event
async def on_ready():
    print('Secret Santa Services reporting for duty')


@bot.command(name='help')
async def help(ctx):
    print('command called: help')
    await ctx.send('Here is a list of commands:\n\
`sss start`: start the Secret Santa event\n\
`sss cancel`: cancel ongoing Secret Santa event\n\
`sss status`: check status of Secret Santa event\n\
`sss shuffle`: assign Secret Santas to everyone participating')

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
@is_me_or_admin()
async def start(ctx):
    print('command called: start')
    global STATE, SANTA_IMG, SANTA_EMOJI

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
    print(STATE)
    print('waiting for reacts')


@bot.command(name='cancel')
@is_me_or_admin()
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


@bot.command(name='status')
@is_me_or_admin()
async def status(ctx):
    print('command called: status')

    global STATE
    if not STATE['waiting_for_reacts']:
        await ctx.send('No active event found. Start an event by sending `sss start`')
        return
    global PARTICIPANTS, ADDRESS_BOOK
    embed = Embed(title='Secret Santa Services', description='Event status', color=0xef2929)
    participants_field = ''
    no_address_field = ''
    no_phone_field = ''
    for i, v in PARTICIPANTS.items():
        if v:
            participants_field += '<@{}>\n'.format(i)
            if ADDRESS_BOOK[i] == '':
                no_address_field += '<@{}>\n'.format(i)
            if PHONE_BOOK[i] == '':
                no_phone_field += '<@{}>\n'.format(i)
    if participants_field == '':
        participants_field = 'No one has joined yet'
    embed.add_field(name='Participants:', value=participants_field, inline=False)
    if not (no_address_field == ''):
        embed.add_field(name='address not added by:', value=no_address_field, inline=False)
    if not (no_phone_field == ''):
        embed.add_field(name='number not added by:', value=no_phone_field, inline=False)

    await ctx.send(embed=embed)


def test(array1, array2):
    for i in range(len(array1)):
        if array1[i] == array2[i]:
            print(i)
            return False
    return True


def dump_secret_santas(secret_santas):
    with open('secret_santas', 'w+') as f:
        f.write('\n'.join(['{} {}'.format(i, v) for i, v in secret_santas.items()]))


async def shuffle_and_assign(sender_ids):
    receiver_ids = [_ for _ in sender_ids]

    random.shuffle(receiver_ids)
    while not test(sender_ids, receiver_ids):
        print(sender_ids, receiver_ids)
        random.shuffle(receiver_ids)
 
    global STATE
    users = {}

    secret_santas = {}
    for i, sender_id in enumerate(sender_ids):
        receiver_id = receiver_ids[i]
        if users.get(sender_id, '') == '':
            users[sender_id] = STATE['guild'].get_member(sender_id)
        if users.get(receiver_id, '') == '':
            users[receiver_id] = STATE['guild'].get_member(receiver_id)
        sender = users[sender_id]
        receiver = users[receiver_id]
        secret_santas['{}'.format(sender)] = '{}'.format(receiver)

        print('secret santa set: {} {}'.format(sender, receiver))
        channel = await sender.create_dm()
        await channel.send('hoe hoe hoe you are secret santa for {}!\ntheir address is:\n{}\n\nmerry christmas from Secret Santa Services :santa: hoe hoe, hoe'.format(receiver, ADDRESS_BOOK[receiver_id]))

    dump_secret_santas(secret_santas)



@bot.command(name='shuffle')
@is_me_or_admin()
async def shuffle(ctx):
    print('command called: shuffle')

    global STATE
    if not STATE['waiting_for_reacts']:
        await ctx.send('No active event found. Start an event by sending `sss start`')
        return
    global PARTICIPANTS, ADDRESS_BOOK, PHONE_BOOK
    with_address_and_phone = []
    no_address = []
    no_phone = []
    for i, v in PARTICIPANTS.items():
        if v:
            if (ADDRESS_BOOK[i] != '') and (PHONE_BOOK[i] != ''):
                with_address_and_phone.append(i)
            if ADDRESS_BOOK[i] == '':
                no_address.append(i)
            if PHONE_BOOK[i] == '':
                no_phone.append(i)

    if no_address != [] or no_phone != []:
        print('people with incomplete info found, can\'t shuffle')
        desc = ''
        if no_address != []:
            desc += 'Following people have not added their address:\n'
            for i in no_address:
                desc += '<@{}>\n'.format(i)

        if no_phone != []:
            desc += '\nFollowing people have not added their number:\n'
            for i in no_phone:
                desc += '<@{}>\n'.format(i)

        embed = Embed(title='Secret Santa Services', description=desc, color=0xef2929)
        embed.set_footer(text='Ask them to set address and number or send `sss force-shuffle` or `sss fs` to continue without them')
        await ctx.send(embed=embed)
    else:
        STATE['waiting_for_reacts'] = False
        STATE['message'] = ''
        print('shuffling')
        await shuffle_and_assign(with_address_and_phone)
        await ctx.send('Secret Santas assigned hoe hoe hoe')
        print('shuffled')
        PARTICIPANTS = defaultdict()
        dump_message_id()
        dump_participants()


@bot.command(aliases=['force-shuffle', 'fs'])
@is_me_or_admin()
async def force_shuffle(ctx):
    print('command called: force-shuffle')

    global STATE
    if not STATE['waiting_for_reacts']:
        await ctx.send('No active event found. Start an event by sending `sss start`')
        return
    global PARTICIPANTS, ADDRESS_BOOK, PHONE_BOOK
    with_address_and_phone = []
    for i, v in PARTICIPANTS.items():
        if v:
            if (ADDRESS_BOOK[i] != '') and (PHONE_BOOK[i] != ''):
                with_address_and_phone.append(i)

    STATE['message'] = ''
    print('shuffling')
    await shuffle_and_assign(with_address_and_phone)
    await ctx.send('Secret Santas assigned hoe hoe hoe')
    print('shuffled')
    dump_message_id()
    dump_participants()


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
        await bot_init(payload.guild_id)
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
        await bot_init(payload.guild_id)
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


global ADDRESS_BOOK, PHONE_BOOK
ADDRESS_BOOK = defaultdict(str)
PHONE_BOOK = defaultdict(str)

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


def dump_phone_book():
    global PHONE_BOOK
    content = '\n'.join(['{} {}'.format(i, v) for i, v in PHONE_BOOK.items()])
    with open('phone_book', 'w+') as f:
        f.write(content)


def load_phone_book():
    global PHONE_BOOK
    try:
        with open('phone_book', 'r') as f:
            for line in f.readlines():
                line = line.strip().split()
                PHONE_BOOK[int(line[0])] = ' '.join(line[1:])
        print('loaded phone book: ', PHONE_BOOK)
    except:
        pass


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if not isinstance(message.channel, channel.DMChannel):
        global INIT
        if not INIT:
            await bot_init(message.guild.id)
        await bot.process_commands(message)
        return
    global STATE, PARTICIPANTS
    if not STATE['waiting_for_reacts']:
        await message.channel.send('Secret Santa Services is not handling any Secret Santa event right now. Ask your admin to start an event by sending `sss start` in server')
        return

    if message.content.strip() == 'help':
        await message.channel.send('hoe hoe hoe here is a list of commands:\n\
`set address <address>` to set your address\n\
`set number <number>` to set your number\n\
`get` to get your address and number\n\
`clear` to clear your address and number')

    if not PARTICIPANTS[message.author.id]:
        await message.channel.send('First react on the message in server to participate')
        return

    global ADDRESS_BOOK, PHONE_BOOK
    line = message.content.strip().split()
    if line[0] == 'set':
        if line[1] == 'address':
            ADDRESS_BOOK[message.author.id] = ' '.join(line[2:])
            print('address added: {} {}'.format(message.author, ADDRESS_BOOK[message.author.id]))
            await message.channel.send('hoe hoe hoe your address has been set as:\n`{}`'.format(ADDRESS_BOOK[message.author.id]))
        elif line[1] == 'number':
            PHONE_BOOK[message.author.id] = ' '.join(line[2:])
            print('number added: {} {}'.format(message.author, PHONE_BOOK[message.author.id]))
            await message.channel.send('hoe hoe hoe your number has been set as:\n`{}`'.format(PHONE_BOOK[message.author.id]))
    if message.content.strip() == 'get':
        address = ADDRESS_BOOK[message.author.id]
        number = PHONE_BOOK[message.author.id]
        if address == '':
            address = 'not set'
        if number == '':
            number = 'not set'
        await message.channel.send('hoe hoe hoe here is your info:\n**address:** `{}`\n**number:** `{}`'.format(address, number))
    if message.content.strip() == 'clear':
        del(ADDRESS_BOOK[message.author.id])
        del(PHONE_BOOK[message.author.id])
        print('address removed: {}'.format(message.author))
        print('number removed: {}'.format(message.author))
        await message.channel.send('hoe hoe hoe your address has been deleted from the address book')
        await message.channel.send('hoe hoe hoe your number has been deleted from the phone book')

    dump_address_book()
    dump_phone_book()


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
    load_phone_book()
    bot.run(_BOT_TOKEN)
