import logging
import re
import sys

import discord


async def adjust_nicknames(client, server, _):
    """
    :param discord.Client client:
    :param discord.Server server:
    :param discord.Member _:
    :return:
    """

    members = []

    for mem in server.members:
        if mem.nick is not None:
            name = mem.nick
        else:
            name = mem.name

        name = await get_valid_name(name)

        number = await get_number(name)

        members.append((mem, name, number))

    members = sorted(members, key=lambda x: x[2])

    number = 1
    for (mem, name, num) in members:
        if num != number:
            new_nick = name[0:name.find('[')] + ' [{:.0f}]'.format(number)
            try:
                await client.change_nickname(mem, new_nick)
                number += 1
            except discord.Forbidden:
                continue
        else:
            number += 1


async def get_valid_name(name):
    """
    :param str name:
    :return:
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
    :param str name:
    :return:
    """

    match = re.search(r'\[(\d+)\]', name)

    # There is a number in brackets but not at the end
    if match:
        return int(match.group(1))
    else:
        return sys.maxsize
