import random
import re
import yaml
import time

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import telegram
from pymongo import MongoClient

from keyboards import main_keyboard, num_keyboard, menu_keyboard, manual_keyboard

with open(r'./params.yaml') as file:
    props = yaml.load(file, Loader=yaml.FullLoader)
    token = props['token']
    mongo = props['mongo']
    mongo_port = props['mongo_port']

updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher
client = MongoClient(mongo, mongo_port)
db = client.user_database
collection = db.user_data_collection

parameters_db = db.parameters
sub_param_db = db.sub_param
int_command = ''


def rand_sleep():
    rand_sleep = random.uniform(0.3, 1)
    return rand_sleep


def info(update, context):
    info_message = '''
Thats my boring bot, based on star trek text rpg from 1971.
https://github.com/SimonBorin/trek_bot/
@blooomberg
'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=info_message)
    time.sleep(rand_sleep())


def manual(update, context):
    msg = 'https://github.com/SimonBorin/trek_bot/wiki/Manual'
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
    time.sleep(rand_sleep())


def start_game(update, context):
    # main()
    query = update.callback_query
    blurb_msg = blurb()
    # Set up a random stardate
    stardate = round(float(random.randrange(1000, 1500, 1)), 2)
    # Enterprise starts with 3,000 units of energy, 15 torpedoes and 1,000
    # units of energy in its shields
    energy = 3000
    torpedoes = 15
    shields = 0
    # No klingons around ... yet!
    klingons = 0

    # The galaxy is divided into 64 sectors. Each sector is represented by one
    # element in the galaxy list. The galaxy list contains a three digit number
    # Hundreds = number of klingons in the sector
    # Tens = number of starbases
    # Units = number of stars
    galaxy = []
    # Initialise the galaxy list
    for i in range(0, 64):
        x = y = 0
        z = random.randint(1, 5)
        if random.randint(1, 10) < 8:
            x = random.randint(1, 3)
        if random.randint(1, 100) > 88:
            y = 1
        # galaxy.append(x * 100 + y * 10 + z)
        galaxy.append([x] + [y] + [z])
        # Keep a record of how many klingons are left to be destroyed
        klingons = klingons + x

    # Choose the starting sector and position for the Enterprise
    sector = random.randint(0, 63)
    ent_position = random.randint(0, 63)
    # Set up current sector and decode it
    # x = klingons; y = starbases; z = stars
    x = galaxy[sector][0]
    y = galaxy[sector][1]
    z = galaxy[sector][2]
    # x, y, z = decode(galaxy[sector])
    # Set up the current sector map
    # Each sector has 64 positions in which a klingon, starbase, star 
    # or the Enterprise may be located in
    current_sector = init(x, y, z, ent_position)
    # Perform a short range scan
    condition, srs_map = srs(current_sector, ent_position)
    status_msg = status(sector, stardate, condition, energy, torpedoes, shields, klingons)
    # Keep going until we have destroyed all the klingons or we run out of
    # energy or we quit
    chat_id = update.effective_chat.id
    username = update.effective_chat.username
    first_name = update.effective_chat.first_name
    last_name = update.effective_chat.last_name
    parameters4db = {'_id': chat_id, 'username': username, 'first_name': first_name, 'last_name': last_name,
                     'galaxy': galaxy, 'klingons': klingons, 'energy': energy, 'torpedoes': torpedoes,
                     'shields': shields, 'stardate': stardate, 'sector': sector,
                     'ent_position': ent_position, 'attack_msg_out': '',
                     'x': x, 'y': y, 'z': z, 'current_sector': current_sector, 'condition': condition,
                     'wrap': 0, 'helm': 0, 'srs_map': srs_map, 'status_msg': status_msg}
    sub_param4db = {'_id': chat_id, 'shields_flag': 0, 'helm': 0, 'phasers_flag': 0, 'lrs_flag': 0, 'helm': 0,
                    'wrap': 0, 'torpedoes': 0}
    try:
        parameters_db.update_one({'_id': chat_id}, {"$set": parameters4db}, upsert=True)
        sub_param_db.update_one({'_id': chat_id}, {"$set": sub_param4db}, upsert=True)
    except Exception as e:
        print('error mongo! chat_id = ', chat_id, '\nerror = ', e)
    out_msg = '''
