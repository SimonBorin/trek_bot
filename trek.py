import random
import os
import re
import yaml
from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler
import telegram
from pymongo import MongoClient
from keyboards import main_keyboard, num_keyboard, menu_keyboard, manual_keyboard, restart_keyboard, helm_keyboard

# with open(r'./params.yaml') as file:
#     props = yaml.load(file, Loader=yaml.FullLoader)
#     mongo = props['mongo']
#     mongo_port = props['mongo_port']

updater = Updater(token=os.environ['BOT_TOKEN'], use_context=True)
dispatcher = updater.dispatcher
client = MongoClient(host='trek_db', port=27017, username='trek_user', password=os.environ['MONGO_PASS'])
db = client.user_database
collection = db.user_data_collection

parameters_db = db.parameters
sub_param_db = db.sub_param


def info(update, context):
    info_msg = 'Thats my boring bot, based on star trek text rpg from 1971.\n' \
               'https://github.com/SimonBorin/trek_bot/\n' \
               '@blooomberg\n'
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=info_msg,
                                  reply_markup=menu_keyboard())


def galaxy_info(update, context):
    info_msg = '''
    ```
    The galaxy is divided into an 8 X 8 quadrant grid,
and each quadrant is further divided into an 8 x 8 sector grid.

You will be assigned a starting point somewhere in the galaxy 
to begin a tour of duty as commander of the starship Enterprise.
Your mission: to seek out and destroy the fleet of Klingon warships 
which are menacing the United Federation of Planets.
 ```
'''
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=info_msg,
                                  reply_markup=manual_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def helm_info(update, context):
    info_msg = '''```
    Course is in a circular numerical vector          
arrangement as shown. Integer                        
values may be used.
                                   
  7  8  9                               
   . . .   
    ...                                
4 ---*--- 6    
    ...                                
   . . .   
  1  2  3

    One warp factor is the size of one quadrant.        
Therefore, to get from quadrant 6x,5y to 5x,5y
you would use course 4, warp factor 1.
```'''
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=info_msg,
                                  reply_markup=manual_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def lrs_info(update, context):
    info_msg = '''```
    Shows conditions in space for one quadrant on each side of the Enterprise
(which is in the middle of the scan). The scan is coded in the form ###
where the units digit is the number of stars, the tens digit is the number
of starbases, and the hundreds digit is the number of Klingons.
Example - 207 = 2 Klingons, No Starbases, & 7 stars.
  ```'''
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=info_msg,
                                  reply_markup=manual_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def srs_info(update, context):
    info_msg = '''```
    Symbology on your sensor screen is as follows:
-O- = Your starship's position
>!< = Klingon battlecruiser
<O> = Federation starbase (Refuel/Repair/Re-Arm here)
 *  = Star 
  ```'''
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=info_msg,
                                  reply_markup=manual_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def phasers_info(update, context):
    info_msg = '''```
    Allows you to destroy the Klingon Battle Cruisers by zapping them with
suitably large units of energy to deplete their shield power. (Remember,
Klingons have phasers, too!)
     ```'''
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=info_msg,
                                  reply_markup=manual_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def torpedoes_info(update, context):
    info_msg = '''```
    Torpedo course is the same  as used in helm control. If you hit
the Klingon vessel, he is destroyed and cannot fire back at you. If you
miss, you are subject to the phaser fire of all other Klingons in the
quadrant.
     ```'''
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=info_msg,
                                  reply_markup=manual_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def shields_info(update, context):
    info_msg = '''```
    Defines the number of energy units to be assigned to the shields. Energy
is taken from total ship's energy. Note that the status display total
energy includes shield energy.
     ```'''
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=info_msg,
                                  reply_markup=manual_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def manual(update, context):
    msg = 'https://github.com/SimonBorin/trek_bot/wiki/Manual'
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


def start(update, context):
    msg = '```\nStreting Game```'
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=msg,
                             reply_markup=restart_keyboard(),
                             parse_mode=telegram.ParseMode.MARKDOWN)


