# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
import sys

import discord


async def adjust_nicknames(bot, instigating_member):
    """
    Adjusts the nicknames of all server members to adhere to the bracketed ID
    rules.

    :param GnomieHomie bot: Current bot object
    :param discord.Member instigating_member: Member that triggered this call
    :return: None
    """

    members_data = []

    for member in bot.server.members:
        # Skip the bot
        if bot.client.connection.user == member:
            continue

        # Skip inactive players
        if member not in bot.active_players:
            continue

        name = member.nick if member.nick is not None else member.name

        name = await get_valid_name(name)

        number = await get_number(name)

        members_data.append((member, name, number, member != bot.server.owner,
                             member == instigating_member))

    # We add an additional boolean field here which is True if the member is
    # not the server owner. This ensures that the server owner is given ID
    # priority (e.g. sorted first) in the member list. Bot's cannot change the
    # owner's ID, so this field ensures the owner's ID will almost never need
    # to change.
    members_data = sorted(members_data,
                          key=lambda member_data: (member_data[2],
                                                   member_data[3],
                                                   member_data[4]))

    correct_id = 1
    for (member, name, current_id, owner, trig_mem) in members_data:
        if current_id != correct_id:
            new_nick = name[0:name.find('[')].strip() \
                       + ' [{:.0f}]'.format(correct_id)
            try:
                await bot.client.change_nickname(member, new_nick)
                correct_id += 1
            except discord.Forbidden:
                continue
        else:
            correct_id += 1


async def get_valid_name(name):
    """
    Parses the input name and returns a valid name according to the ID rules.

    :param str name: Member name
    :return: str
    """

    name = name.strip()

    while True:
        pos_end = name.rfind(']')
        match = re.search(r'\[(\d+)\]', name)

        # There is a number in brackets but not at the end
        if match and pos_end != len(name) - 1:
            index = name.find(match.group(1))
            name = name[0:index - 1] + name[index + len(match.group(1)) + 1:]
        else:
            break

    return name


async def get_number(name):
    """
    Parses the input name and extracts the ID or returns sys.maxsize if there
    was no ID.

    :param str name: Member name
    :return: int
    """

    match = re.search(r'\[(\d+)\]', name)

    # There is a number in brackets but not at the end
    if match:
        return int(match.group(1))
    else:
        return sys.maxsize