Space ... the final frontier.
These are the voyages of the starship Enterprise
Its five year mission ... 
... to boldly go where no-one has gone before
You are Captain Kirk.
Your mission is to destroy all of the Klingons in the galaxy.
    '''
    # context.bot.send_message(chat_id=update.effective_chat.id, text='-==StarTrek==-\n', parse_mode=telegram.ParseMode.MARKDOWN)
    out_letter = ''
    context.bot.send_message(chat_id=update.effective_chat.id, text=blurb_msg, parse_mode=telegram.ParseMode.MARKDOWN)
    time.sleep(rand_sleep())
    start_msg = srs_map + status_msg
                # + main_message()
    # context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map, parse_mode=telegram.ParseMode.MARKDOWN)
    # time.sleep(rand_sleep())
    # context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg, parse_mode=telegram.ParseMode.MARKDOWN)
    # time.sleep(rand_sleep())
    # context.bot.send_message(chat_id=update.effective_chat.id, text=' ``` \nCommand (1-6, 0 for help)?  ``` ',
    #                          parse_mode=telegram.ParseMode.MARKDOWN)
    update.message.reply_text(main_message(start_msg),
                              reply_markup=main_keyboard(),
                              parse_mode=telegram.ParseMode.MARKDOWN)
    # for i in out_msg:
    #     out_letter += i
    #
    #     context.bot.edit_message_text(chat_id=update.effective_chat.id,
    #                                   message_id=query.message.message_id,
    #                                   text=f'```{out_letter}```',
    #                                   reply_markup=main_keyboard(),
    #                                   parse_mode=telegram.ParseMode.MARKDOWN)


def bot_help(update, context):
    help_msg = showhelp()
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_msg, parse_mode=telegram.ParseMode.MARKDOWN)
    time.sleep(rand_sleep())
    context.bot.send_message(chat_id=update.effective_chat.id, text=' ``` \nCommand (1-6, 0 for help)?  ``` ',
                             parse_mode=telegram.ParseMode.MARKDOWN)


def bot_helm(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'helm': 1}}, upsert=True)

    context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCourse direction(1-4,5-9)? ```',
                             parse_mode=telegram.ParseMode.MARKDOWN)
    update.message.reply_text(main_message(),
                              reply_markup=main_keyboard())


def bot_lrs(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    params = parameters_db.find_one({'_id': chat_id})
    sector = params['sector']
    galaxy = params['galaxy']
    # sector = params['sector']
    # galaxy = params['galaxy']
    lrs_out = lrs(galaxy, sector)
    # context.bot.send_message(chat_id=update.effective_chat.id, text=lrs_out, parse_mode=telegram.ParseMode.MARKDOWN)
    # time.sleep(rand_sleep())
    # context.bot.send_message(chat_id=update.effective_chat.id, text=' ``` \nCommand (1-6, 0 for help)?  ``` ',
    #                          parse_mode=telegram.ParseMode.MARKDOWN)
    # update.message.reply_text(main_message(),
    #                           reply_markup=main_keyboard())
    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=update.callback_query.message.message_id,
                                  text=main_message(lrs_out), reply_markup=main_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def bot_srs(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    params = parameters_db.find_one({'_id': chat_id})
    params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
    params['status_msg'] = status(params['sector'], params['stardate'], params['condition'], params['energy'],
                                  params['torpedoes'],
                                  params['shields'], params['klingons'])
    srs_ = f"{params['srs_map']}\n{params['status_msg']}"
    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=update.callback_query.message.message_id,
                                  text=main_message(srs_), reply_markup=main_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def bot_phasers(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'phasers_flag': 1}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text=' ``` \nPhaser energy? ``` ',
                             parse_mode=telegram.ParseMode.MARKDOWN)


def bot_torpedoes(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'torpedoes': 1}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nFire in direction(1-4,6-9)? ```',
                             parse_mode=telegram.ParseMode.MARKDOWN)


def bot_shields(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'shields_flag': 1}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text=' ``` \nEnergy to shields? ``` ',
                             parse_mode=telegram.ParseMode.MARKDOWN)


def bot_resign(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=' ``` \nStarting new game ``` ',
                             parse_mode=telegram.ParseMode.MARKDOWN)
    # params['energy'] = 0
    start_game(update, context)


def bot_sub_command(update, context):
    chat_id = update.effective_chat.id
    bot_sub_command_ = update.message.text

    params = parameters_db.find_one({'_id': chat_id})
    klingons = params['klingons']
    energy = params['energy']
    torpedoes = params['torpedoes']
    shields = params['shields']
    stardate = params['stardate']
    sector = params['sector']
    ent_position = params['ent_position']
    galaxy = params['galaxy']
    x = params['x']
    y = params['y']
    z = params['z']
    current_sector = params['current_sector']
    condition = params['condition']

    sub_params = sub_param_db.find_one({'_id': chat_id})

    pattern = re.compile("^\d*$")
    if pattern.match(bot_sub_command_):
        if sub_params['shields_flag'] == 1:
            a = 1
        #     energy, shields = addshields(energy, shields, bot_sub_command_)
        #     params['energy'] = energy
        #     params['shields'] = shields
        #     condition, srs_map = srs(current_sector, ent_position)
        #     params['condition'] = condition
        #     # params['srs_map'] = srs_map
        #     status_msg = status(sector, stardate, condition, energy, torpedoes, shields, klingons)
        #
        #     context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,
        #                              parse_mode=telegram.ParseMode.MARKDOWN)
        #     time.sleep(rand_sleep())
        #     context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,
        #                              parse_mode=telegram.ParseMode.MARKDOWN)
        #     time.sleep(rand_sleep())
        #     sub_params['shields_flag'] = 0
        #     parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
        #     sub_param_db.update_one({'_id': chat_id}, {"$set": sub_params}, upsert=True)
        #     params['attack_msg_out'] = atack(update, context)
        #     if not params['attack_msg_out']:
        #         context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand (1-6, 0 for help)? ```',
        #                                  parse_mode=telegram.ParseMode.MARKDOWN)

        # elif sub_params['phasers_flag'] == 1:
        #     shields, energy, current_sector, ks, message = phasers(condition, shields, energy, current_sector,
        #                                                            ent_position, x, bot_sub_command_)
        #     params['shields'] = shields
        #     params['energy'] = energy
        #     params['current_sector'] = current_sector
        #     context.bot.send_message(chat_id=update.effective_chat.id, text=message,
        #                              parse_mode=telegram.ParseMode.MARKDOWN)
        #     if ks < x:
        #         # (x-ks) Klingons have been destroyed-update galaxy map
        #         # galaxy[sector] = galaxy[sector] - (100 * (x - ks))
        #         galaxy[sector][0] = galaxy[sector][0] - (x - ks)
        #         params['galaxy'] = galaxy
        #         # update total klingons
        #         klingons = klingons - (x - ks)
        #         params['klingons'] = klingons
        #         # update sector klingons
        #         x = ks
        #         params['x'] = x
        #     # Do we still have shields left?
        #     if shields < 0:
        #         energy = 0
        #         params['energy'] = energy
        #         context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nEnterprise dead in space ```',
        #                                  parse_mode=telegram.ParseMode.MARKDOWN)
        #         time.sleep(rand_sleep())
        #     else:
        #         condition, srs_map = srs(current_sector, ent_position)
        #         params['condition'] = condition
        #         status_msg = status(sector, stardate, condition, energy, torpedoes, shields, klingons)
        #         context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,
        #                                  parse_mode=telegram.ParseMode.MARKDOWN)
        #         time.sleep(rand_sleep())
        #         context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,
        #                                  parse_mode=telegram.ParseMode.MARKDOWN)
        #         time.sleep(rand_sleep())
        #         context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand (1-6, 0 for help)? ```',
        #                                  parse_mode=telegram.ParseMode.MARKDOWN)
        #         time.sleep(rand_sleep())
        #     sub_params['phasers_flag'] = 0
        #     parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
        #     sub_param_db.update_one({'_id': chat_id}, {"$set": sub_params}, upsert=True)
        #     params['attack_msg_out'] = attack(update, context)
        #


        elif sub_params['helm'] == 1:
            sub_params['wrap'] = 1
            params['helm'] = int(bot_sub_command_)
            sub_params['helm'] = 0
            context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nWarp (1-63)? ```',
                                     parse_mode=telegram.ParseMode.MARKDOWN)
            parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
            sub_param_db.update_one({'_id': chat_id}, {"$set": sub_params}, upsert=True)

        elif sub_params['wrap'] == 1:
            a = 1
            # wrap_ = int(bot_sub_command_)
            # helm_ = params['helm']
            # new_sector, energy, ent_position, stardate, msg = helm(galaxy, sector, energy, current_sector, ent_position,
            #                                                        stardate, helm_, wrap_)
            # context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)
            # time.sleep(rand_sleep())
            # # If we're still in the same sector as before, draw the Enterprise
            # params['energy'] = energy
            # params['ent_position'] = ent_position
            # params['stardate'] = stardate
            # if sector == new_sector:
            #     current_sector[ent_position] = 4
            # else:
            #     # Else set up the Enterprise in the new sector
            #     sector = new_sector
            #     ent_position = random.randint(0, 63)
            #     # x, y, z = decode(galaxy[sector])
            #     x = galaxy[sector][0]
            #     y = galaxy[sector][1]
            #     z = galaxy[sector][2]
            #     current_sector = init(x, y, z, ent_position)
            #     params['current_sector'] = current_sector
            #     params['sector'] = sector
            #     params['ent_position'] = ent_position
            #     params['x'] = x
            #     params['y'] = y
            #     params['z'] = z
            # # Perform a short range scan after every movement
            # condition, srs_map = srs(current_sector, ent_position)
            # context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,
            #                          parse_mode=telegram.ParseMode.MARKDOWN)
            # time.sleep(rand_sleep())
            # params['condition'] = condition
            # if condition == "Docked":
            #     # Reset energy, torpedoes and shields
            #     energy = 3000
            #     torpedoes = 15
            #     shields = 0
            # status_msg = status(sector, stardate, condition, energy, torpedoes, shields, klingons)
            # context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,
            #                          parse_mode=telegram.ParseMode.MARKDOWN)
            # time.sleep(rand_sleep())
            # sub_params['wrap'] = 0
            # parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
            # sub_param_db.update_one({'_id': chat_id}, {"$set": sub_params}, upsert=True)
            # params['attack_msg_out'] = atack(update, context)
            # if not params['attack_msg_out']:
            #     context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand (1-6, 0 for help)? ```',
            #                              parse_mode=telegram.ParseMode.MARKDOWN)
            # time.sleep(rand_sleep())


        # elif sub_params['torpedoes'] == 1:
        #     direction = int(bot_sub_command_)
        #     torpedoes, current_sector, ks, msg = photontorpedoes(torpedoes, current_sector, ent_position, x, direction)
        #     params['torpedoes'] = torpedoes
        #     params['current_sector'] = current_sector
        #     # A Klingon has been destroyed-update galaxy map
        #     if ks < x:
        #         # galaxy[sector] = galaxy[sector] - 100
        #         galaxy[sector][0] = galaxy[sector][0] - 1
        #         # update total klingons
        #         klingons = klingons - (x - ks)
        #         # update sector klingons
        #         x = ks
        #         params['galaxy'] = galaxy
        #         params['klingons'] = klingons
        #         params['x'] = x
        #     condition, srs_map = srs(current_sector, ent_position)
        #     status_msg = status(sector, stardate, condition, energy, torpedoes, shields, klingons)
        #     params['condition'] = condition
        #     context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)
        #     time.sleep(rand_sleep())
        #     context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,
        #                              parse_mode=telegram.ParseMode.MARKDOWN)
        #     time.sleep(rand_sleep())
        #     context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,
        #                              parse_mode=telegram.ParseMode.MARKDOWN)
        #     time.sleep(rand_sleep())
        #     sub_params['torpedoes'] = 0
        #     parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
        #     sub_param_db.update_one({'_id': chat_id}, {"$set": sub_params}, upsert=True)
        #     params['attack_msg_out'] = attack(update, context)
        #     if not params['attack_msg_out']:
        #         context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand (1-6, 0 for help)? ```',
        #                                  parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand not recognised captain ``` ',
                                     parse_mode=telegram.ParseMode.MARKDOWN)

    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand not recognised captain ``` ',
                                 parse_mode=telegram.ParseMode.MARKDOWN)

    if params['energy'] == 0:
        over_msg = ' ```\nGame Over!\nStarting new game ```'
        lose_msg = lose()
        context.bot.send_message(chat_id=update.effective_chat.id, text=lose_msg,
                                 parse_mode=telegram.ParseMode.MARKDOWN)
        time.sleep(rand_sleep())
        context.bot.send_message(chat_id=update.effective_chat.id, text=over_msg,
                                 parse_mode=telegram.ParseMode.MARKDOWN)
        time.sleep(rand_sleep())
        start_game(update, context)
    elif params['energy'] != 0 and params['klingons'] <= 0:
        prom_msg = promotion()
        context.bot.send_message(chat_id=update.effective_chat.id, text=prom_msg,
                                 parse_mode=telegram.ParseMode.MARKDOWN)
        start_game(update, context)


def shields_button(update, context):
    chat_id = update.effective_chat.id
    msg = 'Energy to the shields:'
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'shields_flag': 1}}, upsert=True)
    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=update.callback_query.message.message_id,
                                  text=main_message(msg), reply_markup=num_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def shields_compute(update, context, input):
    chat_id = update.effective_chat.id
    params = parameters_db.find_one({'_id': chat_id})
    sub_params = sub_param_db.find_one({'_id': chat_id})
    params['energy'], params['shields'] = addshields(params['energy'], params['shields'], input)
    params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
    params['status_msg'] = status(params['sector'], params['stardate'], params['condition'], params['energy'],
                                  params['torpedoes'],
                                  params['shields'], params['klingons'])

    sub_params['shields_flag'] = 0
    parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
    sub_param_db.update_one({'_id': chat_id}, {"$set": sub_params}, upsert=True)

    params['attack_msg_out'] = attack(update, context)


def phasers_compute(update, context, input):
    chat_id = update.effective_chat.id
    params = parameters_db.find_one({'_id': chat_id})
    sub_params = sub_param_db.find_one({'_id': chat_id})

    params['shields'], params['energy'], params['current_sector'], params['ks'], params['message'] = \
        phasers(params['condition'], params['shields'], params['energy'], params['current_sector'],
                params['ent_position'], params['x'], input)
    # context.bot.send_message(chat_id=update.effective_chat.id, text=message,
    #                          parse_mode=telegram.ParseMode.MARKDOWN)
    if params['ks'] < params['x']:
        # (x-ks) Klingons have been destroyed-update galaxy map
        # galaxy[sector] = galaxy[sector] - (100 * (x - ks))
        params['galaxy'][params['sector']][0] = params['galaxy'][params['sector']][0] - (params['x'] - params['ks'])
        # update total klingons
        params['klingons'] = params['klingons'] - (params['x'] - params['ks'])
        # update sector klingons
        params['x'] = params['ks']
    # Do we still have shields left?
    if params['shields'] < 0:
        params['energy'] = 0
        # context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nEnterprise dead in space ```',
        #                          parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
        params['status_msg'] = status(params['sector'], params['stardate'], params['condition'], params['energy'],
                                      params['torpedoes'], params['shields'], params['klingons'])
        # context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,
        #                          parse_mode=telegram.ParseMode.MARKDOWN)
        # time.sleep(rand_sleep())
        # context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,
        #                          parse_mode=telegram.ParseMode.MARKDOWN)
        # time.sleep(rand_sleep())
        # context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand (1-6, 0 for help)? ```',
        #                          parse_mode=telegram.ParseMode.MARKDOWN)
    parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
    sub_param_db.update_one({'_id': chat_id}, {"$set": sub_params}, upsert=True)
    params['attack_msg_out'] = attack(update, context)
    # if params['attack_msg_out'] == False:
    #     context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand (1-6, 0 for help)? ```',
    #                              parse_mode=telegram.ParseMode.MARKDOWN)


def torpedoes_compute(update, context, input):
    chat_id = update.effective_chat.id
    params = parameters_db.find_one({'_id': chat_id})
    direction = input
    params['torpedoes'], params['current_sector'], params['ks'], params['msg'] = \
        photontorpedoes(params['torpedoes'], params['current_sector'], params['ent_position'], params['x'], direction)
    # A Klingon has been destroyed-update galaxy map
    if params['ks'] < params['x']:
        # galaxy[sector] = galaxy[sector] - 100
        params['galaxy'][params['sector']][0] = params['galaxy'][params['sector']][0] - 1
        # update total klingons
        params['klingons'] = params['klingons'] - (params['x'] - params['ks'])
        # update sector klingons
        params['x'] = params['ks']
    params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
    params['status_msg'] = status(params['sector'], params['stardate'], params['condition'], params['energy'],
                                  params['torpedoes'], params['shields'], params['klingons'])
    # context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)
    # time.sleep(rand_sleep())
    # context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,
    #                          parse_mode=telegram.ParseMode.MARKDOWN)
    # time.sleep(rand_sleep())
    # context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,
    #                          parse_mode=telegram.ParseMode.MARKDOWN)
    # time.sleep(rand_sleep())
    parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
    # sub_param_db.update_one({'_id': chat_id}, {"$set": sub_params}, upsert=True)
    params['attack_msg_out'] = attack(update, context)
    # if not flag_attack:
    #     context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand (1-6, 0 for help)? ```',
    #                              parse_mode=telegram.ParseMode.MARKDOWN)


def helm_out(update, context):
    chat_id = update.effective_chat.id
    params = parameters_db.find_one({'_id': chat_id})
    new_sector, energy, ent_position, stardate, msg = helm(params['galaxy'], params['sector'], params['energy'],
                                                           params['current_sector'], params['ent_position'],
                                                           params['stardate'], params['helm'], params['wrap'])
    # If we're still in the same sector as before, draw the Enterprise
    params['energy'] = energy
    params['ent_position'] = ent_position
    params['stardate'] = stardate
    if params['sector'] == new_sector:
        params['current_sector'][ent_position] = 4
    else:
        # Else set up the Enterprise in the new sector
        sector = new_sector
        ent_position = random.randint(0, 63)
        # x, y, z = decode(galaxy[sector])
        x = params['galaxy'][sector][0]
        y = params['galaxy'][sector][1]
        z = params['galaxy'][sector][2]
        current_sector = init(x, y, z, ent_position)
        params['current_sector'] = current_sector
        params['sector'] = sector
        params['ent_position'] = ent_position
        params['x'] = x
        params['y'] = y
        params['z'] = z
    # Perform a short range scan after every movement
    condition, srs_map = srs(params['current_sector'], params['ent_position'])
    # context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,
    #                          parse_mode=telegram.ParseMode.MARKDOWN)
    # time.sleep(rand_sleep())
    params['condition'] = condition
    if condition == "Docked":
        # Reset energy, torpedoes and shields
        params['energy'] = 3000
        params['torpedoes'] = 15
        params['shields'] = 0
    params['status_msg'] = status(params['sector'], params['stardate'], params['condition'], params['energy'],
                                  params['torpedoes'], params['shields'], params['klingons'])
    # context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,
    #                          parse_mode=telegram.ParseMode.MARKDOWN)
    # time.sleep(rand_sleep())
    parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
    params['attack_msg_out'] = attack(update, context)

    srs_msg = f"{params['srs_map']}\n{params['status_msg']}"
    # context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=update.callback_query.message.message_id,
    #                               text=main_message(srs_msg), reply_markup=main_keyboard(),
    #                               parse_mode=telegram.ParseMode.MARKDOWN)


def attack(update, context):
    chat_id = update.effective_chat.id
    params = parameters_db.find_one({'_id': chat_id})

    condition = params['condition']
    x = params['x']
    current_sector = params['current_sector']
    ent_position = params['ent_position']
    stardate = params['stardate']
    sector = params['sector']
    shields = params['shields']
    torpedoes = params['torpedoes']
    klingons = params['klingons']
    energy = params['energy']
    attack = False
    attack_mag = ''
    if condition == "Red":
        if random.randint(1, 9) < 6:
            attack_mag += '``` \nRed alert - Klingons attacking!\n ```'
            # context.bot.send_message(chat_id=update.effective_chat.id, text=msg1,
            #                          parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            damage = x * random.randint(1, 50)
            shields = shields - damage
            params['shields'] = shields
            attack_mag += f'``` \nHit on shields: {damage} energy units\n ```'
            # context.bot.send_message(chat_id=update.effective_chat.id, text=msg2,
            #                          parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            # Do we still have shields left?
            if shields < 0:
                attack_mag += '``` \nEnterprise dead in space\n ```'
                # context.bot.send_message(chat_id=update.effective_chat.id, text=msg3,
                #                          parse_mode=telegram.ParseMode.MARKDOWN)
                time.sleep(rand_sleep())
                energy = 0
                attack = True
                params['energy'] = energy
            else:
                condition, srs_map = srs(current_sector, ent_position)
                params['condition'] = condition
                status_msg = status(sector, stardate, condition, energy, torpedoes, shields, klingons)
                attack_mag += srs_map
                attack_mag += status_msg
                # context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,
                #                          parse_mode=telegram.ParseMode.MARKDOWN)
                # time.sleep(rand_sleep())
                # context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,
                #                          parse_mode=telegram.ParseMode.MARKDOWN)
                time.sleep(rand_sleep())
    # context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=update.callback_query.message.message_id,
    #                               text=main_message(attack_mag), reply_markup=main_keyboard(),
    #                               parse_mode=telegram.ParseMode.MARKDOWN)
    params['attack_msg_out'] = attack_mag
    parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)


def status(sector, stardate, condition, energy, torpedoes, shields, klingons):
    status_msg = f''' ```
Stardate:           {stardate}
Condition:          {condition}
Energy:             {energy}
Photon torpedoes:   {torpedoes}
Shields:            {shields}
Klingons in galaxy: {klingons}
```
    '''
    return status_msg


def blurb():
    start_message = ''' ```
Space ... the final frontier.
These are the voyages of the starship Enterprise
Its five year mission ... 
... to boldly go where no-one has gone before
You are Captain Kirk.
Your mission is to destroy all of the Klingons in the galaxy.
```
    '''
    return start_message


def promotion():
    promotion_msg = ''' ``` 
You have successfully completed your mission!
The federation has been saved.
You have been promoted to Admiral Kirk.  
    '''
    return promotion_msg


def lose():
    lose = "```\nYou are relieved of duty. ```"
    return lose


def decode(sector):
    # Hundreds = klingons, tens = starbases, units = stars
    klingons = int(sector / 100)
    starbases = int((sector - klingons * 100) / 10)
    stars = int(sector - klingons * 100 - starbases * 10)
    return klingons, starbases, stars


def init(klingons, bases, stars, eposition):
    current_sector = []
    for j in range(0, 64):
        current_sector.append(0)
    # A value of 4 in the sector map indicates the Enterprise's position
    current_sector[eposition] = 4
    # Add in the stars (value = 3)
    while stars > 0:
        position = random.randint(0, 63)
        if current_sector[position] == 0:
            current_sector[position] = 3
            stars = stars - 1
    # Add in the starbases (value = 2)
    while bases > 0:
        position = random.randint(0, 63)
        if current_sector[position] == 0:
            current_sector[position] = 2
            bases = bases - 1
    # Add in the klingons (value = -200)
    while klingons > 0:
        position = random.randint(0, 63)
        if current_sector[position] == 0:
            current_sector[position] = -200
            klingons = klingons - 1
    return current_sector


def srs(current_sector, ent_pos):
    # Print out sector map
    # MapKey: >!< = Klingon
    #      <O> = Starbase
    #       *  = Star
    #      -O- = Enterprise
    klingons = False
    local_srs_map = "```"
    for i in range(0, 64):
        if i % 8 == 0:
            local_srs_map += "\n"
        if current_sector[i] < 0:
            klingons = True
            local_srs_map += ">!<"
        elif current_sector[i] == 0:
            local_srs_map += " . "
        elif current_sector[i] == 2:
            local_srs_map += "<O>"
        elif current_sector[i] == 3:
            local_srs_map += " * "
        else:
            local_srs_map += "-O-"
    # map = ''
    # Work out condition
    if klingons == False:
        condition = "Green"
    else:
        condition = "Red"
    # But docked status overrides Red/Green
    port = ent_pos - 1
    starboard = ent_pos + 1
    if port >= 0:
        if current_sector[port] == 2:
            condition = "Docked"
    if starboard <= 63:
        if current_sector[starboard] == 2:
            condition = "Docked"
    # Return condition status

    local_srs_map += "\n```"
    srs_map = local_srs_map
    return condition, srs_map