def start_game(update, context, restart_msg=''):
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
        klingons += x
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
    params = {
        'sector': sector,
        'stardate': stardate,
        'condition': condition,
        'energy': energy,
        'torpedoes': torpedoes,
        'shields': shields,
        'klingons': klingons
    }
    status_msg = status(params)
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
                     'wrap': 0, 'helm': 0, 'srs_map': srs_map, 'status_msg': status_msg, 'num_input': ''}
    sub_param4db = {'_id': chat_id, 'shields_flag': 0, 'helm': 0, 'phasers_flag': 0, 'lrs_flag': 0,
                    'wrap': 0, 'torpedoes': 0}
    try:
        parameters_db.delete_one({'_id': chat_id})
        sub_param_db.delete_one({'_id': chat_id})
    except Exception as e:
        print('error mongo! chat_id = ', chat_id, '\nerror = ', e)
    parameters_db.update_one({'_id': chat_id}, {"$set": parameters4db}, upsert=True)
    sub_param_db.update_one({'_id': chat_id}, {"$set": sub_param4db}, upsert=True)
    start_msg = restart_msg + blurb_msg
    update.effective_message.reply_text(main_message(update, context, start_msg),
                                        reply_markup=main_keyboard(),
                                        parse_mode=telegram.ParseMode.MARKDOWN)


def restart_game(update, context):
    start_game(update, context)


def bot_helm(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'helm': 1}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='``` \nCourse direction(1-4,5-9)? ```',
                             parse_mode=telegram.ParseMode.MARKDOWN)
    update.message.reply_text(main_message(update, context), reply_markup=main_keyboard())


def bot_lrs(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    params = parameters_db.find_one({'_id': chat_id})
    sector = params['sector']
    galaxy = params['galaxy']
    lrs_out = lrs(galaxy, sector)
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(update, context, lrs_out),
                                  reply_markup=main_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def bot_srs(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    params = parameters_db.find_one({'_id': chat_id})
    params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
    params['status_msg'] = status(params)
    srs_ = f"{params['srs_map']}{params['status_msg']}"
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(update, context, srs_),
                                  reply_markup=main_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def bot_phasers(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'phasers_flag': 1}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=' ``` \nPhaser energy? ``` ',
                             parse_mode=telegram.ParseMode.MARKDOWN)


def bot_torpedoes(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'torpedoes': 1}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='``` \nFire in direction(1-4,6-9)? ```',
                             parse_mode=telegram.ParseMode.MARKDOWN)


def bot_shields(update, context):
    chat_id = update.effective_chat.id
    drop_subparams_flag(chat_id)
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'shields_flag': 1}}, upsert=True)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=' ``` \nEnergy to shields? ``` ',
                             parse_mode=telegram.ParseMode.MARKDOWN)


def bot_resign(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=' ``` \nStarting new game ``` ',
                             parse_mode=telegram.ParseMode.MARKDOWN)
    start_game(update, context)


def shields_button(update, context):
    chat_id = update.effective_chat.id
    msg = 'Energy to the shields:'
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'shields_flag': 1}}, upsert=True)
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(update, context, msg),
                                  reply_markup=num_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def shields_compute(params, sub_params, input):
    params['energy'], params['shields'] = addshields(params['energy'], params['shields'], input)
    params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
    params['status_msg'] = status(params)
    sub_params['shields_flag'] = 0
    params = attack(params)
    return params, sub_params


def phasers_compute(update, context, params, input):
    params = phasers(params, input)
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
        msg = '``` \nEnterprise dead in space ```'
        gameover(update, context, msg)
    else:
        params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
        params['status_msg'] = status(params)
        params = attack(params)
    return params


def torpedoes_compute(params):
    params = photontorpedoes(params)
    # A Klingon has been destroyed-update galaxy map
    if params['ks'] < params['x']:
        # galaxy[sector] = galaxy[sector] - 100
        params['galaxy'][params['sector']][0] = params['galaxy'][params['sector']][0] - 1
        # update total klingons
        params['klingons'] = params['klingons'] - (params['x'] - params['ks'])
        # update sector klingons
        params['x'] = params['ks']
    params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
    params['status_msg'] = status(params)
    params = attack(params)
    return params


def helm_out(params):
    new_sector, energy, ent_position, stardate, msg = helm(params['galaxy'], params['sector'], params['energy'],
                                                           params['current_sector'], params['ent_position'],
                                                           params['stardate'], params['helm_dir'], params['wrap'])
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
    params['condition'] = condition
    if condition == "Docked":
        # Reset energy, torpedoes and shields
        params['energy'] = 3000
        params['torpedoes'] = 15
        params['shields'] = 0
    params['status_msg'] = status(params)
    params = attack(params)
    return params


