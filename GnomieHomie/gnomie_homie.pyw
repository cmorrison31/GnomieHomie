import asyncio
import configparser
import logging
import os
import random
import sys
from datetime import datetime

import discord

client = discord.Client()
config = configparser.ConfigParser()


def load_config(config_file_path):
    config.read(config_file_path)


@client.event
async def bot_login():
    key = config['credentials']['key']
    await client.login(key)
    await client.connect()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


async def process_roll(message):
    data = message.content.strip().split()

    dice = 6  # default dice size
    num_rolls = 1  # default number of rolls
    message_text = '{!s}\n'.format(message.author.mention)

    # If user supplied data exits, parse it and try to get the dice size and
    # number of requested rolls
    if len(data) > 1:
        try:
            for arg in data[1:]:
                if arg.lower().startswith('d'):
                    dice = int(arg[1:])
                else:
                    num_rolls = int(arg)
        except ValueError:
            message_text += 'Invalid /roll command format.\nThe correct ' \
                            'format is: /roll [*d*size] [number of rolls]\n' \
                            'Example: /roll d20 3'
            await client.send_message(message.channel, message_text)
            return

    # Valid the user input and provide feedback if necessary
    if num_rolls <= 0 or num_rolls > 10:
        message_text += 'The number of rolls specified must be greater than ' \
                        '0 and less than 11.'
        await client.send_message(message.channel, message_text)
        return

    if dice < 2 or dice > 100:
        message_text += 'The dice size specified must be greater than 1 and ' \
                        'less than 101.'
        await client.send_message(message.channel, message_text)
        return

    random.seed(os.urandom(64))

    rolls = []
    while len(rolls) < num_rolls:
        rolls.append(random.randint(1, dice))

    if num_rolls == 1:
        message_text += 'Roll using a D{:.0f} dice: '.format(dice)
    else:
        message_text += 'Rolls using a D{:.0f} dice: '.format(dice)

    for roll in rolls[0:-1]:
        message_text += ' {:.0f}, '.format(roll)

    message_text += ' {:.0f}'.format(rolls[-1])

    await client.send_message(message.channel, message_text)


@client.event
async def on_message(message):
    if message.content.strip().startswith('/roll'):
        await process_roll(message)


async def heart_beat():
    await client.wait_until_ready()

    channel = client.get_channel(config['heart beat']['channel'])

    while True:
        # Look for existing heart beat messages
        async for message in client.logs_from(channel, limit=sys.maxsize):
            if message.author.id == client.connection.user.id:
                await client.delete_message(message)

        message_text = 'Heart Beat: ' + datetime.strftime(datetime.now(),
                                                          '%Y-%m-%d %H:%M:%S')
        await client.send_message(channel, message_text)

        await asyncio.sleep(int(config['heart beat']['channel']))


def main():
    loop = asyncio.get_event_loop()
    heart_beat_task = asyncio.ensure_future(heart_beat())

    try:
        loop.run_until_complete(bot_login())
    except Exception as e:
        logger.exception(e)
    finally:
        heart_beat_task.cancel()
        loop.run_until_complete(client.logout())
        loop.close()

    logger.exception('The program is terminating')


if __name__ == '__main__':
    # Setup logging
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='test_bot.log', encoding='utf-8',
                                  mode='a')
    handler.setFormatter(
        logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    load_config('config.ini')

    main()
