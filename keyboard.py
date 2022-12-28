from telebot import types
import sqlite3


import functions as func

admin = types.InlineKeyboardMarkup(row_width=2)
admin.add(
    types.InlineKeyboardButton('Рассылка',callback_data='message'),
    types.InlineKeyboardButton('Статистика', callback_data='statistics'),
    types.InlineKeyboardButton('Назад', callback_data='menu')
)

menu = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
menu.add(
    types.KeyboardButton(''),
    types.KeyboardButton(''),
    types.KeyboardButton('')
)