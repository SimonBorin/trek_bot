############################ Keyboards #########################################
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


def main_keyboard():
    keyboard = [InlineKeyboardButton('Helm', callback_data='helm'),
                InlineKeyboardButton('Shields', callback_data='shields'),
                InlineKeyboardButton('LRS', callback_data='lrs'),
                InlineKeyboardButton('SRS', callback_data='srs'),
                InlineKeyboardButton('Phasers', callback_data='phasers'),
                InlineKeyboardButton('Torpedoes', callback_data='torpedoes')
                ]
    footer = InlineKeyboardButton('Menu', callback_data='menu')
    reply_markup = InlineKeyboardMarkup(build_menu(keyboard, n_cols=2, footer_buttons=footer))
    return reply_markup


def num_keyboard():
    keyboard = [
        InlineKeyboardButton('7', callback_data='7'),
        InlineKeyboardButton('8', callback_data='8'),
        InlineKeyboardButton('9', callback_data='9'),
        InlineKeyboardButton('4', callback_data='4'),
        InlineKeyboardButton('5', callback_data='5'),
        InlineKeyboardButton('6', callback_data='6'),
        InlineKeyboardButton('1', callback_data='1'),
        InlineKeyboardButton('2', callback_data='2'),
        InlineKeyboardButton('3', callback_data='3'),
        InlineKeyboardButton('\u238b', callback_data='back2main'),
        InlineKeyboardButton('0', callback_data='0'),
        InlineKeyboardButton('\u27f5', callback_data='backspace'),
        ]

    footer = InlineKeyboardButton('Enter', callback_data='enter')
    reply_markup = InlineKeyboardMarkup(build_menu(keyboard, n_cols=3,
               footer_buttons=footer))
    return reply_markup


def menu_keyboard():
    keyboard = [
                [InlineKeyboardButton('Manual', callback_data='manual')],
                [InlineKeyboardButton('Info', callback_data='info')],
                [InlineKeyboardButton('Back', callback_data='back2main')]
                ]
    return InlineKeyboardMarkup(keyboard)


def manual_keyboard():
    keyboard = [InlineKeyboardButton('Galaxy', callback_data='galaxyInfo'),
                InlineKeyboardButton('Helm', callback_data='1helmInfo'),
                InlineKeyboardButton('LRS', callback_data='2lrsInfo'),
                InlineKeyboardButton('SRS', callback_data='3srsinfo'),
                InlineKeyboardButton('Phasers', callback_data='4phasersInfo'),
                InlineKeyboardButton('Torpedoes', callback_data='5torpedoesInfo'),
                InlineKeyboardButton('Shields', callback_data='6shieldsInfo'),
                InlineKeyboardButton('Back', callback_data='back2menu'),
                InlineKeyboardButton('Main ', callback_data='back2main')
                ]
    reply_markup = InlineKeyboardMarkup(build_menu(keyboard, n_cols=2))
    return reply_markup