def attack(params):
    attack_mag = ''
    if params['condition'] == "Red":
        if random.randint(1, 9) < 6:
            attack_mag += '``` \nRed alert - Klingons attacking!\n ```'
            damage = params['x'] * random.randint(1, 50)
            params['shields'] = params['shields'] - damage
            attack_mag += f'``` \nHit on shields: {damage} energy units\n ```'
            # Do we still have shields left?
            if params['shields'] < 0:
                attack_mag += '``` \nEnterprise dead in space\n ```'
                params['energy'] = 0
            else:
                params['condition'], srs_map = srs(params['current_sector'], params['ent_position'])
    params['attack_msg_out'] = attack_mag
    return params


def status(params):
    status_msg = f''' ```
Stardate:           {params['stardate']}
Condition:          {params['condition']}
Energy:             {params['energy']}
Photon torpedoes:   {params['torpedoes']}
Shields:            {params['shields']}
Klingons in galaxy: {params['klingons']}
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
    ```'''
    return promotion_msg


def lose():
    lose_msg = "```\nYou are relieved of duty. ```"
    return lose_msg


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
            stars -= 1
    # Add in the starbases (value = 2)
    while bases > 0:
        position = random.randint(0, 63)
        if current_sector[position] == 0:
            current_sector[position] = 2
            bases -= 1
    # Add in the klingons (value = -200)
    while klingons > 0:
        position = random.randint(0, 63)
        if current_sector[position] == 0:
            current_sector[position] = -200
            klingons -= 1
    return current_sector


def srs(current_sector, ent_pos):
    # Print out sector map
    # MapKey: >!< = Klingon
    #      <O> = Starbase
    #       *  = Star
    #      -O- = Enterprise
    klingons = False
    local_srs_map = "```\n"
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
    if not klingons:
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
    if 1 <= direction <= 9 and direction != 5:
        # Work out the horizontal and vertical co-ordinates
        # of the Enterprise in the current sector
        # 0,0 is top left and 7,7 is bottom right
        horiz = int(epos / 8)
        vert = epos - (horiz * 8)
        # And calculate the direction component of our course vector
        hinc, vinc = calcvector(direction)
        # How far do we need to move?
        warp = int(warp_)
        if 1 <= warp <= 63:
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
                while i <= warp and out is False:
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
                    i += 1
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


def phasers(params, bot_sub_command_):
    power = int(bot_sub_command_)
    params['message'] = '``` \n'
    if power <= params['energy']:
        # Reduce available energy by amount directed to phaser banks
        params['energy'] = params['energy'] - power
        # Divide phaser power by number of klingons in the sector if there are
        # any present! Space can do funny things to the mind ...
        if params['x'] > 0:
            power = power / params['x']
            # Work out the vertical and horizotal displacement of Enterprise
            horiz = params['ent_position'] / 8
            vert = params['ent_position'] - (8 * horiz)
            # Check all of the 64 positions in the sector for Klingons
            for i in range(0, 64):
                if params['current_sector'][i] < 0:
                    # We have a Klingon!
                    # Work out its horizontal and vertical displacement
                    horizk = i / 8
                    vertk = i - (8 * horizk)
                    # Work out distance from Klingon to Enterprise
                    z = horiz - horizk
                    y = vert - vertk
                    dist = 1
                    while ((dist + 1) * (dist + 1)) < (z * z + y * y):
                        dist += 1
                    # Klingon energy is negative, so add on the phaser power
                    # corrected for distance
                    params['current_sector'][i] = params['current_sector'][i] + int(power / dist)
                    if params['current_sector'][i] >= 0:
                        # Set this part of space to be empty
                        params['current_sector'][i] = 0
                        # Decrement sector klingons
                        params['ks'] = int(params['x'] - 1)
                        params['message'] += 'Klingon destroyed!\n'
                    else:
                        # We have a hit on Enterprise's shields if not docked
                        if params['condition'] != "Docked":
                            damage = int(power / dist)
                            params['shields'] = params['shields'] - damage
                            params[' message'] += f'Hit on shields: {damage} energy units\n'
    else:
        params['message'] += 'Not enough energy, Captain!'
    params['message'] += '```'
    return params


