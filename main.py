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
import numpy as np
import logging


bot = telebot.TeleBot(TOKEN)
bot_username = bot.get_me().username

markdown = """
    *bold text*
    _italic text_
    [text](URL)
    """

logging.basicConfig(level=logging.INFO, filename="log.log",
                    format="%(asctime)s %(levelname)s %(message)s", filemode="w", encoding = "UTF-8")

print('Бот запущен')

# Запись в Базу Данных
@bot.message_handler(commands=['start'])
def get_text_message(message):
    user_first_name = message.from_user.first_name
    chat_id = message.chat.id
    username = message.from_user.username
    print('Присоединился ', user_first_name, username, message.from_user.id)
    func.first_join(user_id=chat_id, username=username)
    bot.send_message(message.from_user.id, 'Привет!\nЯ - бот НБЦ для чтения Библии по плану.\n\nКраткая инструкция:\n- "Что читаем сегодня?" - нажмите чтобы узнать что читаем сегодня по плану.\n- "Отчет" - нажмите чтобы увидеть отчет о пропущенных днях.\n\nЕсли понадобится помощь - пишите сюда: @utkows', reply_markup=kb.menu)
    logging.info(f"Новый пользователь успешно добавлен в БД: {username}, {user_first_name}.")

# Вызов Админ Панели
@bot.message_handler(commands=['admin'])
def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    print(username, ' использует команду admin')
    logging.info(f"Использует команду admin: {username}, {user_id}.")
    if message.chat.id == admin:
        print(username, 'получил доступ к админке')
        logging.info(f"Получил доступ к админке: {username}, {user_id}.")
        bot.send_message(message.chat.id, ' {}, вы авторизованы!'.format(message.from_user.first_name),
                         reply_markup=kb.admin)