def helm(galaxy, sector, energy, cur_sec, epos, stardate, helm_, warp_):
    direction = int(helm_)
    if direction >= 1 and direction <= 9 and direction != 5:
        # Work out the horizontal and vertical co-ordinates
        # of the Enterprise in the current sector
        # 0,0 is top left and 7,7 is bottom right
        horiz = int(epos / 8)
        vert = epos - (horiz * 8)
        vert2 = int(epos - (horiz * 8))
        # And calculate the direction component of our course vector

        hinc, vinc = calcvector(direction)
        # How far do we need to move?
        warp = int(warp_)
        if warp >= 1 and warp <= 63:
            # Check there is sufficient energy
            if warp <= energy:
                # Reduce energy by warp amount
                energy = energy - warp
                # Remove Enterprise from current position
                cur_sec[epos] = 0
                # Calculate the new stardate
                stardate = round((stardate + (0.1 * warp)), 2)
                # For the moment, assume movement leaves us in original sector
                out = False
                # Move the Enterprise warp units in the specified direction
                i = 1
                while i <= warp and out == False:
                    # Calculate the movement vector
                    vert = vert + vinc
                    horiz = horiz + hinc
                    # Are we in the original sector still?
                    if vert < 0 or vert > 7 or horiz < 0 or horiz > 7:
                        out = True
                        # Calculate new sector and join ends of the galaxy
                        # sector - 1 to moove left
                        # sector + 1 to moove right
                        # sector - 8 to moove up
                        # sector + 8 to moove down
                        vert_moove_coefficient = 0
                        horiz_moove_coefficient = 0
                        if vert < 0:
                            vert_moove_coefficient = -1
                        elif vert > 7:
                            vert_moove_coefficient = 1

                        if horiz < 0:
                            horiz_moove_coefficient = -8
                        elif horiz > 7:
                            horiz_moove_coefficient = 8
                        sector = join(sector + vert_moove_coefficient + horiz_moove_coefficient)

                    else:
                        # If we are in the original sector we can't go through
                        # solid objects! So reset course postion 1 click
                        # Inefficient - does this for warp steps even if we
                        # can't move.

                        if cur_sec[vert + 8 * horiz] != 0:
                            vert = vert - vinc
                            horiz = horiz - hinc
                        # Put the Enterprise in the new position
                        epos = vert + 8 * horiz
                    i = i + 1
                    msg = '``` \nCalculateing ```'

            else:
                msg = f'``` \nToo little energy left. Only {energy} units remain\n ```'
        else:
            msg = '``` \nThe engines canna take it, captain!\n ```'
    else:
        msg = '``` \nThat`s not a direction the Enterprise can go in, captain!\n ```'
    return sector, energy, epos, stardate, msg


