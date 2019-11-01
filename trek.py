import random
import time
import sys
import re
import yaml
import time
import sqlite3

from telegram.ext import Updater
from telegram.ext import CommandHandler,MessageHandler,Filters
import telegram

with open(r'./params.yaml') as file:
    props = yaml.load(file, Loader=yaml.FullLoader)
    token = props['token']
updater = Updater(token=token, use_context=True)

dispatcher = updater.dispatcher
def sql_conn():
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    return cursor,conn
#global vars



parameters = {}
chat_id=0
# parameters[chat_id]['galaxy']=[]
# parameters[chat_id]['klingons']=0
# parameters[chat_id]['energy']=0
# parameters[chat_id]['torpedoes']=0
# parameters[chat_id]['shields']=0
# parameters[chat_id]['stardate']=0.0
# parameters[chat_id]['sector']=0
# parameters[chat_id]['ent_position']=0
# parameters[chat_id]['x']=0
# parameters[chat_id]['y']=0
# parameters[chat_id]['z']=0
# parameters[chat_id]['current_sector']=[]
# parameters[chat_id]['condition']=''
# parameters[chat_id]['wrap']=0
# parameters[chat_id]['helm']=0

sub_param = {}
# sub_param[chat_id]['shields_flag']=0
# sub_param[chat_id]['helm_flag']=0
# sub_param[chat_id]['phasers_flag']=0
# sub_param[chat_id]['lrs_flag']=0
# sub_param[chat_id]['helm']=0
# sub_param[chat_id]['wrap']=0
# sub_param[chat_id]['torpedoes']=0

second_coefficient = 0


def init_db():
    cursor,conn = sql_conn()
    cursor.execute('DROP TABLE parameters')
    conn.commit()
    cursor.execute('DROP TABLE flags')
    conn.commit()
    cursor.execute('''CREATE TABLE IF NOT EXISTS parameters
                    (chat_id INTEGER, 
                    data text, 
                    value INTEGER)
                   ''')
    conn.commit()
    cursor.execute('''CREATE TABLE IF NOT EXISTS flags
                        (chat_id INTEGER, 
                        shields_flag INTEGER,
                        helm_flag INTEGER, 
                        phasers_flag INTEGER,
                        lrs_flag INTEGER,
                        helm INTEGER,
                        wrap INTEGER,
                        torpedoes INTEGER)
                       ''')
    conn.commit()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tst
                            (chat_id INTEGER, 
                            shields_flag INTEGER)
                           ''')
    conn.commit()


def rand_sleep():
    rand_sleep = random.uniform(0.3,1)
    return rand_sleep

def info(update, context):
    s=2
    info_message = '''
Thats my boring bot, based on star trek text rpg from 1973.
https://github.com/SimonBorin/trek_bot/tree/trash
@blooomberg
'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=info_message)
    time.sleep(rand_sleep())


