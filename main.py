from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Google
gscope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
gcredentials = 'parameters.json'
gdocument = 'bd_bot'

import telebot
from telebot import types
import time
from datetime import datetime
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
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from tzlocal import get_localzone


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
    bot.send_message(message.from_user.id, '👋 Здравствуйте!\nЭто бот Нижегородской Библейской Церкви для чтения Библии по плану.\n\n❗️Вначале рекомендуем ознакомиться с инструкцией по [ссылке](https://telegra.ph/Plan-chteniya-Biblii-NBC-bot-01-10)', parse_mode= "Markdown", reply_markup=kb.menu)
    logging.info(f"Новый пользователь успешно добавлен в БД: {username}, {user_first_name}.")



# Функция автоотправки ежедневных напоминаний с функцией удаления инлайн-кнопки у предыдущего напоминания каждого пользователя и чисткой id в бд
def whats_read_evday():
    print('Ежедневные напоминания запущены')
    tconv = time.strftime("%d.%m.%Y")
    today_date = tconv
    inline_today = func.addiction_stat(day = today_date)
    info_msg = func.msg_plan(day_input=today_date)
    users = func.admin_message()
    for i in range(len(users)):
        rem_select = func.reminder_select(user_id = users[i][0])
        try:
            # print("MAIN получены id сообщений для удаления", rem_select)
            for m in range(len(rem_select)):
                try:
                    time.sleep(1)
                    func.reminder_delete(user_id = users[i][0], message_id = rem_select[m][0])
                    bot.edit_message_reply_markup(users[i][0], message_id = rem_select[m][0], reply_markup = '')
                except:
                    pass
        except:
                pass
        try:
            time.sleep(1)
            msg = bot.send_message(users[i][0], f'☀️ Доброе утро!\n📆 Сегодня {today_date}, *день №{inline_today}*\n\n📖 Читаем *{info_msg}*', parse_mode= "Markdown", reply_markup=kb.inline_read)
            message_id = msg.message_id
            # print('MAIN ID отправленных сообщений ', message_id)
            func.reminder_add(user_id = users[i][0], message_id = message_id)
        except:
            pass
    print('Ежедневные напоминания отправлены')

# Параметры расписания
tz = get_localzone()
scheduler = BackgroundScheduler(timezone=tz)
scheduler.add_job(whats_read_evday, 'cron', hour='6', minute='0')
scheduler.start()