def lrs(galaxy, sector):
    lrs_out = '``` \n'
    for i in range(-8, 9, 8):
        for j in range(-1, 2):
            # Join the ends of the galaxy together
            sec = join(sector + j + i)
            for x in galaxy[sec]:
                lrs_out += str(x)
            lrs_out += ' '
        lrs_out += '\n'
    lrs_out += '\n ```'
    return lrs_out


def phasers(condition, shields, energy, sector, epos, ksec, bot_sub_command_):
    power = int(bot_sub_command_)
    message = '``` \n'
    if power <= energy:
        # Reduce available energy by amount directed to phaser banks
        energy = energy - power
        # Divide phaser power by number of klingons in the sector if there are
        # any present! Space can do funny things to the mind ...
        if ksec > 0:
            power = power / ksec
            # Work out the vertical and horizotal displacement of Enterprise
            horiz = epos / 8
            vert = epos - (8 * horiz)
            # Check all of the 64 positions in the sector for Klingons
            for i in range(0, 64):
                if sector[i] < 0:
                    # We have a Klingon!
                    # Work out its horizontal and vertical displacement
                    horizk = i / 8
                    vertk = i - (8 * horizk)
                    # Work out distance from Klingon to Enterprise
                    z = horiz - horizk
                    y = vert - vertk
                    dist = 1
                    while ((dist + 1) * (dist + 1)) < (z * z + y * y):
                        dist = dist + 1
                    # Klingon energy is negative, so add on the phaser power
                    # corrected for distance
                    sector[i] = sector[i] + int(power / dist)
                    if sector[i] >= 0:
                        # Set this part of space to be empty
                        sector[i] = 0
                        # Decrement sector klingons
                        ksec = int(ksec - 1)
                        message += 'Klingon destroyed!\n'
                    else:
                        # We have a hit on Enterprise's shields if not docked
                        if condition != "Docked":
                            damage = int(power / dist)
                            shields = shields - damage
                            message += f'Hit on shields: {damage} energy units\n'
    else:
        message += 'Not enough energy, Captain!'
    message += '```'
    return shields, energy, sector, ksec, message