def start_game(update, context):
    global parameters
    # main()
    blurb_msg = blurb()
    # Set up a random stardate
    stardate=float(random.randrange(1000,1500,1))
    # Enterprise starts with 3,000 units of energy, 15 torpedoes and 1,000
    # units of energy in its shields
    energy=3000
    torpedoes=15
    shields=0
    # No klingons around ... yet!
    klingons = 0

    # The galaxy is divided into 64 sectors. Each sectoris represented by one 
    # element in the galaxy list. The galaxy list contains a three digit number
    # Hundreds = number of klingons in the sector
    # Tens = number of starbases
    # Units = number of stars
    galaxy=[]
    # Initialise the galaxy list
    for i in range (0,64):
        x=y=0
        z=random.randint(1,5)
        if random.randint(1,10)<8:
            x=random.randint(1,3)
        if random.randint(1,100)>88:
            y=1
        galaxy.append(x*100+y*10+z)
        # Keep a record of how many klingons are left to be destroyed
        klingons=klingons+x

    # Choose the starting sector and position for the Enterprise
    sector = random.randint(0,63)
    ent_position = random.randint(0,63)
    # Set up current sector and decode it
    # x = klingons; y = starbases; z = starsf
    x,y,z=decode(galaxy[sector])
    # Set up the current sector map
    # Each sector has 64 positions in which a klingon, starbase, star 
    # or the Enterprise may be located in
    current_sector=init(x,y,z,ent_position)
    # Perform a short range scan
    condition,srs_map=srs(current_sector,ent_position)
    status_msg = status(sector,stardate,condition,energy,torpedoes,shields,klingons)
    # Keep going until we have destroyed all the klingons or we run out of
    # energy or we quit
    wrap = 0
    helm = 0
    chat_id = update.effective_chat.id
    parameters.update({chat_id:{'galaxy':galaxy,'klingons':klingons,'energy':energy,'torpedoes':torpedoes,
                                'shields':shields,'stardate':stardate,'sector':sector,'ent_position':ent_position,
                                'x':x,'y':y,'z':z,'current_sector':current_sector,'condition':condition,
                                'wrap':wrap,'helm':helm}})
    sub_param.update({chat_id:{'shields_flag':0,'helm_flag':0,'phasers_flag':0,'lrs_flag':0,'helm':0,'wrap':0,'torpedoes':0}})
    # parameters[chat_id]['galaxy']=galaxy
    # parameters[chat_id]['klingons']=klingons
    # parameters[chat_id]['energy']=energy
    # parameters[chat_id]['torpedoes']=torpedoes
    # parameters[chat_id]['shields']=shields
    # parameters[chat_id]['stardate']=stardate
    # parameters[chat_id]['sector']=sector
    # parameters[chat_id]['ent_position']=ent_position
    # parameters[chat_id]['x']=x
    # parameters[chat_id]['y']=y
    # parameters[chat_id]['z']=z
    # parameters[chat_id]['current_sector']=current_sector
    # parameters[chat_id]['condition']=condition
    # parameters[chat_id]['wrap'] = wrap
    # parameters[chat_id]['helm'] = helm
    # init_data(chat_id, galaxy, klingons, energy, torpedoes, shields, stardate, sector, ent_position, x, y, z, current_sector, condition, wrap, helm)
    if klingons > 0 and energy > 0:

        # Command
        # 1 = Helm
        # 2 = Long range scan
        # 3 = Phasers
        # 4 = Photon torpedoes
        # 5 = Shields
        # 6 = Resign
        print('Command (1-6, 0 for help)? ')
    # print('debug')
    # print(update['message']['text']) 
    context.bot.send_message(chat_id=update.effective_chat.id, text=blurb_msg,parse_mode=telegram.ParseMode.MARKDOWN)
    time.sleep(rand_sleep())
    context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,parse_mode=telegram.ParseMode.MARKDOWN)
    time.sleep(rand_sleep())
    context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,parse_mode=telegram.ParseMode.MARKDOWN)
    time.sleep(rand_sleep())
    context.bot.send_message(chat_id=update.effective_chat.id, text=' ``` \nCommand (1-6, 0 for help)?  ``` ',parse_mode=telegram.ParseMode.MARKDOWN)



def bot_help(update, context):
    help_msg = showhelp()
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_msg,parse_mode=telegram.ParseMode.MARKDOWN)
    time.sleep(rand_sleep())
    context.bot.send_message(chat_id=update.effective_chat.id, text=' ``` \nCommand (1-6, 0 for help)?  ``` ',parse_mode=telegram.ParseMode.MARKDOWN)

def bot_helm(update, context):
    global sub_param
    chat_id = update.effective_chat.id
    sub_param[chat_id]['helm']=1
    context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCourse direction(1-4,5-9)? ```',parse_mode=telegram.ParseMode.MARKDOWN)

def bot_lrs(update, context):

    chat_id = update.effective_chat.id
    sector = parameters[chat_id]['sector']
    galaxy = parameters[chat_id]['galaxy']
    lrs_out = lrs(galaxy,sector)
    context.bot.send_message(chat_id=update.effective_chat.id, text=lrs_out,parse_mode=telegram.ParseMode.MARKDOWN)
    time.sleep(rand_sleep())
    context.bot.send_message(chat_id=update.effective_chat.id, text=' ``` \nCommand (1-6, 0 for help)?  ``` ',parse_mode=telegram.ParseMode.MARKDOWN)

def bot_phasers(update, context):
    chat_id = update.effective_chat.id
    global sub_param
    sub_param[chat_id]['phasers_flag']=1
    context.bot.send_message(chat_id=update.effective_chat.id, text=' ``` \nPhaser energy? ``` ',parse_mode=telegram.ParseMode.MARKDOWN)
    print('Phaser energy? ')

def bot_torpedoes(update, context):
    chat_id = update.effective_chat.id
    global sub_param
    sub_param[chat_id]['torpedoes']=1
    context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nFire in direction(1-4,6-9)? ```',parse_mode=telegram.ParseMode.MARKDOWN)

def bot_shields(update, context):
    chat_id=update.effective_chat.id
    global sub_param
    sub_param[chat_id]['shields_flag']=1
    context.bot.send_message(chat_id=update.effective_chat.id, text=' ``` \nEnergy to shields? ``` ',parse_mode=telegram.ParseMode.MARKDOWN)
    print('Energy to shields? ')

def bot_resign(update, context):
    chat_id = update.effective_chat.id
    parameters[chat_id]['energy']=0