def photontorpedoes(params):
    if params['torpedoes'] < 1:
        msg = '``` \nNo photon torpedoes left, captain! ```'
    else:
        direction = params['helm_dir']
        if 1 <= direction <= 9 and direction != 5:
            # Work out the horizontal and vertical co-ordinates
            # of the Enterprise in the current sector
            # 0,0 is top left and 7,7 is bottom right
            horiz = int(params['ent_position'] / 8)
            vert = int(params['ent_position'] - horiz * 8)
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
                    if params['current_sector'][vert + 8 * horiz] == 2:
                        # Oh dear - taking out a starbase ends the game
                        out = True
                        params['current_sector'][vert + 8 * horiz] = 0
                        params['energy'] = 0
                        msg = '``` \nStarbase destroyed ```'
                    elif params['current_sector'][vert + 8 * horiz] == 3:
                        # Shooting a torpedo into a star has no effect
                        out = True
                        msg = '``` \nTorpedo missed ```'
                    elif params['current_sector'][vert + 8 * horiz] < 0:
                        # Hit and destroyed a Klingon!
                        out = True
                        params['current_sector'][vert + 8 * horiz] = 0
                        params['ks'] = params['x'] - 1
                        msg = '``` \nKlingon destroyed! ```'
            # One fewer torpedo
            params['torpedoes'] -= 1
        else:
            msg = '``` \nYour command is not logical, Captain. ```'
    params['msg'] = msg
    return params


def addshields(energy, shields, num_input):
    # Add energy to shields
    power = int(num_input)
    if (power > 0) and (energy >= power):
        energy -= power
        shields += power
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