def photontorpedoes(torpedoes, sector, epos, ksec, direction_):
    if torpedoes < 1:
        msg = '``` \nNo photon torpedoes left, captain! ```'
    else:
        direction = int(direction_)
        if 1 <= direction <= 9 and direction != 5:
            # Work out the horizontal and vertical co-ordinates
            # of the Enterprise in the current sector
            # 0,0 is top left and 7,7 is bottom right
            horiz = int(epos / 8)
            vert = int(epos - horiz * 8)
            # And calculate the direction to fire the torpedo
            hinc, vinc = calcvector(direction)
            # A torpedo only works in the current sector and stops moving
            # when we hit something solid
            out = False
            while not out:
                # Calculate the movement vector
                vert = vert + vinc
                horiz = horiz + hinc
                # Is the torpedo still in the sector?
                if vert < 0 or vert > 7 or horiz < 0 or horiz > 7:
                    out = True
                    msg = '``` \nTorpedo missed ```'
                else:
                    # Have we hit an object?
                    if sector[vert + 8 * horiz] == 2:
                        # Oh dear - taking out a starbase ends the game
                        out = True
                        sector[vert + 8 * horiz] = 0
                        energy = 0
                        msg = '``` \nStarbase destroyed ```'
                    elif sector[vert + 8 * horiz] == 3:
                        # Shooting a torpedo into a star has no effect
                        out = True
                        msg = '``` \nTorpedo missed ```'
                    elif sector[vert + 8 * horiz] < 0:
                        # Hit and destroyed a Klingon!
                        out = True
                        sector[vert + 8 * horiz] = 0
                        ksec = ksec - 1
                        msg = '``` \nKlingon destroyed! ```'
            # One fewer torpedo
            torpedoes = torpedoes - 1
        else:
            msg = '``` \nYour command is not logical, Captain. ```'
    return torpedoes, sector, ksec, msg