# @bot.message_handler(regexp="^\d*$")
# @bot.message_handler(content_types=['text'])
def bot_sub_command(update, context):
    global sub_param
    global parameters
    global srs_map
    chat_id = update.effective_chat.id
    bot_sub_command_ = update.message.text
    # print('debug text',update.message.text)
    pattern = re.compile("^\d*$")
    if pattern.match(bot_sub_command_):
        chat_id = update.effective_chat.id
        klingons = parameters[chat_id]['klingons']
        energy = parameters[chat_id]['energy']
        torpedoes = parameters[chat_id]['torpedoes']
        shields = parameters[chat_id]['shields']
        stardate = parameters[chat_id]['stardate']
        sector = parameters[chat_id]['sector']
        ent_position = parameters[chat_id]['ent_position']
        galaxy = parameters[chat_id]['galaxy']
        x = parameters[chat_id]['x']
        y = parameters[chat_id]['y']
        z = parameters[chat_id]['z']
        current_sector = parameters[chat_id]['current_sector']
        condition = parameters[chat_id]['condition']


        if sub_param[chat_id]['shields_flag']==1:
            energy,shields=addshields(energy,shields,bot_sub_command_)
            parameters[chat_id]['energy']=energy
            parameters[chat_id]['shields']=shields
            condition,srs_map=srs(current_sector,ent_position)
            parameters[chat_id]['condition']=condition
            status_msg = status(sector,stardate,condition,energy,torpedoes,shields,klingons)

            context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            atack(update,context)
            context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand (1-6, 0 for help)? ```',parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            print('Command (1-6, 0 for help)? ')
            sub_param[chat_id]['shields_flag']=0

        elif sub_param[chat_id]['phasers_flag']==1:
            shields,energy,current_sector,ks,message=phasers(condition,shields,energy,current_sector,ent_position,x,bot_sub_command_)
            parameters[chat_id]['shields']=shields
            parameters[chat_id]['energy']=energy
            parameters[chat_id]['current_sector']=current_sector
            # print('debug phasers()\nshields = ', shields, '\nks = ',ks)
            context.bot.send_message(chat_id=update.effective_chat.id, text=message,parse_mode=telegram.ParseMode.MARKDOWN)
            if ks < x:
                # (x-ks) Klingons have been destroyed-update galaxy map
                galaxy[sector]=galaxy[sector]-(100*(x-ks))
                parameters[chat_id]['galaxy']=galaxy
                # update total klingons
                klingons=klingons-(x-ks)
                parameters[chat_id]['klingons']=klingons
                # update sector klingons
                x=ks
                parameters[chat_id]['x']=x
            # Do we still have shields left?
            if shields < 0:
                print ("Enterprise dead in space")
                energy = 0
                parameters[chat_id]['energy']=energy
                context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nEnterprise dead in space ```',parse_mode=telegram.ParseMode.MARKDOWN)
                time.sleep(rand_sleep())
            else:
                condition,srs_map=srs(current_sector,ent_position)
                parameters[chat_id]['condition']=condition
                status_msg = status(sector,stardate,condition,energy,torpedoes,shields,klingons)
                context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,parse_mode=telegram.ParseMode.MARKDOWN)
                time.sleep(rand_sleep())
                context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,parse_mode=telegram.ParseMode.MARKDOWN)
                time.sleep(rand_sleep())
            sub_param[chat_id]['phasers_flag']=0
            print('Command (1-6, 0 for help)? ')
            atack(update,context)
            context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand (1-6, 0 for help)? ```',parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())

        elif sub_param[chat_id]['helm']==1:
            sub_param[chat_id]['wrap']=1
            parameters[chat_id]['helm'] = int(bot_sub_command_)
            sub_param[chat_id]['helm']=0
            context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nWarp (1-63)? ```',parse_mode=telegram.ParseMode.MARKDOWN)

        elif sub_param[chat_id]['wrap']==1:
            wrap_ =  int(bot_sub_command_)
            helm_ = parameters[chat_id]['helm']
            # print(f'debug \nwrap {wrap_}\nhelm {helm_}')
            new_sector,energy,ent_position,stardate,msg=helm(galaxy,sector, energy,current_sector,ent_position,stardate,helm_,wrap_)
            context.bot.send_message(chat_id=update.effective_chat.id, text=msg,parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            # If we're still in the same sector as before, draw the Enterprise
            parameters[chat_id]['energy']=energy
            parameters[chat_id]['ent_position']=ent_position
            parameters[chat_id]['stardate']=stardate
            if sector == new_sector:
                current_sector[ent_position]=4
            else:
            # Else set up the Enterprise in the new sector
                sector = new_sector
                ent_position = random.randint(0,63)
                x,y,z=decode(galaxy[sector])
                current_sector=init(x,y,z,ent_position)
                parameters[chat_id]['current_sector']=current_sector
                parameters[chat_id]['sector']=sector
                parameters[chat_id]['ent_position']=ent_position
                parameters[chat_id]['x']=x
                parameters[chat_id]['y']=y
                parameters[chat_id]['z']=z
            # Perform a short range scan after every movement
            condition,srs_map=srs(current_sector,ent_position)
            context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            parameters[chat_id]['condition']=condition
            if condition == "Docked":
                # Reset energy, torpedoes and shields
                energy=3000
                torpedoes=15
                shields=0
            status_msg = status(sector,stardate,condition,energy,torpedoes,shields,klingons)
            context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            atack(update,context)
            context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand (1-6, 0 for help)? ```',parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            sub_param[chat_id]['wrap']=0

        elif sub_param[chat_id]['torpedoes']==1:
            direction=int(bot_sub_command_)
            torpedoes,current_sector,ks,msg=photontorpedoes(torpedoes,current_sector,ent_position,x,direction)
            parameters[chat_id]['torpedoes']=torpedoes
            parameters[chat_id]['current_sector']=current_sector
            # A Klingon has been destroyed-update galaxy map
            if ks < x:
                galaxy[sector]=galaxy[sector]-100
                # update total klingons
                klingons=klingons-(x-ks)
                # update sector klingons
                x=ks
                parameters[chat_id]['galaxy']=galaxy
                parameters[chat_id]['klingons']=klingons
                parameters[chat_id]['x']=x
            condition,srs_map=srs(current_sector,ent_position)
            status_msg = status(sector,stardate,condition,energy,torpedoes,shields,klingons)
            parameters[chat_id]['condition']=condition
            context.bot.send_message(chat_id=update.effective_chat.id, text=msg,parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            atack(update,context)
            context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand (1-6, 0 for help)? ```',parse_mode=telegram.ParseMode.MARKDOWN)
            sub_param[chat_id]['torpedoes']=0



    else :
        print("Command not recognised captain")
        context.bot.send_message(chat_id=update.effective_chat.id, text='``` \nCommand not recognised captain ``` ', parse_mode=telegram.ParseMode.MARKDOWN)
        sub_param[chat_id]['torpedoes'] = 0

def atack(update,context):
    global parameters
    chat_id = update.effective_chat.id
    condition=parameters[chat_id]['condition']
    x=parameters[chat_id]['x']
    current_sector=parameters[chat_id]['current_sector']
    ent_position=parameters[chat_id]['ent_position']
    stardate=parameters[chat_id]['stardate']
    sector=parameters[chat_id]['sector']
    shields=parameters[chat_id]['shields']
    torpedoes=parameters[chat_id]['torpedoes']
    klingons=parameters[chat_id]['klingons']
    energy = parameters[chat_id]['energy']

    if condition == "Red":
        if random.randint(1,9)<6:
            print ("Red alert - Klingons attacking!")
            msg1 = '``` \nRed alert - Klingons attacking!\n ```'
            context.bot.send_message(chat_id=update.effective_chat.id, text=msg1,parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            time.sleep(0.5 * second_coefficient)
            damage=x*random.randint(1,50)
            shields=shields-damage
            parameters[chat_id]['shields']=shields
            print ("Hit on shields: ",damage," energy units")
            msg2 = f'``` \nHit on shields: {damage} energy units\n ```'
            context.bot.send_message(chat_id=update.effective_chat.id, text=msg2,parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(rand_sleep())
            # Do we still have shields left?
            if shields < 0:
                print ("Enterprise dead in space")
                msg3 = '``` \nEnterprise dead in space\n ```'
                context.bot.send_message(chat_id=update.effective_chat.id, text=msg3,parse_mode=telegram.ParseMode.MARKDOWN)
                time.sleep(rand_sleep())
                energy = 0
            else:
                condition,srs_map=srs(current_sector,ent_position)
                parameters[chat_id]['condition']=condition
                status_msg = status(sector,stardate,condition,energy,torpedoes,shields,klingons)

                context.bot.send_message(chat_id=update.effective_chat.id, text=srs_map,parse_mode=telegram.ParseMode.MARKDOWN)
                time.sleep(rand_sleep())
                context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg,parse_mode=telegram.ParseMode.MARKDOWN)
                time.sleep(rand_sleep())

#     if klingons > 0 and energy > 0:

#         # Command
#         # 1 = Helm
#         # 2 = Long range scan
#         # 3 = Phasers
#         # 4 = Photon torpedoes
#         # 5 = Shields
#         # 6 = Resign
#         print('Command (1-6, 0 for help)? ')
#         command=bot_command_
#         if command == 0:
#             showhelp()

#         elif command == 1:
#             new_sector,energy,ent_position,stardate=helm(galaxy,sector,
#             energy,current_sector,ent_position,stardate)
#             # If we're still in the same sector as before, draw the Enterprise
#             if sector == new_sector:
#                 current_sector[ent_position]=4
#             else:
#             # Else set up the Enterprise in the new sector
#                 sector = new_sector
#                 ent_position = random.randint(0,63)
#                 x,y,z=decode(galaxy[sector])
#                 current_sector=init(x,y,z,ent_position)
#             # Perform a short range scan after every movement
#             condition=srs(current_sector,ent_position)
#             if condition == "Docked":
#                 # Reset energy, torpedoes and shields
#                 energy=3000
#                 torpedoes=15
#                 shields=0
#             status(sector,stardate,condition,energy,torpedoes,shields,klingons)
#         elif command == 2:
#             lrs(galaxy,sector)
#         elif command == 3:
#             shields,energy,current_sector,ks=phasers(condition,shields,energy,
#             current_sector,ent_position,x)
#             if ks < x:
#                 # (x-ks) Klingons have been destroyed-update galaxy map
#                 galaxy[sector]=galaxy[sector]-(100*(x-ks))
#                 # update total klingons
#                 klingons=klingons-(x-ks)
#                 # update sector klingons
#                 x=ks
#             # Do we still have shields left?
#             if shields < 0:
#                 print ("Enterprise dead in space")
#                 energy = 0
#             else:
#                 condition=srs(current_sector,ent_position)
#                 status(sector,stardate,condition,energy,torpedoes,
#                 shields,klingons)
#         elif command == 4:
#             torpedoes,current_sector,ks=photontorpedoes(torpedoes,
#             current_sector,ent_position,x)
#             # A Klingon has been destroyed-update galaxy map
#             if ks < x:
#                 galaxy[sector]=galaxy[sector]-100
#                 # update total klingons
#                 klingons=klingons-(x-ks)
#                 # update sector klingons
#                 x=ks
#             condition=srs(current_sector,ent_position)
#             status(sector,stardate,condition,energy,torpedoes,shields,klingons)
#         elif command == 5:
#             energy,shields=addshields(energy,shields)
#             condition=srs(current_sector,ent_position)
#             status(sector,stardate,condition,energy,torpedoes,shields,klingons)
#         elif command == 6:
#             # Set quit condition by making energy = 0
#             energy = 0
#         else:
#             print ("Command not recognised captain")
#         # After a command has been issued and condition is Red, a klingon may
#         # fire randomly on the enterprise!
#         if condition == "Red" and command != 0:
#             if random.randint(1,9)<6:
#                 print ("Red alert - Klingons attacking!")
#                 time.sleep(0.5 * second_coefficient)
#                 damage=x*random.randint(1,50)
#                 shields=shields-damage
#                 print ("Hit on shields: ",damage," energy units")
#                 # Do we still have shields left?
#                 if shields < 0:
#                     print ("Enterprise dead in space")
#                     energy = 0
#                 else:
#                     condition=srs(current_sector,ent_position)
#                     status(sector,stardate,condition,energy,torpedoes,
#                     shields,klingons)
#         if bot_command is not None:
#             a211qw=1# break # bail out of loop after one pass during testing
#     # If we get here we've won if no klingons are left, but lost otherwise
#     if klingons == 0:
#         promotion()
#     elif energy <= 0:
#         lose()
#     parameters[chat_id]['galaxy']=galaxy
#     parameters[chat_id]['klingons']=klingons
#     parameters[chat_id]['energy']=energy
#     parameters[chat_id]['torpedoes']=torpedoes
#     parameters[chat_id]['shields']=shields
#     parameters[chat_id]['stardate']=stardate
#     parameters[chat_id]['sector']=sector
#     parameters[chat_id]['ent_position']=ent_position
#     parameters[chat_id]['x']=x
#     parameters[chat_id]['y']=y
#     parameters[chat_id]['z']=z
#     parameters[chat_id]['current_sector']=current_sector
#     parameters[chat_id]['condition']=condition
#     #print('my command is ',command,'\n its type is ', type(command))


def status(sector,stardate,condition,energy,torpedoes,shields,klingons):
    time.sleep(0.2 * second_coefficient)
    print ("\nStardate:           ",stardate )
    time.sleep(0.2 * second_coefficient)
    print ("Condition:          ",condition)
    time.sleep(0.2 * second_coefficient)
    print ("Energy:             ",energy)
    time.sleep(0.2 * second_coefficient)
    print( "Photon torpedoes:   ",torpedoes)
    time.sleep(0.2 * second_coefficient)
    print ("Shields:            ",shields )
    time.sleep(0.2 * second_coefficient)
    print ("Klingons in galaxy: ",klingons, "\n")
    time.sleep(0.2 * second_coefficient)
    status_msg= f''' ```
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
    print ("\nSpace ... the final frontier.")

    time.sleep(1.5 * second_coefficient)
    print ("These are the voyages of the starship Enterprise")
    print( "Its five year mission ...")

    time.sleep(1.5 * second_coefficient)
    print ("... to boldly go where no-one has gone before")

    time.sleep(1.5 * second_coefficient)
    print ("You are Captain Kirk.")
    print ("Your mission is to destroy all of the Klingons in the galaxy.")

    time.sleep(2.5 * second_coefficient)
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
    print ("\nYou have successfully completed your mission!")
    print ("The federation has been saved.")
    print ("You have been promoted to Admiral Kirk.")

def lose():
    print ("\nYou are relieved of duty.")

def decode( sector):
    # Hundreds = klingons, tens = starbases, units = stars
    klingons=sector/100
    starbases=(sector-klingons*100)/10
    stars=sector-klingons*100-starbases*10
    return(klingons,starbases,stars)

def init(klingons,bases,stars,eposition):
    current_sector=[]
    for j in range (0,64):
        current_sector.append(0)
    # A value of 4 in the sector map indicates the Enterprise's position
    current_sector[eposition]=4
    # Add in the stars (value = 3)
    while stars > 0:
        position = random.randint(0,63)
        if current_sector[position]==0:
            current_sector[position]=3
            stars=stars-1
    # Add in the starbases (value = 2)
    while bases > 0:
        position=random.randint(0,63)
        if current_sector[position]==0:
            current_sector[position]=2
            bases=bases-1
    # Add in the klingons (value = -200)
    while klingons > 0:
        position=random.randint(0,63)
        if current_sector[position]==0:
            current_sector[position]=-200
            klingons=klingons-1
    return(current_sector)

def srs(current_sector,ent_pos):
    # Print out sector map
    # MapKey: >!< = Klingon
    #      <O> = Starbase
    #       *  = Star
    #      -O- = Enterprise
    klingons=False
    local_srs_map= "```"
    for i in range (0,64):
        if i%8 == 0:
            print()
            local_srs_map+="\n"
            time.sleep(0.2 * second_coefficient)
        if current_sector[i]<0:
            klingons=True
            print( ">!<", end=" ")
            local_srs_map+=">!<"
        elif current_sector[i]==0:
            print (" . ", end=" ")
            local_srs_map+=" . "
        elif current_sector[i]==2:
            print ("<O>", end=" ")
            local_srs_map+="<O>"
        elif current_sector[i]==3:
            print (" * ", end=" ")
            local_srs_map+=" * "
        else:
            print ("-O-", end=" ")
            local_srs_map+="-O-"
    print()
    # map = ''
    # Work out condition
    if klingons == False:
        condition="Green"
    else:
        condition="Red"
    # But docked status overrides Red/Green
    port=ent_pos-1
    starboard=ent_pos+1
    if port >= 0:
        if current_sector[port]==2:
            condition="Docked"
    if starboard <= 63:
        if current_sector[starboard]==2:
            condition="Docked"
    # Return condition status

    local_srs_map+="\n```"
    srs_map = local_srs_map
    # print('Thi is debug msg to check map')
    # print(srs_map)
    return(condition,srs_map)

def helm(galaxy,sector,energy,cur_sec,epos,stardate, helm_, warp_):
    direction=int(helm_)
    if direction >=1 and direction <=9 and direction !=5:
        # Work out the horizontal and vertical co-ordinates
        # of the Enterprise in the current sector
        # 0,0 is top left and 7,7 is bottom right
        horiz=int(epos/8)
        vert=int(epos-horiz*8)
        # And calculate the direction component of our course vector

        hinc,vinc=calcvector(direction)
        # How far do we need to move?
        warp=int(warp_)
        # print(f'horiz - {horiz}')
        # print(f'vert - {vert}')
        # If warp selected is in legal range move Enterprise
        # print(f'horiz - {horiz}\nvert - {vert}\nhinc - {hinc}\nvinc - {vinc}\n dir - {direction}\nwrap - {warp}')
        if warp >= 1 and warp <= 63:
            # Check there is sufficient energy
            if warp <= energy:
                # Reduce energy by warp amount
                energy = energy - warp
                # Remove Enterprise from current position
                cur_sec[epos] = 0
                # Calculate the new stardate
                stardate = stardate + (0.1*warp)
                # For the moment, assume movement leaves us in original sector
                out = False
                # Move the Enterprise warp units in the specified direction
                i=1
                while i <= warp and out == False:
                    # Calculate the movement vector
                    vert = vert + vinc
                    horiz = horiz + hinc
                    # Are we in the original sector still?
                    if vert < 0 or vert > 7 or horiz < 0 or horiz > 7:
                        out=True
                        # Calculate new sector and join ends of the galaxy
                        sector=int(join(sector+8*(horiz/8)+(vert/8)))
                    else:
                        # If we are in the original sector we can't go through
                        # solid objects! So reset course postion 1 click
                        # Inefficient - does this for warp steps even if we
                        # can't move.

                        if cur_sec[vert+8*horiz] != 0:
                            vert=vert-vinc
                            horiz=horiz-hinc
                        # Put the Enterprise in the new position
                        epos=vert+8*horiz
                    i=i+1
                    msg = '``` \nCalculateing ```'

            else:
                print ("Too little energy left. Only ",energy," units remain")
                msg = f'``` \nToo little energy left. Only {energy} units remain\n ```'
        else:
            print ("The engines canna take it, captain!")
            msg = '``` \nThe engines canna take it, captain!\n ```'
    else:
        print ("That's not a direction the Enterprise can go in, captain!")
        msg = '``` \nThat`s not a direction the Enterprise can go in, captain!\n ```'
    print(f'sector - {sector}')
    print(f'energy - {energy}')
    print(f'epos - {epos}')
    print(f'stardate - {stardate}')
    print(f'msg - {msg}')
    return(sector,energy,epos,stardate,msg)

def lrs( galaxy,sector):
    lrs_out='``` \n'
    # Print out the klingons/starbase/stars values from the
    # neighbouring eight sectors (and this one)
    time.sleep(0.2 * second_coefficient)
    print()
    for i in range (-8,9,8):
        for j in range (-1,2):
            # Join the ends of the galaxy together
            sec=join(sector+j+i)
            print ("%03d" % galaxy[sec], end=" ")
            lrs_out += "%03d " % galaxy[sec]
            time.sleep(0.2 * second_coefficient)
        print()
        lrs_out += '\n'
    print()
    lrs_out += '\n ```'
    return lrs_out

def phasers( condition,shields,energy,sector,epos,ksec, bot_sub_command_):

    power=int(bot_sub_command_)
    message = '``` \n'
    if power <= energy:
        # Reduce available energy by amount directed to phaser banks
        energy=energy-power
        # Divide phaser power by number of klingons in the sector if there are
        # any present! Space can do funny things to the mind ...
        if ksec > 0:
            power=power/ksec
            # Work out the vertical and horizotal displacement of Enterprise
            horiz=epos/8
            vert=epos-(8*horiz)
            # Check all of the 64 positions in the sector for Klingons
            for i in range (0,64):
                if sector[i]<0:
                    # We have a Klingon!
                    # Work out its horizontal and vertical displacement
                    horizk=i/8
                    vertk=i-(8*horizk)
                    # Work out distance from Klingon to Enterprise
                    z=horiz-horizk
                    y=vert-vertk
                    dist=1
                    while ((dist+1)*(dist+1))<(z*z+y*y):
                        dist=dist+1
                    # Klingon energy is negative, so add on the phaser power
                    # corrected for distance
                    sector[i]=sector[i]+int(power/dist)
                    if sector[i]>=0:
                        # Set this part of space to be empty
                        sector[i]=0
                        # Decrement sector klingons
                        ksec=int(ksec-1)
                        print ("Klingon destroyed!")
                        message += 'Klingon destroyed!\n'
                        time.sleep(0.2 * second_coefficient)
                    else:
                        # We have a hit on Enterprise's shields if not docked
                        if condition != "Docked":
                            damage=int(power/dist)
                            shields=shields-damage
                            print ("Hit on shields: ",damage," energy units")
                            message += f'Hit on shields: {damage} energy units\n'
                            time.sleep(0.2 * second_coefficient)
    else:
        print ("Not enough energy, Captain!")
        message += 'Not enough energy, Captain!'
    message += '```'
    return(shields,energy,sector,ksec,message)

def photontorpedoes( torpedoes,sector,epos,ksec, direction_):
    if torpedoes < 1:
        print ("No photon torpedoes left, captain!")
        msg = '``` \nNo photon torpedoes left, captain! ```'
    else:
        direction=int(direction_)
        if direction >=1 and direction <=9 and direction !=5:
            time.sleep(0.2 * second_coefficient)
            # Work out the horizontal and vertical co-ordinates
            # of the Enterprise in the current sector
            # 0,0 is top left and 7,7 is bottom right
            horiz=int(epos/8)
            vert=int(epos-horiz*8)
            # And calculate the direction to fire the torpedo
            hinc,vinc=calcvector(direction)
            # A torpedo only works in the current sector and stops moving
            # when we hit something solid
            out = False
            while out == False:
                    # Calculate the movement vector
                vert = vert + vinc
                horiz = horiz + hinc
                # Is the torpedo still in the sector?
                if vert < 0 or vert > 7 or horiz < 0 or horiz > 7:
                    out=True
                    print ("Torpedo missed")
                    msg = '``` \nTorpedo missed ```'
                else:
                    # Have we hit an object?
                    if sector[vert+8*horiz] == 2:
                        # Oh dear - taking out a starbase ends the game
                        out=True
                        sector[vert+8*horiz] = 0
                        energy=0
                        print ("Starbase destroyed")
                        msg = '``` \nStarbase destroyed ```'
                    elif sector[vert+8*horiz] == 3:
                        # Shooting a torpedo into a star has no effect
                        out=True
                        print ("Torpedo missed")
                        msg = '``` \nTorpedo missed ```'
                    elif sector[vert+8*horiz] < 0:
                        # Hit and destroyed a Klingon!
                        out=True
                        sector[vert+8*horiz] = 0
                        ksec = ksec - 1
                        print ("Klingon destroyed!")
                        msg = '``` \nKlingon destroyed! ```'
            # One fewer torpedo
            torpedoes = torpedoes-1
        else:
            print ("Your command is not logical, Captain.")
            msg = '``` \nYour command is not logical, Captain. ```'
    return(torpedoes,sector,ksec,msg)

def addshields( energy,shields, bot_sub_command_):
    # Add energy to shields
    power=int(bot_sub_command_)
    if ((power > 0) and (energy >= power)):
        energy = energy - power
        shields = shields + power
    return (energy,shields)

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
    # print(f'direction - {direction}')
    if direction == 4:
        direction = 6
    elif direction == 1:
        direction = 5
    elif direction == 2:
        direction = 4
    elif direction == 6:
        direction = 2
    elif direction == 9:
        direction = 1
    elif direction == 8:
        direction = 0
    # Work out the direction increment vector
    # hinc = horizontal increment
    # vinc = vertical increment
    if direction < 2 or direction > 6:
        hinc = -1
    elif direction > 2 and direction < 6:
        hinc = 1
    else:
        hinc = 0
    if direction < 4 and direction > 0:
        vinc = 1
    elif direction > 4:
        vinc = -1
    else:
        vinc = 0
    return(hinc,vinc)

def join( sector):
    # Join the ends of the galaxy together
    if sector < 0:
        sector = sector + 64
    if sector > 63:
        sector = sector - 63
    return(sector)

def showhelp():
    # Print out the command help
    print ("1 - Helm")
    print ("2 - Long Range Scan")
    print ("3 - Phasers")
    print ("4 - Photon Torpedoes")
    print ("5 - Shields")
    print ("6 - Resign")
    msg = '''
    ```
1 - Helm
2 - Long Range Scan
3 - Phasers
4 - Photon Torpedoes
5 - Shields
6 - Resign
```
    '''
    return msg

def init_data(chat_id, galaxy, klingons, energy, torpedoes, shields, stardate, sector, ent_position, x, y, z, current_sector, condition, wrap, helm):
    data = ['klingons', 'energy', 'torpedoes', 'shields', 'stardate', 'sector', 'ent_position', 'x', 'y', 'z', 'wrap', 'helm']
    value = [ klingons, energy, torpedoes, shields, stardate, sector, ent_position, x, y, z, wrap, helm]
    cursor,conn = sql_conn()
    cursor.execute(
        "INSERT INTO tst VALUES(123,321)")
    conn.commit()
    cursor.execute(
        f"INSERT INTO flags(chat_id,shields_flag,helm_flag,phasers_flag,lrs_flag,helm,wrap,torpedoes) VALUES({chat_id},0,0,0,0,0,0,0)")
    conn.commit()
    for i in range(len(data)):
        cursor.execute(f"INSERT INTO parameters(chat_id,data,value) VALUES({chat_id},'{data[i]}',{value[i]})")
        conn.commit()
    for i in galaxy:
        cursor.execute(f"INSERT INTO parameters(chat_id,data,value) VALUES({chat_id},'galaxy',{i})")
        conn.commit()
    for i in current_sector:
        cursor.execute(f"INSERT INTO parameters(chat_id,data,value) VALUES({chat_id},'current_sector',{i})")
        conn.commit()
    if condition == 'Red':
        condition_num = 1
    elif condition == 'Green':
        condition_num = 0
    elif condition == 'Docked':
        condition_num = 10
    cursor.execute(f"INSERT INTO parameters(chat_id,data,value) VALUES({chat_id},'condition',{condition_num})")
    conn.commit()

def fuck_you(chat_id,):
    print("fuck you",chat_id)

[dispatcher.add_handler(i) for i in [
    CommandHandler('info', info),
    CommandHandler('start', start_game),
    CommandHandler(['help', '0' ], bot_help),
    CommandHandler(['helm', '1' ], bot_helm),
    CommandHandler(['lrs','2'], bot_lrs),
    CommandHandler(['phasers', '3'], bot_phasers),
    CommandHandler(['torpedoes', '4'], bot_torpedoes),
    CommandHandler(['shields','5'], bot_shields),
    CommandHandler(['resign','6'], bot_resign),
    MessageHandler(Filters.all, bot_sub_command)
    ]]

if __name__ == '__main__':
    init_db()
    updater.start_polling()