# Отметка о прочтении inline
@bot.callback_query_handler(func=lambda call: call.data == 'inline_read')  
def inline_reading(check):
    user_id = check.from_user.id
    user_name = check.from_user.username
    user_first_name = check.from_user.first_name
    tconv = time.strftime("%d.%m.%Y")
    today_date = tconv
    today = func.addiction_stat(day = today_date)
    print('Отметка о прочтении (инлайн) ', user_name, user_first_name)
    logging.info(f"Отметка о прочтении (инлайн) {user_name}, {user_first_name}.")
    info_msg = func.msg_plan(day_input=today_date)
    func.reading(user_id = user_id)
    rem_select = func.reminder_select(user_id = user_id)
    try:
        func.reminder_delete(user_id = user_id, message_id = rem_select[0][0])
    except:
        pass
    bot.edit_message_text(chat_id=check.message.chat.id, message_id=check.message.message_id, text=f"☀️ Доброе утро!\n📆 Сегодня {today_date}, *день №{today}*\n\n📖 Читаем *{info_msg}*\n\n✅ Прочитано!", parse_mode= "Markdown", reply_markup=None)




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
    # Цикл удаления инлайн-кнопки у автосообщения и id из бд
    rem_select = func.reminder_select(user_id = user_id)
    try:
        bot.edit_message_reply_markup(message.chat.id, message_id = rem_select, reply_markup = '')
        func.reminder_delete(user_id = user_id, message_id = rem_select[0][0])
    except:
        pass
    if message.text == '🎁 Что читаем сегодня?':
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today_date = tconv(message.date)
        print('Что читаем сегодня ', user_name, user_first_name)
        logging.info(f"Что читаем сегодня: {user_name}, {user_first_name}.")
        today = func.addiction_stat(day = today_date)
        info = func.msg_plan(day_input=today_date)
        if info == ([]):
            result_msg = bot.send_message(message.from_user.id, 'Что-то пошло не так.\nВсе сломалось? Пишите @utkows')
            logging.error(f"Ошибка, запрос от пользователя {user_name}, {user_first_name} пустая ячейка в БД.")
        else:
            bot.send_message(message.chat.id, f"Сегодня {today_date}, *день № {today}*", parse_mode= "Markdown")
            result_msg = bot.send_message(message.chat.id, info, reply_markup=kb.read)
            logging.info(f"Успешный вывод инфы о дне для {user_name}, {user_first_name}.")
        # print('Конец сессии')
        bot.register_next_step_handler(result_msg, reading)
    elif message.text == '📊 Отчет':
        print('Отчет ', user_name, user_first_name)
        logging.info(f"Запрос отчета от {user_name}, {user_first_name}.")
        read_data = func.whats_read(user_id = user_id)
        # print('MAIN получен список прочитанного ', read_data)
        # func.add_to_gsheet(read_data = read_data)
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today_date = tconv(message.date)
        today = func.addiction_stat(day = today_date)
        today = re.sub("[)|(|,)]", "", str(today))
        # print('MAIN прочитанное день', today)
        stat_read = func.stat_reading(today = today, text = read_data)
        res_msg_reading = func.result_msg_read(stat_read = stat_read, user_id = user_id)
        stat_read_full = func.stat_read_full(stat_read)
        bot.send_message(message.chat.id, f"Сегодня {today_date}, *день № {today}*", parse_mode= "Markdown")
        stat_read_len = str(len(stat_read)-1)
        count_stat = str(len(res_msg_reading))
        # print('MAIN количество пропущенных дней ', stat_read_len)
        # print('MAIN количество прочитанных дней ', count_stat)
        today_verify = func.today_verify(user_id, today)
        # print('today_verify ', today_verify)
        # print('today ', today)
        count_res = str(int(today) - int(count_stat))
        # print('MAIN опережение на ', count_res)
        if int(today) - int(stat_read_len) == int(today) and count_res < '0' and str(today_verify) == str(today):
            count_res = re.sub("[-]", "", count_res)
            bot.send_message(message.from_user.id, f'📈 Вы опережаете план на *{count_res}* дней!', parse_mode= "Markdown", reply_markup=kb.input_read_advance)
        elif stat_read_len == '0':
            today_verify = func.today_verify(user_id, today)
            if today_verify is None:
                tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
                today_date = tconv(message.date)
                today = func.addiction_stat(day = today_date)
                info = func.msg_plan(day_input=today_date)
                bot.send_message(message.from_user.id, f'*🎇 Все по плану!*\n\n⚡️ Не забудьте почитать сегодня:  *{info}*', parse_mode= "Markdown", reply_markup=kb.input_read_all_list)
            else:
                bot.send_message(message.from_user.id, '*🎇 Все по плану!*', parse_mode= "Markdown", reply_markup=kb.input_read_all_list)
        else:
            count_stat = stat_read
            count_day = 0
            for i in count_stat:
                if i != 0:
                    count_day += 1
            # print('MAIN количество пропущенных дней ', count_day)
            if count_day < 8:
                logging.info(f"MAIN сформирован список пропущенных дней: {stat_read_full}, для {user_name}, {user_first_name}.")
                bot.send_message(message.from_user.id, f'📉 *Вы пропустили дни №:*\n\n{stat_read_full}\n\n⏳ Вы отстаете на *{count_day}* дней.', parse_mode= "Markdown")
                msg = bot.send_message(message.from_user.id, 'Чтобы отметить пропущенные дни, нажмите кнопку внизу и введите нужный номер дня из списка выше.', reply_markup=kb.check)
                bot.register_next_step_handler(msg, reading_input)
            else:
                stat_read_msg = ', '.join([f'{stat_read_msg}' for stat_read_msg in stat_read])
                logging.info(f"MAIN сформирован список пропущенных дней: {stat_read_msg}, для {user_name}, {user_first_name}.")
                stat_read_msg = stat_read_msg[:0][:1] + stat_read_msg[(2):]
                bot.send_message(message.from_user.id, f'📉 *Вы пропустили дни №:*\n\n{stat_read_msg}\n\n⏳ Вы отстаете на *{count_day}* дней.', parse_mode= "Markdown")
                bot.send_message(message.from_user.id, 'Чтобы посмотреть что нужно прочитать в эти пропущенные дни, нажмите кнопку внизу и введите нужный номер дня из списка выше.', reply_markup=kb.statistics)
    elif message.text == '🗞 Показать все прочитанные дни':
        print('Список прочитанного ', user_name, user_first_name)
        read_data = func.whats_read(user_id = user_id)
        # print('MAIN вывожу список прочитанного ', read_data)
        logging.info(f"Показать все прочитанные дни: {read_data}, для {user_name}, {user_first_name}.")
        text = ' '.join([f'{read_data}' for read_data in read_data])
        text = re.sub("[)|(|')]", "", text)
        text = text.replace(",,", ",")
        bot.send_message(message.from_user.id, f'*Список прочитанных дней:*\n\n {text}', parse_mode= "Markdown", reply_markup=kb.input_read_all_list)
    elif message.text == '✍️ Ввести номер дня':
        print('Вводит день вручную ', user_name, user_first_name)
        logging.info(f"Вводит день вручную {user_name}, {user_first_name}.")
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction_stat(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        msg = bot.send_message(message.from_user.id, f'Введите порядковый номер дня в формате "1", например сегодня день № *{today}*.', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day)
    elif message.text == '🗓 Отметить дни как прочитанные':
        msg = bot.send_message(message.from_user.id, f'Выберите действие', reply_markup=kb.check)
        bot.register_next_step_handler(msg, check)
    elif message.text == '✍️ Ввести другой день':
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction_stat(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        msg = bot.send_message(message.from_user.id, f'Введите порядковый номер дня в формате "1", например сегодня день № *{today}*.', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day)
    elif message.text == '✍️ Отметить день':
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_sev_days)
    elif message.text == '✅ Всё прочитано':
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction_stat(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        read_data = func.whats_read(user_id = user_id)
        stat_read = func.stat_reading(today = today, text = read_data)
        res_msg_reading = func.result_msg_read(stat_read = stat_read, user_id = user_id)
        res_msg_reading_len = str(len(stat_read))
        # print('MAIN пропущенных дней', res_msg_reading_len)
        if int(res_msg_reading_len) > 1:
            msg = bot.send_message(message.from_user.id, f'❗️ *Внимание!*\nПосле выполнения этого действия все пропущенные дни будут отмечены как прочитанные.\nВы уверены что хотите это сделать?', parse_mode= "Markdown", reply_markup=kb.yes_no)
            bot.register_next_step_handler(msg, check_all)
        else:
            bot.send_message(message.chat.id, "Нет непрочитанных дней!", parse_mode= "Markdown", reply_markup=kb.menu)
    elif message.text == '❌ Удалить отметку о прочтении':
            print('Удалить отметку о прочтении ', user_name, user_first_name)
            logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
            msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
            bot.register_next_step_handler(msg, delete_check)
    elif message.text == '❌ Удалить другой день':
            print('Удалить другой день ', user_name, user_first_name)
            logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
            msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
            bot.register_next_step_handler(msg, delete_check)
    elif message.text == '🆘 Помощь':
            print('Помощь ', user_name, user_first_name)
            logging.info(f"Помощь {user_name}, {user_first_name}.")
            bot.send_message(message.chat.id, f'Ответы на самые частые вопросы вы сможете найти по [ссылке](https://telegra.ph/Plan-chteniya-Biblii-NBC-bot-01-10)', parse_mode= "Markdown")
            bot.send_message(message.chat.id, f'Если вашего вопроса нет в списке, или у вас есть предложение по улучшению бота, напишите сообщение, нажав кнопку внизу 👇', parse_mode= "Markdown", reply_markup=kb.quesch)
    elif message.text == '✉️ Отправить сообщение':
            logging.info(f"Отправить сообщение {user_name}, {user_first_name}.")
            msg = bot.send_message(message.chat.id, "Пожалуйста, введите ваше сообщение", reply_markup=kb.back)
            bot.register_next_step_handler(msg, quesch)
    elif message.text == '🔙 Назад':
            logging.info(f"Нажал Назад в гл.меню {user_name}, {user_first_name}.")
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.menu)    
    else:
        logging.info(f"Ошибка, некорректное значение при вводе в гл.меню {user_name}, {user_first_name}.")
        bot.send_message(message.chat.id, "Пожалуйста, воспользуйтесь кнопками!", reply_markup=kb.menu)

# Функция получение информации о введенном вручную дне
def input_day(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    generate_alldays = sorted(map(str, range(1, 365+1)))
    text = message.text
    global value_input
    if message.text == '🔙 Назад':
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.check)
    elif text.isdigit()==False:
        logging.info(f"Введено некорректное значение при ручном вводе дня {user_name}, {user_first_name}.")
        bot.send_message(message.from_user.id, 'Пожалуйста, введите корректное значение!', reply_markup=kb.statistics)
    elif text.isdigit():
        for i in generate_alldays:
            if i == text:        
                value_input = func.user_input(value = text)
                value = func.value_plan(value_input = value_input)
                msg = bot.send_message(message.from_user.id, value, reply_markup=kb.input_day)
                bot.register_next_step_handler(msg, reading_input)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, введите значение!', reply_markup=kb.statistics)

# Функция отметка о прочтении введенного вручную дня (с отображением плана)
def reading_input(message):
    text = message.text
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    user_id = message.from_user.id
    tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
    today = tconv(message.date)
    today = func.addiction_stat(day = today)
    today = re.sub("[)|(|,)]", "", str(today))
    read_data = func.whats_read(user_id = user_id)
    stat_read = func.stat_reading(today = today, text = read_data)
    res_msg_reading = func.result_msg_read(stat_read = stat_read, user_id = user_id)
    res_msg_reading_len = str(len(stat_read))
    if text == "✅ Прочитано!":
            print('Отметка о прочтении (вручн) ', user_name, user_first_name)
            logging.info(f"Отметка о прочтении (вручн) {user_name}, {user_first_name}.")
            func.addiction(day = value_input)
            func.reading(user_id = user_id)
            bot.send_message(message.from_user.id, 'Отлично! 🎉', reply_markup=kb.check_day)
    elif text == '🔙 Назад':
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.menu)
    elif text == '✍️ Ввести другой день':
        print('Ввести другой день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите порядковый номер дня в формате "1", например сегодня день № *{today}*.', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day)
    elif text == '✅ Всё прочитано':
        print('Всё прочитано ', user_name, user_first_name)
        logging.info(f"Всё прочитано {user_name}, {user_first_name}.")
        if int(res_msg_reading_len) > 1:
            msg = bot.send_message(message.from_user.id, f'❗️ *Внимание!*\nПосле выполнения этого действия все пропущенные дни будут отмечены как прочитанные.\nВы уверены что хотите это сделать?', parse_mode= "Markdown", reply_markup=kb.yes_no)
            bot.register_next_step_handler(msg, check_all)
        else:
            bot.send_message(message.chat.id, "Нет непрочитанных дней!", parse_mode= "Markdown", reply_markup=kb.menu)
    elif text == '✍️ Отметить день':
        print('Отметить день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_sev_days)
    elif text == '✍️ Ввести другой день':
        print('Ввести другой день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_sev_days)
    elif message.text == '❌ Удалить отметку о прочтении':
        print('Удалить отметку о прочтении ', user_name, user_first_name)
        logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
        bot.register_next_step_handler(msg, delete_check)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!', reply_markup=kb.menu)
        logging.info(f"Введено некорректное значение при отметке прочитанного (вручн) {user_name}, {user_first_name}.")

# Функция по отметке прочитанного (авто)
def reading(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if text == "✅ Прочитано!":
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today_date = tconv(message.date)
        print('Отметка о прочтении (авто) ', user_name, user_first_name)
        logging.info(f"Отметка о прочтении (авто) {user_name}, {user_first_name}.")
        func.addiction_stat(day = today_date)
        func.reading(user_id = user_id)
        bot.send_message(message.from_user.id, 'Отлично! 🎉', reply_markup=kb.menu)
    elif text == '🔙 Назад':
        bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.menu)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!')
        logging.info(f"Введено некорректное значение при отметке прочитанного (авто) {user_name}, {user_first_name}.")


def check(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    logging.info(f"Отметить дни как прочитанные {user_name}, {user_first_name}.")
    read_data = func.whats_read(user_id = user_id)
    tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
    today = tconv(message.date)
    today = func.addiction_stat(day = today)
    today = re.sub("[)|(|,)]", "", str(today))
    stat_read = func.stat_reading(today = today, text = read_data)
    res_msg_reading = func.result_msg_read(stat_read = stat_read, user_id = user_id)
    res_msg_reading_len = str(len(stat_read))
    # print(f'Количество пропущенных дней {res_msg_reading_len}, сегодня день номер {today}')
    if text == '✅ Всё прочитано':
        print('Всё прочитано ', user_name, user_first_name)
        if int(res_msg_reading_len) > 1:
            msg = bot.send_message(message.from_user.id, f'❗️ *Внимание!*\nПосле выполнения этого действия все пропущенные дни будут отмечены как прочитанные.\nВы уверены что хотите это сделать?', parse_mode= "Markdown", reply_markup=kb.yes_no)
            bot.register_next_step_handler(msg, check_all)
        else:
            bot.send_message(message.chat.id, "Нет непрочитанных дней!", parse_mode= "Markdown", reply_markup=kb.menu)
    elif text == '✍️ Отметить день':
        print('Отметить день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_sev_days)
    elif text == '✍️ Ввести другой день':
        print('Ввести другой день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_sev_days)
    else:
        bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.statistics)


# Функция по отметке всех пропущенных дней
def check_all(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if text == '❌ Нет!':
        bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.statistics)
    elif text == '✅ Да!':
        print('Отметка о прочтении (все дни) ', user_name, user_first_name)
        logging.info(f"Отметка о прочтении (все дни) {user_name}, {user_first_name}.")
        read_data = func.whats_read(user_id = user_id)
        # print('MAIN получен список прочитанного ', read_data)
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction_stat(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        stat_read = func.stat_reading(today = today, text = read_data)
        func.check_all(user_id = user_id, stat_read = stat_read)
        bot.send_message(message.chat.id, "Пропущенные дни отмечены как прочитанные!", reply_markup=kb.menu)
    else:
        bot.send_message(message.from_user.id, "Пожалуйста, используйте кнопки!", reply_markup=kb.menu)


# Функция по отметке прочитанных дней (без отображения плана)
def input_sev_days(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    generate_alldays = sorted(map(str, range(1, 365+1)))
    if text == '🔙 Назад':
            bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.check)
    elif text.isdigit()==False:
        logging.info(f"Введено некорректное значение при ручном вводе дня {user_name}, {user_first_name}.")
        bot.send_message(message.from_user.id, 'Пожалуйста, введите корректное значение!', reply_markup=kb.check)
    elif text.isdigit():
            for i in generate_alldays:
                if i == text:
                    value_input = func.user_input(value = text)
                    func.addiction(day = value_input)
                    func.reading(user_id = user_id)
                    # func.check_all(user_id = user_id, stat_read = text)
            msg = bot.send_message(message.from_user.id, f'День №{text} отмечен как прочитанный!', reply_markup=kb.check_day)
            bot.register_next_step_handler(msg, check)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, введите значение!', reply_markup=kb.check)


# Функция по удалению отметки о прочтении
def delete_check(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if text == '🔙 Назад':
        bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.statistics)
    else:
        logging.info(f"Успешное удаление отметки о прочтении дня {text}, для {user_name}, {user_first_name}.")
        func.delete_check(user_id = user_id, delete_day = text)
        bot.send_message(message.from_user.id, f"Отметка о прочтении {text}-го дня удалена", reply_markup=kb.delete_more)


# Функция по отправке сообщения ОС
def quesch(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if message.text == '🔙 Назад':
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
    elif call.data == 'subd':
        bot.send_document(chat_id=chat_id, document=open('db.db', 'rb'))

def message1(message):
    text = message.text
    if message.text == '🔙 Назад':
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
    if message.text == '🔙 Назад':
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
# print('Нажми выход еще раз')
# bot.polling()