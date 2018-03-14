# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import configparser
import logging
from asyncio import Lock
from datetime import datetime

import discord

import members
from dice_roles import process_roll
from nicknames import adjust_nicknames, valid_nick_change


class GnomieHomie:
    def __init__(self, config_path='config.ini'):
        self.client = discord.Client()
        self.config = configparser.ConfigParser()

        self.load_config(config_path)
        self.config_path = config_path
        self.server = None
        self.active_players = set()
        self.nick_lock = Lock()

        @self.client.event
        async def on_ready():
            print('Logged in as')
            print(self.client.user.name)
            print(self.client.user.id)
            print('------')
            self.server = self.client.get_server(
                self.config['server']['server id'])
            await self.update_active_players()
            print('Updated active players')

        @self.client.event
        async def on_member_join(member):
            await adjust_nicknames(self, member)

        @self.client.event
        async def on_member_remove(member):
            await self.update_active_players()
            await adjust_nicknames(self, member)

        @self.client.event
        async def on_member_update(member_old, member_new):
            if await valid_nick_change(self, member_old, member_new):
                await self.nick_lock.acquire()
                await adjust_nicknames(self, member_new)
                self.nick_lock.release()
            else:
                try:
                    await self.nick_lock.acquire()
                    await self.client.change_nickname(member_new,
                                                      member_old.nick)
                except discord.Forbidden:
                    pass
                finally:
                    self.nick_lock.release()

        @self.client.event
        async def on_message(message):
            if message.author not in self.active_players:
                await self.update_active_players()
                await adjust_nicknames(self, message.author)

            if message.content.strip().startswith('/roll'):
                max_rolls = self.config.getint('dice rolls',
                                               'max number of rolls')
                max_dice_size = self.config.getint('dice rolls',
                                                   'max dice size')
                await process_roll(self.client, message, max_rolls,
                                   max_dice_size)

            if message.content.strip().startswith('/active_players'):
                await members.print_active_players(self, message.channel)

    async def update_active_players(self):
        start_date = datetime.strptime(self.config['game']['start date'],
                                       '%Y-%m-%d')
        self.active_players = await members.get_active_players(self,
                                                               start_date)

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
        self.config['server'] = {'server id': ''}
        self.config['dice rolls'] = {'max dice size': '100',
                                     'max number of rolls': '10'}
        self.config['game'] = {'start date': '1970-01-01'}

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


def main():
    gnomie_bot = GnomieHomie()
    gnomie_bot.run()


if __name__ == '__main__':
    # Setup logging
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='gnomie_homie.log',
                                  encoding='utf-8',
                                  mode='a')
    handler.setFormatter(
        logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    main()
