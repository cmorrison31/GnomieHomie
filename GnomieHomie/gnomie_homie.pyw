# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import configparser
import logging
import os
import random
from datetime import datetime

import discord


class GnomieHomie:
    def __init__(self, config_path='config.ini'):
        self.client = discord.Client()
        self.config = configparser.ConfigParser()

        self.load_config(config_path)
        self.config_path = config_path

        @self.client.event
        async def on_ready():
            print('Logged in as')
            print(self.client.user.name)
            print(self.client.user.id)
            print('------')

        @self.client.event
        async def on_message(message):
            if message.content.strip().startswith('/roll'):
                await self.process_roll(message)

    def run(self):
        loop = asyncio.get_event_loop()
        heart_beat_task = asyncio.ensure_future(self.heart_beat())

        try:
            loop.run_until_complete(self.bot_login())
        except Exception as e:
            logger.exception(e)
        finally:
            heart_beat_task.cancel()
            loop.run_until_complete(self.client.logout())
            loop.close()
            self.config.write(self.config_path)

        logger.exception('The bot is terminating.')

    async def bot_login(self):
        key = self.config['credentials']['key']
        await self.client.login(key)
        await self.client.connect()

    def load_config(self, config_file_path):
        # Set default values
        self.config['heart beat'] = {'message id': '', 'channel': '',
                                     'time': '3600'}
        self.config['credentials'] = {'key': ''}
        self.config['dice rolls'] = {'max dice size': '100',
                                     'max number of rolls': '10'}

        # Load and parse the actual config file
        self.config.read(config_file_path)

    async def heart_beat(self):
        await self.client.wait_until_ready()

        channel = self.client.get_channel(self.config['heart beat']['channel'])

        message_id = self.config['heart beat']['message id']

        while True:
            message_text = 'Heart Beat: ' + \
                           datetime.strftime(datetime.utcnow(),
                                             '%Y-%m-%d %H:%M:%S UTC')

            # If we don't have an existing ID we need to create a new message
            if len(message_id) == 0:
                message = await self.client.send_message(channel, message_text)
                message_id = message.id
                self.config['heart beat']['message id'] = message_id
            else:
                try:
                    message = await self.client.get_message(channel,
                                                            message_id)
                except (discord.NotFound, discord.Forbidden):
                    # Either the ID is wrong or we don't have permission for
                    # message ID we were passed. Either way we restart the
                    # loop with a bland ID to trigger creating a new message
                    message_id = ''
                    continue

                await self.client.edit_message(message, message_text)

            await asyncio.sleep(int(self.config['heart beat']['time']))

    async def process_roll(self, message):
        data = message.content.strip().split()

        dice = 6  # default dice size
        num_rolls = 1  # default number of rolls
        message_text = '{!s}\n'.format(message.author.mention)

        max_rolls = self.config.getint('dice rolls', 'max number of rolls')
        max_dice_size = self.config.getint('dice rolls', 'max dice size')

        # If user supplied data exits, parse it and try to get the dice size
        # and number of requested rolls
        if len(data) > 1:
            try:
                for arg in data[1:]:
                    if arg.lower().startswith('d'):
                        dice = int(arg[1:])
                    else:
                        num_rolls = int(arg)
            except ValueError:
                message_text += 'Invalid /roll command format.\nThe correct ' \
                                'format is: /roll [*d*size] ' \
                                '[number of rolls]\nExample: /roll d20 3'
                await self.client.send_message(message.channel, message_text)
                return

        # Valid the user input and provide feedback if necessary
        if num_rolls <= 0 or num_rolls > max_rolls:
            message_text += 'The number of rolls specified must be greater ' \
                            'than 0 and less than {:.0f}.'\
                .format(max_rolls + 1)
            await self.client.send_message(message.channel, message_text)
            return

        if dice < 2 or dice > max_dice_size:
            message_text += 'The dice size specified must be greater than 1 ' \
                            'and less than {:.0f}.'.format(max_dice_size + 1)
            await self.client.send_message(message.channel, message_text)
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

        await self.client.send_message(message.channel, message_text)


def main():
    gnomie_bot = GnomieHomie()
    gnomie_bot.run()


if __name__ == '__main__':
    # Setup logging
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='gnomie_homie.log', encoding='utf-8',
                                  mode='a')
    handler.setFormatter(
        logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    main()
