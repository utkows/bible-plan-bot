from telebot import types
import sqlite3


# import functions as func

admin = types.InlineKeyboardMarkup(row_width=2)
admin.add(
    types.InlineKeyboardButton('Прочитанное', callback_data='reading'),
    types.InlineKeyboardButton('Статистика', callback_data='statistics'),
    types.InlineKeyboardButton('Назад', callback_data='menu')
)

menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
menu.add(
    types.InlineKeyboardButton('Что читаем сегодня?', callback_data='whats_read'),
    types.InlineKeyboardButton('Отчет', callback_data='reading'),
    types.InlineKeyboardButton('Канал НБЦ', callback_data='nbc')
)

read = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
read.add(
    types.InlineKeyboardButton('Прочитано!', callback_data='read'),
    types.InlineKeyboardButton('Назад', callback_data='back'),
)

back = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
back.add(
    types.InlineKeyboardButton('Назад', callback_data='back'),
)

input_read = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
input_read.add(
    types.InlineKeyboardButton('Ввести день вручную', callback_data='input_day'),
    types.InlineKeyboardButton('Назад', callback_data='back')
)