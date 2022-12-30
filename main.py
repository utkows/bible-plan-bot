from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Google
gscope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
gcredentials = 'parameters.json'
gdocument = 'bd_bot'

import telebot
from telebot import types
import time
from config import TOKEN, admin
import sqlite3
import keyboard as kb
import config as config
import functions as func
from config import db, TOKEN
import codecs
import re


bot = telebot.TeleBot(TOKEN)
bot_username = bot.get_me().username

# Запись в Базу Данных
@bot.message_handler(commands=['start'])
def get_text_message(message):
    chat_id = message.chat.id
    username = message.from_user.username
    print('Присоединился ', username, message.from_user.id)
    func.first_join(user_id=chat_id, username=username)
    bot.send_message(message.from_user.id, 'Привет!\nЯ - бот НБЦ для чтения Библии по плану.\n\nКраткая инструкция:\n- "Что читаем сегодня?" - нажмите чтобы узнать что читаем сегодня по плану.\n- "Прочитанное" - нажмите чтобы увидеть отчет о прочитанных днях.\n- "Ввести день вручную" - введите номер дня, чтобы узнать что мы читали в этот день.\n\nЕсли понадобится помощь - пишите сюда: @utkows', reply_markup=kb.menu)

# Рассылка
@bot.message_handler(commands=['send'])
def message1(message):
    print('MAIN получена комманда на рассылку')
    admins = [316920734]
    chat_id = message.chat.id
    text = message.text
    command_sender = message.from_user.id
    if command_sender in admins:
        print('MAIN команда от админа')
        msg = bot.send_message(chat_id=chat_id, text='Введите текст для рассылки. \n\nДля отмены нажми Назад без кавычек!', reply_markup=kb.back)
        bot.register_next_step_handler(msg, message1)
    else:
        print('MAIN команда НЕ от админа')
        bot.send_message(command_sender, f'Не выйдет, извини :(')
def message1(message):
    text = message.text
    if message.text == 'Назад':
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        info = func.admin_message(text)
        bot.send_message(message.chat.id, text=' Рассылка начата!')
        for i in range(len(info)):
            try:
                time.sleep(1)
                bot.send_message(info[i][0], str(text))
            except:
                pass
        bot.send_message(message.chat.id, text=' Рассылка завершена!')
        print (info)

# Вызов Админ Панели
@bot.message_handler(commands=['admin'])
def start(message: types.Message):
    if message.chat.id == admin:
        bot.send_message(message.chat.id, ' {}, вы авторизованы!'.format(message.from_user.first_name),
                         reply_markup=kb.admin)

# Запрос, что читаем сегодня, отчет о прочитанных днях
@bot.message_handler(content_types=['text'])
def msg_user(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    if message.text == 'Что читаем сегодня?':
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        message1 = tconv(message.date)
        print('Пишет', user_name)
        text_message = message1
        global day
        day = text_message
        today = func.addiction(day = day)
        today = re.sub("[)|(|,)]", "", str(today))
        print('MAIN сегодняшний день номер', today)
        info = func.msg_plan(day_input=text_message)
        print('Вывожу сообщение')
        print(info)
        if info == ([]):
            result_msg = bot.send_message(message.from_user.id, 'Что-то пошло не так.\nВсе сломалось? Пишите @utkows')
        else:
            bot.send_message(message.chat.id, "День № {}".format(today))
            result_msg = bot.send_message(message.chat.id, info, reply_markup=kb.read)
        print('Конец сессии')
        bot.register_next_step_handler(result_msg, reading)
    elif message.text == 'Прочитанное':
        read_data = func.whats_read(user_id = user_id)
        print('MAIN получен список прочитанного ', read_data)
        text = ''.join([f'{read_data}' for read_data in read_data])
        text = re.sub("[)|(|')]", "", text)
        text = text.replace(",,", ",")
        func.add_to_gsheet(read_data = text)
        tconv = lambda x: time.strftime("%d.%m", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        print('MAIN прочитанное день', today)
        bot.send_message(message.chat.id, "Сегодня день № {}".format(today))
        bot.send_message(message.from_user.id, 'Отчет о прочитанных днях:')
        bot.send_message(message.from_user.id, text)
        bot.send_message(message.from_user.id, 'Если видите что какого-то номера не хватает - нажмите кнопку "Ввести день вручную" и введите недостающий номер. Затем нажмите кнопку "Прочитано".', reply_markup=kb.input_read)
    elif message.text == 'Ввести день вручную':
        msg = bot.send_message(message.from_user.id, 'Введите порядковый номер дня в формате "1".', reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day)
    elif message.text == 'Назад':
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        bot.send_message(message.chat.id, "Не понимаю :(\nПожалуйста, используйте кнопки!", reply_markup=kb.menu)

# Функция получение информации о введенном вручную дне
def input_day(message):
    user_id = message.from_user.id
    text = message.text
    global value_input
    if message.text == 'Назад':
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        value_input = func.user_input(value=text)
        value = func.value_plan(value_input = value_input)
        msg = bot.send_message(message.from_user.id, value, reply_markup=kb.read)
        bot.register_next_step_handler(msg, reading_input)

# Функция отметка о прочтении введенного вручную дня
def reading_input(message):
    text = message.text
    user_id = message.from_user.id
    if text == "Прочитано!":
            func.addiction(day = value_input)
            func.reading(user_id = user_id)
            bot.send_message(message.from_user.id, 'Молодец!', reply_markup=kb.menu)
    elif text == 'Назад':
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        bot.send_message(message.from_user.id, 'Все сломалось. Нажмите "Назад"')

# Функция по отметке прочитанного (авто)
def reading(message):
    user_id = message.from_user.id
    text = message.text
    if text == "Прочитано!":
            func.addiction(day = day)
            func.reading(user_id = user_id)
            bot.send_message(message.from_user.id, 'Молодец!', reply_markup=kb.menu)
    elif text == 'Назад':
            bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        bot.send_message(message.from_user.id, 'Все сломалось. Напишите еще раз сегодняшний день и "Прочитано"')


#Функции бота
@bot.callback_query_handler(func=lambda call: True)   
def handler_call(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id
    if call.data == 'statistics':
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=func.stats(), reply_markup=kb.admin)
    elif call.data == 'whats_read':
        bot.send_message(call.from_user.id)
    elif call.data == 'Прочитанное':
        read_data = func.whats_read(user_id = user_id)
        print('MAIN получен список прочитанного ', read_data)
        text = ''.join([f'{read_data}' for read_data in read_data])
        text = re.sub("[)|(|')]", "", text)
        text = text.replace(",,", ",")
        func.add_to_gsheet(read_data = text)
        bot.send_message(call.from_user.id, 'Вот список прочитанного:')
        bot.send_message(call.from_user.id, text)



# Поддержание работы
bot.polling(none_stop=True)
bot.infinity_polling()