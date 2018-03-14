# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
from datetime import datetime

import discord


async def get_active_players(bot, start_date=datetime(1970, 1, 1)):
    """
    Returns a list of active users and list of inactive users. Active users are
    users who have made at least one post since the start of the game.

    :param GnomieHomie bot: Current bot object
    :param datetime start_date: Starting date for the game
    :return: set(discord.Member)
    """

    active_users = set()

    for channel in bot.server.channels:
        async for message in bot.client.logs_from(channel, limit=sys.maxsize,
                                                  after=start_date):
            if message.author in bot.server.members:
                active_users.add(message.author)

    return active_users


async def print_active_players(bot, channel):
    """
    Prints a list of the active players in the specified channel

    :param GnomieHomie bot: Current bot object
    :param discord.Channel channel: Channel to post in
    :return: None
    """

    message_text = 'These are the current players:\n'

    for member in bot.active_players:
        name = member.nick if member.nick is not None else member.name
        message_text += name + '\n'

    await bot.client.send_message(channel, message_text)