def addshields(energy, shields, num_input):
    # Add energy to shields
    power = int(num_input)
    if (power > 0) and (energy >= power):
        energy = energy - power
        shields = shields + power
    return energy, shields


def calcvector(direction):
    # Convert numeric keypad directions to that of the original game
    # NK 7 = 7
    # NK 4 = 6
    # NK 1 = 5
    # NK 2 = 4
    # NK 3 = 3
    # NK 6 = 2
    # NK 9 = 1
    # NK 8 = 0
    # This could be rather more elegant if I didn't bother doing this!
    # However, I'm trying to stay true to the spirit of the original
    # BASIC listing ...
    calcvector_dict = {
        7: 7,
        4: 6,
        1: 5,
        2: 4,
        3: 3,
        6: 2,
        9: 1,
        8: 0
    }
    direction = calcvector_dict[direction]
    # Work out the direction increment vector
    # hinc = horizontal increment
    # vinc = vertical increment
    if direction < 2 or direction > 6:
        hinc = -1
    elif 2 < direction < 6:
        hinc = 1
    else:
        hinc = 0
    if 4 > direction > 0:
        vinc = 1
    elif direction > 4:
        vinc = -1
    else:
        vinc = 0
    return hinc, vinc


def join(sector):
    # Join the ends of the galaxy together
    if sector < 0:
        sector = sector + 64
    if sector > 63:
        sector = sector - 63
    return sector


