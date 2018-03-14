# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
from datetime import datetime

import discord


async def get_active_players(client, start_date=datetime(1970, 1, 1)):
    """
    Returns a list of active users and list of inactive users. Active users are
    users who have made at least one post since the start of the game.

    :param discord.Client client: Current client object
    :param datetime start_date: Starting date for the game
    :return: set(discord.Member)
    """

    active_users = set()

    for channel in client.get_all_channels():
        async for message in client.logs_from(channel, limit=sys.maxsize,
                                              after=start_date):
            active_users.add(message.author)

    return active_users