# Запрос, что читаем сегодня, отчет о прочитанных днях
@bot.message_handler(content_types=['text'])
def msg_user(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    if message.text == 'Что читаем сегодня?':
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today_date = tconv(message.date)
        print('Что читаем сегодня ', user_name)
        logging.info(f"Что читаем сегодня: {user_name}, {user_first_name}.")
        today = func.addiction(day = today_date)
        today = re.sub("[)|(|,)]", "", str(today))
        # print('MAIN сегодняшний день номер', today)
        logging.info(f"MAIN сегодняшний день номер: {today}, инфа для {user_name}, {user_first_name}.")
        info = func.msg_plan(day_input=today_date)
        # print('Вывожу сообщение')
        # print(info)
        if info == ([]):
            result_msg = bot.send_message(message.from_user.id, 'Что-то пошло не так.\nВсе сломалось? Пишите @utkows')
            logging.error(f"Ошибка, запрос от пользователя {user_name}, {user_first_name} пустая ячейка в БД.")
        else:
            bot.send_message(message.chat.id, f"Сегодня {today_date}, *день № {today}*", parse_mode= "Markdown")
            result_msg = bot.send_message(message.chat.id, info, reply_markup=kb.read)
            logging.info(f"Успешный вывод инфы о дне для {user_name}, {user_first_name}.")
        # print('Конец сессии')
        bot.register_next_step_handler(result_msg, reading)
    elif message.text == 'Отчет':
        print('Отчет ', user_name)
        logging.info(f"Запрос отчета от {user_name}, {user_first_name}.")
        read_data = func.whats_read(user_id = user_id)
        # print('MAIN получен список прочитанного ', read_data)
        logging.info(f"MAIN Получен список прочитанного: {read_data}, для {user_name}, {user_first_name}.")
        # func.add_to_gsheet(read_data = read_data)
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today_date = tconv(message.date)
        today = func.addiction(day = today_date)
        today = re.sub("[)|(|,)]", "", str(today))
        # print('MAIN прочитанное день', today)
        logging.info(f"MAIN прочитанное день: {today}, для {user_name}, {user_first_name}.")
        stat_read = func.stat_reading(today = today, text = read_data)
        res_msg_reading = func.result_msg_read(stat_read = stat_read, user_id = user_id)
        bot.send_message(message.chat.id, f"Сегодня {today_date}, *день № {today}*", parse_mode= "Markdown")
        stat_read_len = str(len(stat_read)-1)
        count_stat = res_msg_reading
        # print('MAIN количество пропущенных дней ', stat_read_len)
        logging.info(f"MAIN количество пропущенных дней: {stat_read_len}, для {user_name}, {user_first_name}.")
        count_day = 0
        for item in count_stat:
            if item != 0:
                count_day += 1
        count_res = str(int(today) - count_day)
        # print('MAIN опережение на ', count_res)
        logging.info(f"MAIN опережение на: {count_res}, для {user_name}, {user_first_name}.")
        if count_res < '0' == stat_read_len:
            count_res = re.sub("[-]", "", count_res)
            bot.send_message(message.from_user.id, f'Вы опережаете план на *{count_res}* дней!', parse_mode= "Markdown", reply_markup=kb.input_read_advance)
        elif stat_read_len == '0':
                bot.send_message(message.from_user.id, '*Все по плану!*', parse_mode= "Markdown", reply_markup=kb.input_read_all_list)
        else:
            count_stat = stat_read
            count_day = 0
            for i in count_stat:
                if i != 0:
                    count_day += 1
            # print('MAIN количество пропущенных дней ', count_day)
            logging.info(f"MAIN количество пропущенных дней: {count_day}, для {user_name}, {user_first_name}.")
            stat_read_msg = ', '.join([f'{stat_read_msg}' for stat_read_msg in stat_read])
            stat_read_msg = stat_read_msg.replace("0, ", "")
            # print('MAIN сформирован список пропущенных дней ', stat_read_msg)
            logging.info(f"MAIN сформирогван список пропущенных дней: {stat_read_msg}, для {user_name}, {user_first_name}.")
            bot.send_message(message.from_user.id, f'*Вы пропустили дни №:*\n\n{stat_read_msg}\n\nВы отстаете на *{count_day}* дней.', parse_mode= "Markdown")
            bot.send_message(message.from_user.id, 'Чтобы прочитать пропущенные дни, нажмите кнопку внизу и введите нужный номер дня из списка выше.', reply_markup=kb.input_read)
    elif message.text == 'Весь список прочитанного':
        print('Список прочитанного ', user_name)
        read_data = func.whats_read(user_id = user_id)
        # print('MAIN вывожу список прочитанного ', read_data)
        logging.info(f"MAIN вывожу список прочитанного: {read_data}, для {user_name}, {user_first_name}.")
        text = ' '.join([f'{read_data}' for read_data in read_data])
        text = re.sub("[)|(|')]", "", text)
        text = text.replace(",,", ",")
        bot.send_message(message.from_user.id, f'*Список прочитанных дней:*\n\n {text}', parse_mode= "Markdown", reply_markup=kb.input_read_all_list)
    elif message.text == 'Ввести день вручную':
        print('Вводит день вручную ', user_name)
        logging.info(f"Вводит день вручную {user_name}, {user_first_name}.")
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        msg = bot.send_message(message.from_user.id, f'Введите порядковый номер дня в формате "1", например сегодня день № *{today}*.', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day)
    elif message.text == 'Отметить все дни как прочитанные':
        logging.info(f"Отметить все дни как прочитанные {user_name}, {user_first_name}.")
        read_data = func.whats_read(user_id = user_id)
        logging.info(f"MAIN Получен список прочитанного: {read_data}, для {user_name}, {user_first_name}.")
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        logging.info(f"MAIN прочитанное день: {today}, для {user_name}, {user_first_name}.")
        stat_read = func.stat_reading(today = today, text = read_data)
        res_msg_reading = func.result_msg_read(stat_read = stat_read, user_id = user_id)
        res_msg_reading_len = str(len(res_msg_reading))
        # print(f'Количество прочитанных дней {res_msg_reading_len}, сегодня день номер {today}')
        if int(res_msg_reading_len) < int(today):
            msg = bot.send_message(message.from_user.id, f'*Внимание!*\nПосле выполнения этого действия все пропущенные дни будут отмечены как прочитанные, в том числе и *сегодняшний*.\nВы уверены что хотите это сделать?', parse_mode= "Markdown", reply_markup=kb.yes_no)
            bot.register_next_step_handler(msg, check_all)
        else:
            bot.send_message(message.chat.id, "Нет непрочитанных дней!", parse_mode= "Markdown", reply_markup=kb.menu)
    elif message.text == 'Удалить отметку о прочтении':
            logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
            msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
            bot.register_next_step_handler(msg, delete_check)
    elif message.text == 'Канал НБЦ':
            print('Ссылка на канал ', user_name)
            logging.info(f"Ссылка на канал {user_name}, {user_first_name}.")
            bot.send_message(message.chat.id, "*Подписывайтесь!*\nhttps://t.me/nbcnnov", parse_mode= "Markdown", reply_markup=kb.menu)
    elif message.text == 'Помощь':
            logging.info(f"Помощь {user_name}, {user_first_name}.")
            bot.send_document(message.chat.id, document=open('FAQ.jpg', 'rb'))
            bot.send_message(message.chat.id, f'Если вашего вопроса нет в списке, или у вас есть предложение по улучшению бота, напишите сообщение, нажав кнопку внизу.', parse_mode= "Markdown", reply_markup=kb.quesch)
    elif message.text == 'Отправить сообщение':
            msg = bot.send_message(message.chat.id, "Пожалуйста, введите ваше сообщение", reply_markup=kb.back)
            bot.register_next_step_handler(msg, quesch)
    elif message.text == 'Назад':
            logging.info(f"Нажал Назад в гл.меню {user_name}, {user_first_name}.")
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        logging.info(f"Ошибка, некорректное значение при вводе в гл.меню {user_name}, {user_first_name}.")
        bot.send_message(message.chat.id, "Не понимаю :(\nПожалуйста, используйте кнопки!", reply_markup=kb.menu)

# Функция получение информации о введенном вручную дне
def input_day(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    generate_alldays = sorted(map(str, range(1, 365+1)))
    text = message.text
    global value_input
    if message.text == 'Назад':
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.menu)
    elif text.isdigit()==False:
        logging.info(f"Введено некорректное значение при ручном вводе дня {user_name}, {user_first_name}.")
        bot.send_message(message.from_user.id, 'Пожалуйста, введите корректное значение!', reply_markup=kb.input_read)
    elif text.isdigit():
        for i in generate_alldays:
            if i == text:        
                value_input = func.user_input(value = text)
                value = func.value_plan(value_input = value_input)
                msg = bot.send_message(message.from_user.id, value, reply_markup=kb.read)
                bot.register_next_step_handler(msg, reading_input)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, введите значение!', reply_markup=kb.input_read)

# Функция отметка о прочтении введенного вручную дня
def reading_input(message):
    text = message.text
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    user_id = message.from_user.id
    if text == "Прочитано!":
            print('Отметка о прочтении (вручн) ', user_name)
            logging.info(f"Отметка о прочтении (вручн) {user_name}, {user_first_name}.")
            func.addiction(day = value_input)
            func.reading(user_id = user_id)
            bot.send_message(message.from_user.id, 'Отлично!', reply_markup=kb.menu)
    elif text == 'Назад':
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!')
        logging.info(f"Введено некорректное значение при отметке прочитанного (вручн) {user_name}, {user_first_name}.")

# Функция по отметке прочитанного (авто)
def reading(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if text == "Прочитано!":
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today_date = tconv(message.date)
        print('Отметка о прочтении (авто) ', user_name)
        logging.info(f"Отметка о прочтении (авто) {user_name}, {user_first_name}.")
        func.addiction(day = today_date)
        func.reading(user_id = user_id)
        bot.send_message(message.from_user.id, 'Отлично!', reply_markup=kb.menu)
    elif text == 'Назад':
        bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!')
        logging.info(f"Введено некорректное значение при отметке прочитанного (авто) {user_name}, {user_first_name}.")

# Функция по отметке всех пропущенных дней
def check_all(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if text == 'Нет!':
        bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.menu)
    elif text == 'Да!':
        print('Отметка о прочтении (все дни) ', user_name)
        logging.info(f"Отметка о прочтении (все дни) {user_name}, {user_first_name}.")
        read_data = func.whats_read(user_id = user_id)
        # print('MAIN получен список прочитанного ', read_data)
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        stat_read = func.stat_reading(today = today, text = read_data)
        func.check_all(user_id = user_id, stat_read = stat_read)
        logging.info(f"Отметка о прочтении всех пропущенных дней {user_name}, {user_first_name}.")
        bot.send_message(message.chat.id, "Пропущенные дни отмечены как прочитанные!", reply_markup=kb.menu)
    else:
        bot.send_message(message.from_user.id, "Пожалуйста, используйте кнопки!", reply_markup=kb.menu)

def delete_check(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if text == 'Назад':
        bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        logging.info(f"Успешное удаление отметки о прочтении дня {text}, для {user_name}, {user_first_name}.")
        func.delete_check(user_id = user_id, delete_day = text)
        bot.send_message(message.from_user.id, f"Отметка о прочтении {text}-го дня удалена", reply_markup=kb.menu)

def quesch(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if message.text == 'Назад':
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        logging.info(f"Отправка сообщения от {user_name}, {user_first_name}.")
        info = admin
        bot.send_message(message.chat.id, text=' Ваше сообщение отправляется')
        bot.send_message(info, f'Входящее сообщение!\n\nID: {user_id}\nUsername: @{user_name}\nИмя: {user_first_name}\n\nСообщение: {str(text)}')
        bot.send_message(message.chat.id, text=' Сообщение отправлено!\nПостараемся ответить на него в ближайшее время!', reply_markup=kb.menu)



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
            msg = bot.send_message(chat_id=chat_id, text='Введите текст для рассылки. \n\nДля отмены нажми Назад!', reply_markup=kb.back)
            bot.register_next_step_handler(msg, message1)
    elif call.data == 'logging': 
        bot.send_document(chat_id=chat_id, document=open('log.log', 'rb'))
    elif call.data == 'admin_msg_user':
            chat_id = call.message.chat.id
            text = call.message.text
            msg = bot.send_message(chat_id=chat_id, text='Введите ID пользователя. \n\nДля отмены нажми Назад!', reply_markup=kb.back)
            bot.register_next_step_handler(msg, admin_msg_user_id)

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
        # print (info)

def admin_msg_user_id(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if message.text == 'Назад':
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        global info_user
        info_user = text
        msg = bot.send_message(message.chat.id, text=f' ID {text} записан, введи сообщение.')
        bot.register_next_step_handler(msg, admin_msg_user)

def admin_msg_user(message):
    user_id = message.from_user.id
    text = message.text
    info_user_id = info_user
    bot.send_message(info_user_id, f'Входящее сообщение!\n\n{str(text)}')
    bot.send_message(message.chat.id, text=' Сообщение отправлено!')

# Поддержание работы
bot.polling(none_stop=True)
bot.infinity_polling()