def showhelp():
    msg = '''
    ```
1 - Helm
2 - Long Range Scan
3 - Phasers
4 - Photon Torpedoes
5 - Shields
6 - Resign
    Manual
    Info
```
    '''
    return msg


def drop_subparams_flag(chat_id):
    sub_params = sub_param_db.find_one({'_id': chat_id})
    for i in sub_params:
        if i != '_id':
            sub_params[i] = 0
    sub_param_db.update_one({'_id': chat_id}, {"$set": sub_params}, upsert=True)


############################ menu funks #########################################
def main_menu(update, context):
    query = update.callback_query
    msg = '*Main Menu*'
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(msg),
                                  reply_markup=menu_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def phasers_button(update, context):
    chat_id = update.effective_chat.id
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'phasers_flag': 1}}, upsert=True)
    msg = f'Phaser Energy:{int_command}'
    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=update.callback_query.message.message_id,
                                  text=main_message(msg), reply_markup=num_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def torpedoes_button(update, context):
    chat_id = update.effective_chat.id
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'torpedoes': 1}}, upsert=True)
    msg = f'Fire in direction:{int_command}'
    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=update.callback_query.message.message_id,
                                  text=main_message(msg), reply_markup=num_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def back2main(update, context):
    query = update.callback_query
    drop_subparams_flag(query.message.chat_id)
    global int_command
    int_command = ''
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(),
                                  reply_markup=main_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def num_menu(update, context):
    query = update.callback_query
    print(update.callback_query.data)
    input = update.callback_query.data
    pattern = re.compile("^\d*$")
    global int_command
    if pattern.match(input):
        int_command += input
    msg = f'Your command:{int_command}'
    print(msg)
    chat_id = query.message.chat_id
    sub_params = sub_param_db.find_one({'_id': chat_id})
    params = parameters_db.find_one({'_id': chat_id})
    if sub_params['helm'] == 1:
        msg = f'Setting Helm Vector:{int_command}'
        params['helm'] = int(int_command)

    elif sub_params['wrap'] == 1:
        msg = f'Enter Wrap Coefficient:{int_command}'
        params['wrap'] = int(int_command)

    elif sub_params['shields_flag'] == 1:
        msg = f'Energy to the shields:{int_command}'
        params['input'] = int(int_command)

    elif sub_params['phasers_flag'] == 1:
        msg = f'Phaser Energy:{int_command}'
        params['input'] = int(int_command)

    elif sub_params['torpedoes'] == 1:
        msg = f'Fire in direction:{int_command}'
        params['input'] = int(int_command)

    parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)

    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(msg),
                                  reply_markup=num_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def num_command(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    params = parameters_db.find_one({'_id': chat_id})
    sub_params = sub_param_db.find_one({'_id': chat_id})
    global int_command
    if sub_params['helm'] == 1:
        msg = 'Enter Wrap Coefficient'
        keyboard = num_keyboard()
        sub_param_db.update_one({'_id': chat_id}, {"$set": {'helm': 0}}, upsert=True)
        int_command = ''

    elif sub_params['wrap'] == 1:
        keyboard = main_keyboard()
        sub_param_db.update_one({'_id': chat_id}, {"$set": {'wrap': 0}}, upsert=True)
        int_command = ''
        helm_out(update, context)
        params = parameters_db.find_one({'_id': chat_id})
        msg = params['srs_map'] + params['status_msg']

    elif sub_params['shields_flag'] == 1:
        keyboard = main_keyboard()
        sub_param_db.update_one({'_id': chat_id}, {"$set": {'shields_flag': 0}}, upsert=True)
        int_command = ''
        input = params['input']
        params['input'] = 0
        shields_compute(update, context, input)
        params = parameters_db.find_one({'_id': chat_id})
        msg = params['srs_map'] + params['status_msg']


    elif sub_params['phasers_flag'] == 1:
        keyboard = main_keyboard()
        sub_param_db.update_one({'_id': chat_id}, {"$set": {'phasers_flag': 0}}, upsert=True)
        int_command = ''
        input = params['input']
        params['input'] = 0
        phasers_compute(update, context, input)

    elif sub_params['torpedoes'] == 1:
        keyboard = main_keyboard()
        sub_param_db.update_one({'_id': chat_id}, {"$set": {'torpedoes': 0}}, upsert=True)
        int_command = ''
        input = params['input']
        params['input'] = 0
        torpedoes_compute(update, context, input)
    else:
        msg = ''
        keyboard = main_keyboard()

    params = parameters_db.find_one({'_id': chat_id})
    if params['attack_msg_out'] != '':
        msg = params['attack_msg_out']
        params['attack_msg_out']=''
        parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)


    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(msg),
                                  reply_markup=keyboard,
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def num_backspace(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    global int_command
    int_command = int_command[:-1]
    msg = f'Your command:{int_command}'
    sub_params = sub_param_db.find_one({'_id': chat_id})
    if sub_params['shields_flag'] == 1:
        msg = f'Energy to the shields:{int_command}'
    elif sub_params['helm'] == 1:
        msg = f'Setting Helm Vector:{int_command}'
    elif sub_params['wrap'] == 1:
        msg = f'Enter Wrap Coefficient:{int_command}'
    elif sub_params['phasers_flag'] == 1:
        msg = f'Phaser Energy:{int_command}'
    elif sub_params['torpedoes'] == 1:
        msg = f'Fire in direction:{int_command}'
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(msg),
                                  reply_markup=num_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def helm_menu(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    sub_params = sub_param_db.find_one({'_id': chat_id})
    sub_params['helm'] = 1
    sub_params['wrap'] = 1
    sub_param_db.update_one({'_id': chat_id}, {"$set": sub_params}, upsert=True)
    msg = 'Setting Helm Vector'
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text=main_message(msg),
                                  reply_markup=num_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def main_message(update=''):
    lenth_keeper = '\n------------------------------------------\n'
    message = 'Waiting for orders, Capitain!'
    if update == '':
        out_msg = message
    else:
        out_msg = update
    out_msg = lenth_keeper + out_msg + lenth_keeper
    return out_msg


[dispatcher.add_handler(i) for i in [
    CommandHandler('info', info),
    CommandHandler('manual', manual),
    CommandHandler('start', start_game),
    CommandHandler(['help', '0'], bot_help),
    CommandHandler(['helm', '1'], bot_helm),
    CommandHandler(['lrs', '2'], bot_lrs),
    CommandHandler(['phasers', '3'], bot_phasers),
    CommandHandler(['torpedoes', '4'], bot_torpedoes),
    CommandHandler(['shields', '5'], bot_shields),
    CommandHandler(['resign', '6'], bot_resign),
    MessageHandler(Filters.all, bot_sub_command),
    CallbackQueryHandler(bot_lrs, pattern='lrs'),
    CallbackQueryHandler(bot_srs, pattern='srs'),
    CallbackQueryHandler(main_menu, pattern='menu'),
    CallbackQueryHandler(shields_button, pattern='shields'),
    CallbackQueryHandler(helm_menu, pattern='helm'),
    CallbackQueryHandler(num_menu, pattern=r'^\d*$'),
    CallbackQueryHandler(back2main, pattern='back2main'),
    CallbackQueryHandler(num_backspace, pattern='backspace'),
    CallbackQueryHandler(phasers_button, pattern='phasers'),
    CallbackQueryHandler(torpedoes_button, pattern='torpedoes'),
    CallbackQueryHandler(num_command, pattern='enter')
]]

if __name__ == '__main__':
    updater.start_polling()