def main_menu(update, context):
    query = update.callback_query
    msg = '''```
╔╦╗╔═╗╦╔╗╔
║║║╠═╣║║║║
╩ ╩╩ ╩╩╝╚╝
```'''
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=msg,
                                  reply_markup=menu_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def phasers_button(update, context):
    chat_id = update.effective_chat.id
    params = parameters_db.find_one({'_id': chat_id})
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'phasers_flag': 1}}, upsert=True)
    msg = f"Phaser Energy:{params['num_input']}"
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(update, context, msg),
                                  reply_markup=num_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def torpedoes_button(update, context):
    chat_id = update.effective_chat.id
    sub_param_db.update_one({'_id': chat_id}, {"$set": {'torpedoes': 1}}, upsert=True)
    msg = "Fire in direction: "
    context.bot.edit_message_text(chat_id=update.effective_chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(update, context, msg),
                                  reply_markup=helm_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def back2main(update, context):
    query = update.callback_query
    drop_subparams_flag(query.message.chat_id)
    chat_id = update.effective_chat.id
    params = parameters_db.find_one({'_id': chat_id})
    params['num_input'] = ''
    parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(update, context, ''),
                                  reply_markup=main_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def back2menu(update, context):
    query = update.callback_query
    msg = '''```
╔╦╗╔═╗╦╔╗╔
║║║╠═╣║║║║
╩ ╩╩ ╩╩╝╚╝
    ```'''
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=msg,
                                  reply_markup=menu_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def num_menu(update, context):
    query = update.callback_query
    print(update.callback_query.data)
    chat_id = update.effective_chat.id
    params = parameters_db.find_one({'_id': chat_id})
    sub_params = sub_param_db.find_one({'_id': chat_id})
    input = update.callback_query.data
    pattern = re.compile("^\d*$")
    if pattern.match(input):
        temp_num = params['num_input']
        temp_num += input
        params['num_input'] = temp_num
    msg = f"Your command:{params['num_input']}"
    print(msg)

    keyboard = num_keyboard()
    if sub_params['helm'] == 1:
        msg = f"Setting Helm Vector:{params['num_input']}"
        params['helm'] = int(params['num_input'])

    elif sub_params['wrap'] == 1:
        msg = f"Enter Wrap Coefficient:{params['num_input']}"
        params['wrap'] = int(params['num_input'])
        if params['wrap'] > 63:
            msg += '''```
Enterprise can`t jump 
over more then 63 sectors 
at a time.
Wrap Coefficient
would be set on max.
```'''
            params['wrap'] = 63
            params['num_input'] = 0

    elif sub_params['shields_flag'] == 1:
        msg = f"Energy to the shields:{params['num_input']}"
        params['input'] = int(params['num_input'])
        if params['input'] >= params['energy']:
            msg += '''```
Warning! 
Not Enough Energy!
Further actions will cause 
self-destruction!
            ```'''

    elif sub_params['phasers_flag'] == 1:
        msg = f"Phaser Energy:{params['num_input']}"
        params['input'] = int(params['num_input'])
        if params['input'] >= params['energy']:
            msg += '''```
Warning! 
Not Enough Energy!
Further actions will cause 
self-destruction!
                    ```'''

    elif sub_params['torpedoes'] == 1:
        msg = f"Fire in direction:{params['num_input']}"
        params['input'] = int(params['num_input'])

    parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(update, context, msg),
                                  reply_markup=keyboard,
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def num_command(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    params = parameters_db.find_one({'_id': chat_id})
    sub_params = sub_param_db.find_one({'_id': chat_id})
    if sub_params['wrap'] == 1:
        keyboard = main_keyboard()
        sub_param_db.update_one({'_id': chat_id}, {"$set": {'wrap': 0}}, upsert=True)
        params['num_input'] = ''
        params = helm_out(params)
        params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
        msg = ''

    elif sub_params['shields_flag'] == 1:
        keyboard = main_keyboard()
        shields_update = params['num_input']
        params['num_input'] = ''
        input = params['input']
        params['input'] = 0
        sub_params['shields_flag'] = 0
        params, sub_params = shields_compute(params, sub_params, input)
        sub_param_db.update_one({'_id': chat_id}, {"$set": sub_params}, upsert=True)
        msg = f'''```
Energy to shields {shields_update}
```'''

    elif sub_params['phasers_flag'] == 1:
        keyboard = main_keyboard()
        sub_param_db.update_one({'_id': chat_id}, {"$set": {'phasers_flag': 0}}, upsert=True)
        params['num_input'] = ''
        input = params['input']
        params['input'] = 0
        params = phasers_compute(update, context, params, input)
        params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
        msg = params['msg']
        params['msg'] = ''

    else:
        msg = ''
        keyboard = main_keyboard()

    if params['attack_msg_out'] != '':
        msg += params['attack_msg_out']
        params['attack_msg_out'] = ''

    if params['energy'] == 0:
        gameover(update, context, msg)
        params['msg'] = ''
    elif params['klingons'] == 0:
        victory(update, context)
        params['msg'] = ''
    else:

        params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
        params['status_msg'] = status(params)
        parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
        context.bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text=main_message(update, context, msg),
                                      reply_markup=keyboard,
                                      parse_mode=telegram.ParseMode.MARKDOWN)


def num_backspace(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    params = parameters_db.find_one({'_id': chat_id})
    params['num_input'] = params['num_input'][:-1]
    parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
    msg = f"Your command:{params['num_input']}"
    sub_params = sub_param_db.find_one({'_id': chat_id})
    if sub_params['shields_flag'] == 1:
        msg = f"Energy to the shields:{params['num_input']}"
    elif sub_params['helm'] == 1:
        msg = f"Setting Helm Vector:{params['num_input']}"
    elif sub_params['wrap'] == 1:
        msg = f"Enter Wrap Coefficient:{params['num_input']}"
    elif sub_params['phasers_flag'] == 1:
        msg = f"Phaser Energy:{params['num_input']}"
    elif sub_params['torpedoes'] == 1:
        msg = f"Fire in direction:{params['num_input']}"
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=main_message(update, context, msg),
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
                                  text=main_message(update, context, msg),
                                  reply_markup=helm_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def helm_direction(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    params = parameters_db.find_one({'_id': chat_id})
    sub_params = sub_param_db.find_one({'_id': chat_id})
    params['helm_dir'] = int(update.callback_query.data[-1:])
    keyboard = main_keyboard()
    msg = ''
    if sub_params['helm'] == 1:
        keyboard = num_keyboard()
        msg = 'Enter Wrap Coefficient'
        sub_param_db.update_one({'_id': chat_id}, {"$set": {'helm': 0}}, upsert=True)
    elif sub_params['torpedoes'] == 1:
        sub_param_db.update_one({'_id': chat_id}, {"$set": {'torpedoes': 0}}, upsert=True)
        params = torpedoes_compute(params)
        params['input'] = 0
        msg = params['msg'] + params['attack_msg_out']
        params['msg'] = ''
    parameters_db.update_one({'_id': chat_id}, {"$set": params}, upsert=True)
    if params['klingons'] == 0:
        victory(update, context)
        params['msg'] = ''
    else:
        context.bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=main_message(update, context, msg),
                                      reply_markup=keyboard,
                                      parse_mode=telegram.ParseMode.MARKDOWN)


def manual_menu(update, context):
    query = update.callback_query
    msg = '''```
╔╦╗╔═╗╔╗╔╦ ╦╔═╗╦  
║║║╠═╣║║║║ ║╠═╣║  
╩ ╩╩ ╩╝╚╝╚═╝╩ ╩╩═╝
```'''
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text=msg,
                                  reply_markup=manual_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def gameover(update, context, attack_mag):
    query = update.callback_query
    msg = attack_mag + lose() + '''```
╔═╗╔═╗╔╦╗╔═╗  ╔═╗╦  ╦╔═╗╦═╗
║ ╦╠═╣║║║║╣   ║ ║╚╗╔╝║╣ ╠╦╝
╚═╝╩ ╩╩ ╩╚═╝  ╚═╝ ╚╝ ╚═╝╩╚═                                                    
    ```'''

    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text=msg,
                                  reply_markup=restart_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def victory(update, context):
    query = update.callback_query
    msg = promotion() + '''```
╦  ╦╦╔═╗╔╦╗╔═╗╦═╗╦ ╦
╚╗╔╝║║   ║ ║ ║╠╦╝╚╦╝
 ╚╝ ╩╚═╝ ╩ ╚═╝╩╚═ ╩                                                       
    ```'''
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text=msg,
                                  reply_markup=restart_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def restart(update, context):
    query = update.callback_query
    start_game(update, context)
    context.bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text='',
                                  reply_markup=main_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def main_message(update, context, incom=''):
    message = 'Waiting for orders, Capitain!'
    if incom == '':
        out_msg = message
    else:
        out_msg = incom
    out_msg = out_msg + main_screen(update, context)  # + out_msg
    return out_msg


def main_screen(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    params = parameters_db.find_one({'_id': chat_id})
    params['condition'], params['srs_map'] = srs(params['current_sector'], params['ent_position'])
    params['status_msg'] = status(params)
    main_screen_msg = params['srs_map'] + params['status_msg']
    return main_screen_msg


def booze(update, context):
    query = update.callback_query
    start_text = '''```
tst
```'''
    context.bot.send_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text=start_text,
                                  reply_markup=main_keyboard(),
                                  parse_mode=telegram.ParseMode.MARKDOWN)


[dispatcher.add_handler(i) for i in [
    CommandHandler(['start', 'restart'], start),
    CallbackQueryHandler(bot_lrs, pattern='lrs'),
    CallbackQueryHandler(helm_direction, pattern='arrow'),
    CallbackQueryHandler(main_menu, pattern='menu'),
    CallbackQueryHandler(shields_button, pattern='shields'),
    CallbackQueryHandler(helm_menu, pattern='helm'),
    CallbackQueryHandler(num_menu, pattern=r'^\d*$'),
    CallbackQueryHandler(back2main, pattern='back2main'),
    CallbackQueryHandler(num_backspace, pattern='backspace'),
    CallbackQueryHandler(phasers_button, pattern='phasers'),
    CallbackQueryHandler(torpedoes_button, pattern='torpedoes'),
    CallbackQueryHandler(info, pattern='info'),
    CallbackQueryHandler(manual_menu, pattern='manual'),
    CallbackQueryHandler(back2menu, pattern='back2menu'),
    CallbackQueryHandler(galaxy_info, pattern='galaxyInfo'),
    CallbackQueryHandler(helm_info, pattern='1helmInfo'),
    CallbackQueryHandler(lrs_info, pattern='2lrsInfo'),
    CallbackQueryHandler(phasers_info, pattern='4phasersInfo'),
    CallbackQueryHandler(torpedoes_info, pattern='5torpedoesInfo'),
    CallbackQueryHandler(shields_info, pattern='6shieldsInfo'),
    CallbackQueryHandler(srs_info, pattern='3srsinfo'),
    CallbackQueryHandler(num_command, pattern='enter'),
    CallbackQueryHandler(restart, pattern='restart')
]]

if __name__ == '__main__':
    updater.start_polling()
