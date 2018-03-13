import os
import random


async def process_roll(client, message, max_rolls, max_dice_size):
    data = message.content.strip().split()

    dice = 6  # default dice size
    num_rolls = 1  # default number of rolls
    message_text = '{!s}\n'.format(message.author.mention)

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
            await client.send_message(message.channel, message_text)
            return

    # Valid the user input and provide feedback if necessary
    if num_rolls <= 0 or num_rolls > max_rolls:
        message_text += 'The number of rolls specified must be greater ' \
                        'than 0 and less than {:.0f}.' \
            .format(max_rolls + 1)
        await client.send_message(message.channel, message_text)
        return

    if dice < 2 or dice > max_dice_size:
        message_text += 'The dice size specified must be greater than 1 ' \
                        'and less than {:.0f}.'.format(max_dice_size + 1)
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
