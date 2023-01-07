from telebot import types
import sqlite3


# import functions as func

admin = types.InlineKeyboardMarkup(row_width=2)
admin.add(
    types.InlineKeyboardButton('Рассылка', callback_data='admin_msg'),
    types.InlineKeyboardButton('Сообщение пользователю', callback_data='admin_msg_user'),
    types.InlineKeyboardButton('Статистика', callback_data='statistics'),
    types.InlineKeyboardButton('Логи', callback_data='logging')
)

menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
menu.add(
    types.InlineKeyboardButton('Что читаем сегодня?', callback_data='whats_read'),
    types.InlineKeyboardButton('Отчет', callback_data='reading'),
    types.InlineKeyboardButton('Помощь', callback_data='help'),
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
    types.InlineKeyboardButton('Отметить все дни как прочитанные', callback_data='check_all_days'),
    types.InlineKeyboardButton('Удалить отметку о прочтении', callback_data='input_day'),
    types.InlineKeyboardButton('Назад', callback_data='back')
)

input_read_advance = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
input_read_advance.add(
    types.InlineKeyboardButton('Ввести день вручную', callback_data='input_day'),
    types.InlineKeyboardButton('Весь список прочитанного', callback_data='input_day_advance'),
    types.InlineKeyboardButton('Удалить отметку о прочтении', callback_data='input_day'),
    types.InlineKeyboardButton('Назад', callback_data='back')
)

yes_no = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
yes_no.add(
    types.InlineKeyboardButton('Да!', callback_data='yes'),
    types.InlineKeyboardButton('Нет!', callback_data='no'),
)

input_read_all_list = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
input_read_all_list.add(
    types.InlineKeyboardButton('Ввести день вручную', callback_data='input_day'), 
    types.InlineKeyboardButton('Удалить отметку о прочтении', callback_data='input_day'),
    types.InlineKeyboardButton('Назад', callback_data='back')
)


quesch = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
quesch.add(
    types.InlineKeyboardButton('Отправить сообщение', callback_data='send_msg'),
    types.InlineKeyboardButton('Назад', callback_data='back'),
)