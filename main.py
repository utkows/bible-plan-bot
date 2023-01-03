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
from collections import Counter


bot = telebot.TeleBot(TOKEN)
bot_username = bot.get_me().username

markdown = """
    *bold text*
    _italic text_
    [text](URL)
    """

print('Бот запущен')

# Запись в Базу Данных
@bot.message_handler(commands=['start'])
def get_text_message(message):
    chat_id = message.chat.id
    username = message.from_user.username
    print('Присоединился ', username, message.from_user.id)
    func.first_join(user_id=chat_id, username=username)
    bot.send_message(message.from_user.id, 'Привет!\nЯ - бот НБЦ для чтения Библии по плану.\n\nКраткая инструкция:\n- "Что читаем сегодня?" - нажмите чтобы узнать что читаем сегодня по плану.\n- "Отчет" - нажмите чтобы увидеть отчет о пропущенных днях.\n\nЕсли понадобится помощь - пишите сюда: @utkows', reply_markup=kb.menu)

# Вызов Админ Панели
@bot.message_handler(commands=['admin'])
def start(message: types.Message):
    username = message.from_user.username
    print(username, ' использует команду admin')
    if message.chat.id == admin:
        print(username, 'получил доступ к админке')
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
        # print('MAIN сегодняшний день номер', today)
        info = func.msg_plan(day_input=text_message)
        # print('Вывожу сообщение')
        print(info)
        if info == ([]):
            result_msg = bot.send_message(message.from_user.id, 'Что-то пошло не так.\nВсе сломалось? Пишите @utkows')
        else:
            bot.send_message(message.chat.id, "День № {}".format(today))
            result_msg = bot.send_message(message.chat.id, info, reply_markup=kb.read)
        print('Конец сессии')
        bot.register_next_step_handler(result_msg, reading)
    elif message.text == 'Отчет':
        read_data = func.whats_read(user_id = user_id)
        # print('MAIN получен список прочитанного ', read_data)
        text = ''.join([f'{read_data}' for read_data in read_data])
        text = re.sub("[)|(|')]", "", text)
        text = text.replace(",,", ",")
        func.add_to_gsheet(read_data = text)
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        # print('MAIN прочитанное день', today)
        stat_read = func.stat_reading(today = today, text = text)
        bot.send_message(message.chat.id, "Сегодня день № {}".format(today))
        # bot.send_message(message.from_user.id, 'Отчет о пропущенных днях:')
        stat_read = stat_read.replace("0,", "")
        count_stat = text
        count_stat = re.sub("[ |,|0)]", "", count_stat)
        count_day = 0
        for item in count_stat:
            if item != 0:
                count_day += 1
        count_res = str(int(today) - count_day)
        # print('MAIN опережение на ', count_res)
        if count_res >= '0':
            if stat_read == '0':
                bot.send_message(message.from_user.id, '*Отставания нет, отлично!*\n\nЕсли хотите опередить всех - нажмите кнопку внизу и введите номер следующего дня, который хотите прочитать.', parse_mode= "Markdown", reply_markup=kb.input_read)
            else:
                stat_read = stat_read.replace("0,", "")
                count_stat = stat_read
                count_stat = re.sub("[ |,|0)]", "", count_stat)
                count_day = 0
                for item in count_stat:
                    if item != 0:
                        count_day += 1
                # print('MAIN количество прочитанных дней ', count_day)
                bot.send_message(message.from_user.id, f'*Вы пропустили дни №:*\n\n{stat_read}\n\nВы отстаете на *{count_day}* дней', parse_mode= "Markdown")
                bot.send_message(message.from_user.id, 'Чтобы прочитать пропущенные дни, нажмите кнопку внизу и введите нужный номер дня из списка выше.', reply_markup=kb.input_read)
        else:
            count_res = re.sub("[-]", "", count_res)
            bot.send_message(message.from_user.id, f'Вы опережаете план на *{count_res}* дней!', parse_mode= "Markdown", reply_markup=kb.input_read_advance)
    elif message.text == 'Весь список прочитанного':
        read_data = func.whats_read(user_id = user_id)
        text = ''.join([f'{read_data}' for read_data in read_data])
        text = re.sub("[)|(|')]", "", text)
        text = text.replace(",,", ",")
        bot.send_message(message.from_user.id, f'*Список прочитанных дней:*\n\n {text}', parse_mode= "Markdown", reply_markup=kb.input_read)

    elif message.text == 'Ввести день вручную':
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        msg = bot.send_message(message.from_user.id, f'Введите порядковый номер дня в формате "1", например сегодня день № *{today}*.', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day)
    elif message.text == 'Канал НБЦ':
            bot.send_message(message.chat.id, "*Подписывайтесь!*\nhttps://t.me/nbcnnov", parse_mode= "Markdown", reply_markup=kb.menu)
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
        for i in text:
            if i.isdigit() is not True:
                bot.send_message(message.chat.id, "Введите корректный номер!", reply_markup=kb.input_read)
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
        bot.send_message(message.from_user.id, 'Зачем это сделал?. Управляй ботом кнопками!')


#Функции бота (админ)
@bot.callback_query_handler(func=lambda call: True)   
def handler_call(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id
    if call.data == 'statistics':
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=func.stats(), reply_markup=kb.admin)
    elif call.data == 'admin_msg':
            chat_id = call.message.chat.id
            text = call.message.text
            msg = bot.send_message(chat_id=chat_id, text='Введите текст для рассылки. \n\nДля отмены нажми Назад без кавычек!', reply_markup=kb.back)
            bot.register_next_step_handler(msg, message1)

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

# Поддержание работы
bot.polling(none_stop=True)
bot.infinity_polling()