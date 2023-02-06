import telebot
from telebot import types
import time
from datetime import datetime
from config import TOKEN, admin
import sqlite3
import keyboard as kb
import config as config
import functions as func
import random_elem as stic_list
import random
from config import db, TOKEN, HOST, PORT, URL, channel_adm
import codecs
import re
from collections import Counter
import numpy as np
import logging
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from flask_apscheduler import APScheduler
from tzlocal import get_localzone
import flask


bot = telebot.TeleBot(TOKEN)
bot_username = bot.get_me().username

markdown = """
    *bold text*
    _italic text_
    [text](URL)
    """

logging.basicConfig(level=logging.INFO, filename="log.log",
                    format="%(asctime)s %(levelname)s %(message)s", filemode="a", encoding = "UTF-8")



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
    cnt = 0
    for i in range(len(users)):
        rem_select = func.reminder_select(user_id = users[i][0])
        try:
            # print("MAIN получены id сообщений для удаления", rem_select)
            for m in range(len(rem_select)):
                try:
                    time.sleep(1)
                    func.reminder_delete(user_id = users[i][0], message_id = rem_select[m][0])
                    bot.edit_message_reply_markup(users[i][0], message_id = rem_select[m][0], reply_markup = '')
                    logging.info(f"Кнопка удалена у {users[i][0]}")
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
            cnt += 1
            logging.info(f"Сообщение отправлено {users[i][0]}")
        except:
            pass
    print(f'Ежедневные напоминания отправлены, активных пользователей {cnt}')

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
        bot.edit_message_text(chat_id=check.message.chat.id, message_id=check.message.message_id, text=f"☀️ Доброе утро!\n📆 Сегодня {today_date}, *день №{today}*\n\n📖 Читаем *{info_msg}*\n\n✅ Прочитано!", parse_mode= "Markdown", reply_markup=None)
    except:
        pass

# Пуш на удаление инлайн кнопки в 00.00
def push_del_inline():
    print('Удаление кнопок запущено')
    tconv = time.strftime("%d.%m.%Y")
    today_date = tconv
    inline_today = func.addiction_stat(day = today_date)
    info_msg = func.msg_plan(day_input=today_date)
    users = func.admin_message()
    cnt = 0
    for i in range(len(users)):
        rem_select = func.reminder_select(user_id = users[i][0])
        # print("MAIN получены id сообщений для удаления", rem_select)
        try:
            for m in range(len(rem_select)):
                try:
                    func.reminder_delete(user_id = users[i][0], message_id = rem_select[m][0])
                    bot.edit_message_reply_markup(users[i][0], message_id = rem_select[m][0], reply_markup = '')
                    logging.info(f"Кнопка удалена у {users[i][0]}")
                    cnt += 1
                except:
                    pass
        except:
                pass
    print(f'Удаление кнопок завершено, удалено {cnt} кнопок')

# Параметры расписания удаления кнопок
scheduler = BackgroundScheduler(timezone=tz)
scheduler.add_job(push_del_inline, 'cron', hour='23', minute='59')
scheduler.start()


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




@bot.message_handler(func=lambda message: message.text == '🎁 Что читаем сегодня?')
def whats_read_btn(message):
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
    else:
        logging.info(f"Ошибка, некорректное значение при вводе в гл.меню {user_name}, {user_first_name}.")
        bot.send_message(message.chat.id, "Пожалуйста, воспользуйтесь кнопками!", reply_markup=kb.menu)


@bot.message_handler(func=lambda message: message.text == '📆 Что читаем на этой неделе?')
def whats_read_week_btn(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    print('Что читаем на неделе', user_name)
    tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
    today_date = tconv(message.date)
    today = func.addiction_stat(day = today_date)
    # today = '144'
    week = func.whats_read_week_btn(today = today)
    bot.send_message(message.chat.id, f"🔎 На этой неделе читаем:\n\n{week}", parse_mode= "Markdown", reply_markup=kb.menu)


@bot.message_handler(func=lambda message: message.text == '📊 Отчет')
def statistics_btn(message):
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
    if message.text == '📊 Отчет':
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
            for i in stic_list.den:
                if i == count_res:
                    day_out = 'день'
            for i in stic_list.dnya:
                if i == count_res:
                    day_out = 'дня'
            for i in stic_list.dney:
                if i == count_res:
                    day_out = 'дней'
            msg = bot.send_message(message.from_user.id, f'📈 Вы опережаете план на *{count_res}* {day_out}!', parse_mode= "Markdown", reply_markup=kb.input_read_advance)
            bot.register_next_step_handler(msg, advance_out)
        elif stat_read_len == '0':
            today_verify = func.today_verify(user_id, today)
            if today_verify is None:
                tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
                today_date = tconv(message.date)
                today = func.addiction_stat(day = today_date)
                info = func.msg_plan(day_input=today_date)
                msg = bot.send_message(message.from_user.id, f'*🎇 Все по плану!*\n\n⚡️ Не забудьте почитать сегодня:  *{info}*', parse_mode= "Markdown", reply_markup=kb.today_verify)
                bot.register_next_step_handler(msg, reading_input_verify)
            else:
                msg = bot.send_message(message.from_user.id, '*🎇 Все по плану!*', parse_mode= "Markdown", reply_markup=kb.input_read_all_list)
                bot.register_next_step_handler(msg, input_read_all_list)
        else:
            count_stat = stat_read
            count_day = str(len(stat_read)-1)
            # for i in count_stat:
            #     if i != 0:
            #         count_day += 1
            # print('MAIN количество пропущенных дней ', count_day)
            if int(count_day) < 8:
                print(count_day)
                logging.info(f"MAIN сформирован список пропущенных дней: {stat_read_full}, для {user_name}, {user_first_name}.")
                for i in stic_list.den:
                    if i == count_day:
                        day_out = 'день'
                for i in stic_list.dnya:
                    if i == count_day:
                        day_out = 'дня'
                for i in stic_list.dney:
                    if i == count_day:
                        day_out = 'дней'
                bot.send_message(message.from_user.id, f'📉 *Вы пропустили дни №:*\n\n{stat_read_full}\n\n⏳ Вы отстаете на *{count_day}* {day_out}.', parse_mode= "Markdown")
                msg = bot.send_message(message.from_user.id, 'Чтобы отметить пропущенные дни, нажмите кнопку внизу и введите нужный номер дня из списка выше.', reply_markup=kb.check_lag)
                bot.register_next_step_handler(msg, reading_input_lag)
            else:
                stat_read_msg = ', '.join([f'{stat_read_msg}' for stat_read_msg in stat_read])
                logging.info(f"MAIN сформирован список пропущенных дней: {stat_read_msg}, для {user_name}, {user_first_name}.")
                stat_read_msg = stat_read_msg[:0][:1] + stat_read_msg[(2):]
                for i in stic_list.den:
                    if i == count_day:
                        day_out = 'день'
                for i in stic_list.dnya:
                    if i == count_day:
                        day_out = 'дня'
                for i in stic_list.dney:
                    if i == count_day:
                        day_out = 'дней'
                bot.send_message(message.from_user.id, f'📉 *Вы пропустили дни №:*\n\n{stat_read_msg}\n\n⏳ Вы отстаете на *{count_day}* {day_out}.', parse_mode= "Markdown")
                msg = bot.send_message(message.from_user.id, 'Чтобы посмотреть что нужно прочитать в эти пропущенные дни, нажмите кнопку внизу и введите нужный номер дня из списка выше.', reply_markup=kb.statistics)
                bot.register_next_step_handler(msg, lag_more_8)
    else:
        logging.info(f"Ошибка, некорректное значение при вводе в гл.меню {user_name}, {user_first_name}.")
        bot.send_message(message.chat.id, "Пожалуйста, воспользуйтесь кнопками!", reply_markup=kb.menu)

@bot.message_handler(func=lambda message: message.text == '🆘 Помощь')
def statistics_btn(message):
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
    if message.text == '🆘 Помощь':
        print('Помощь ', user_name, user_first_name)
        logging.info(f"Помощь {user_name}, {user_first_name}.")
        bot.send_message(message.chat.id, f'Ответы на самые частые вопросы вы сможете найти по [ссылке](https://telegra.ph/Plan-chteniya-Biblii-NBC-bot-01-10)', parse_mode= "Markdown")
        msg = bot.send_message(message.chat.id, f'Если вашего вопроса нет в списке, или у вас есть предложение по улучшению бота, напишите сообщение, нажав кнопку внизу 👇', parse_mode= "Markdown", reply_markup=kb.quesch)
        bot.register_next_step_handler(msg, quesch_msg)
    else:
        logging.info(f"Ошибка, некорректное значение при вводе в гл.меню {user_name}, {user_first_name}.")
        bot.send_message(message.chat.id, "Пожалуйста, воспользуйтесь кнопками!", reply_markup=kb.menu)

@bot.message_handler(func=lambda message: message.text == '🔙 Назад')
def back(message):
    # Цикл удаления инлайн-кнопки у автосообщения и id из бд
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    generate_alldays = sorted(map(str, range(1, 365+1)))
    text = message.text
    rem_select = func.reminder_select(user_id = user_id)
    try:
        bot.edit_message_reply_markup(message.chat.id, message_id = rem_select, reply_markup = '')
        func.reminder_delete(user_id = user_id, message_id = rem_select[0][0])
    except:
        pass
    if text == '🔙 Назад':
        bot.send_message(message.from_user.id, "Вы в главном меню", reply_markup=kb.menu)
    else:
        logging.info(f"Ошибка, некорректное значение при вводе в гл.меню {user_name}, {user_first_name}.")
        bot.send_message(message.chat.id, "Пожалуйста, воспользуйтесь кнопками!", reply_markup=kb.menu)


@bot.message_handler(content_types=['text'])
def any_text(message):
    bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!', reply_markup=kb.menu)




# Функции опережения
# --------------------------------------------------------------------------
def advance_out(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    text = message.text
    if message.text == '✍️ Ввести номер дня':
        print('Вводит день вручную ', user_name, user_first_name)
        logging.info(f"Вводит день вручную {user_name}, {user_first_name}.")
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction_stat(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        msg = bot.send_message(message.from_user.id, f'Введите порядковый номер дня в формате "1", например сегодня день № *{today}*.', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day_advance)
    elif message.text == '🗞 Показать все прочитанные дни':
        print('Список прочитанного ', user_name, user_first_name)
        read_data = func.whats_read(user_id = user_id)
        # print('MAIN вывожу список прочитанного ', read_data)
        logging.info(f"Показать все прочитанные дни: {read_data}, для {user_name}, {user_first_name}.")
        text = ' '.join([f'{read_data}' for read_data in read_data])
        text = re.sub("[)|(|')]", "", text)
        text = text.replace(",,", ",")
        msg = bot.send_message(message.from_user.id, f'*Список прочитанных дней:*\n\n {text}', parse_mode= "Markdown", reply_markup=kb.input_read_all_list)
        bot.register_next_step_handler(msg, all_day_advance)
    elif message.text == '✍️ Ввести другой день':
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction_stat(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        msg = bot.send_message(message.from_user.id, f'Введите порядковый номер дня в формате "1", например сегодня день № *{today}*.', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day_advance)
    elif text == "✅ Прочитано!":
        print('Отметка о прочтении (вручн) ', user_name, user_first_name)
        logging.info(f"Отметка о прочтении (вручн) {user_name}, {user_first_name}.")
        func.addiction(day = value_input)
        func.reading(user_id = user_id)
        stic = random.choice(stic_list.read_stick)
        msg = bot.send_message(message.from_user.id, f'Отлично! {stic}', reply_markup=kb.check_day)
        bot.register_next_step_handler(msg, advance_out)
    elif text == '🔙 Назад':
        bot.send_message(message.from_user.id, "Вы в главном меню", reply_markup=kb.menu)
    else:
        msg = bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!', reply_markup=kb.input_read_advance)
        bot.register_next_step_handler(msg, advance_out)

# Функция получение информации о введенном вручную дне
def input_day_advance(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    generate_alldays = sorted(map(str, range(1, 365+1)))
    text = message.text
    global value_input
    if message.text == '🔙 Назад':
        msg = bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.input_read_advance)
        bot.register_next_step_handler(msg, advance_out)
    elif text.isdigit()==False:
        logging.info(f"Введено некорректное значение при ручном вводе дня {user_name}, {user_first_name}.")
        bot.send_message(message.from_user.id, 'Пожалуйста, введите корректное значение!', reply_markup=kb.input_read_advance)
    elif text.isdigit():
        for i in generate_alldays:
            if i == text:        
                value_input = func.user_input(value = text)
                value = func.value_plan(value_input = value_input)
                msg = bot.send_message(message.from_user.id, value, reply_markup=kb.input_day)
                bot.register_next_step_handler(msg, advance_out)
    else:
        msg = bot.send_message(message.from_user.id, 'Пожалуйста, введите значение!', reply_markup=kb.input_read_advance)
        bot.register_next_step_handler(msg, advance_out)

# Функция при нажатии на Показать все дни
def all_day_advance(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    text = message.text
    if message.text == '✍️ Ввести номер дня':
        print('Вводит день вручную ', user_name, user_first_name)
        logging.info(f"Вводит день вручную {user_name}, {user_first_name}.")
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction_stat(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        msg = bot.send_message(message.from_user.id, f'Введите порядковый номер дня в формате "1", например сегодня день № *{today}*.', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day_advance)
    elif message.text == '❌ Удалить отметку о прочтении':
        print('Удалить отметку о прочтении ', user_name, user_first_name)
        logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
        bot.register_next_step_handler(msg, delete_check_advance)
    elif message.text == '❌ Удалить другой день':
        print('Удалить другой день ', user_name, user_first_name)
        logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
        bot.register_next_step_handler(msg, delete_check_advance)
    elif text == '🔙 Назад':
        msg = bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.input_read_advance)
        bot.register_next_step_handler(msg, advance_out)
    else:
        msg = bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!', reply_markup=kb.input_read_advance)
        bot.register_next_step_handler(msg, advance_out)

def delete_check_advance(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if text == '🔙 Назад':
        msg = bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.input_read_all_list)
        bot.register_next_step_handler(msg, all_day_advance)
    else:
        logging.info(f"Успешное удаление отметки о прочтении дня {text}, для {user_name}, {user_first_name}.")
        func.delete_check(user_id = user_id, delete_day = text)
        msg = bot.send_message(message.from_user.id, f"Отметка о прочтении {text}-го дня удалена", reply_markup=kb.delete_more)
        bot.register_next_step_handler(msg, all_day_advance)
# ------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------



# Функция-вывод при отсутствии отставания и не прочитанном сегодняшнем дне
# ------------------------------------------------------------------------------------------
def reading_input_verify(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if message.text == "✅ Прочитано":
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today_date = tconv(message.date)
        print('Отметка о прочтении (авто) ', user_name, user_first_name)
        logging.info(f"Отметка о прочтении (авто) {user_name}, {user_first_name}.")
        func.addiction_stat(day = today_date)
        func.reading(user_id = user_id)
        stic = random.choice(stic_list.read_stick)
        bot.send_message(message.from_user.id, f'Отлично! {stic}', reply_markup=kb.menu)
    elif message.text == '❌ Удалить отметку о прочтении':
        print('Удалить отметку о прочтении ', user_name, user_first_name)
        logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
        bot.register_next_step_handler(msg, delete_check_verify)
    elif message.text == '❌ Удалить другой день':
        print('Удалить другой день ', user_name, user_first_name)
        logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
        bot.register_next_step_handler(msg, delete_check_verify)
    elif text == '🔙 Назад':
        msg = bot.send_message(message.from_user.id, "Вы в главном меню", reply_markup=kb.menu)
    else:
        logging.info(f"Введено некорректное значение при отметке прочитанного (авто) {user_name}, {user_first_name}.")
        msg = bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!')
        bot.register_next_step_handler(msg, reading_input_verify)


def delete_check_verify(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if text == '🔙 Назад':
        msg = bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.today_verify)
        bot.register_next_step_handler(msg, reading_input_verify)
    else:
        logging.info(f"Успешное удаление отметки о прочтении дня {text}, для {user_name}, {user_first_name}.")
        func.delete_check(user_id = user_id, delete_day = text)
        msg = bot.send_message(message.from_user.id, f"Отметка о прочтении {text}-го дня удалена", reply_markup=kb.delete_more)
        bot.register_next_step_handler(msg, reading_input_verify)
# ------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------



# Функция-вывод при отсутствии отставания и опережения
# ------------------------------------------------------------------------------------------
def input_read_all_list(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    text = message.text
    if message.text == '✍️ Ввести номер дня':
        print('Вводит день вручную ', user_name, user_first_name)
        logging.info(f"Вводит день вручную {user_name}, {user_first_name}.")
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction_stat(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        msg = bot.send_message(message.from_user.id, f'Введите порядковый номер дня в формате "1", например сегодня день № *{today}*.', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day_all_list)
    elif text == '✍️ Ввести другой день':
        print('Ввести другой день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day_all_list)
    elif text == "✅ Прочитано!":
            print('Отметка о прочтении (вручн) ', user_name, user_first_name)
            logging.info(f"Отметка о прочтении (вручн) {user_name}, {user_first_name}.")
            func.addiction(day = value_input)
            func.reading(user_id = user_id)
            stic = random.choice(stic_list.read_stick)
            msg = bot.send_message(message.from_user.id, f'Отлично! {stic}', reply_markup=kb.check_day)
            bot.register_next_step_handler(msg, input_read_all_list)
    elif message.text == '❌ Удалить отметку о прочтении':
        print('Удалить отметку о прочтении ', user_name, user_first_name)
        logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
        bot.register_next_step_handler(msg, delete_check_all_list)
    elif message.text == '❌ Удалить другой день':
        print('Удалить другой день ', user_name, user_first_name)
        logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
        bot.register_next_step_handler(msg, delete_check_all_list)
    elif text == '🔙 Назад':
        msg = bot.send_message(message.from_user.id, "Вы в главном меню", reply_markup=kb.menu)
    else:
        msg = bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!', reply_markup=kb.input_read_all_list)
        bot.register_next_step_handler(msg, input_read_all_list)

# Функция получение информации о введенном вручную дне
def input_day_all_list(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    generate_alldays = sorted(map(str, range(1, 365+1)))
    text = message.text
    global value_input
    if message.text == '🔙 Назад':
            msg = bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.input_read_all_list)
            bot.register_next_step_handler(msg, input_read_all_list)
    elif text.isdigit()==False:
        logging.info(f"Введено некорректное значение при ручном вводе дня {user_name}, {user_first_name}.")
        msg = bot.send_message(message.from_user.id, 'Пожалуйста, введите корректное значение!', reply_markup=kb.input_read_all_list)
        bot.register_next_step_handler(msg, input_read_all_list)
    elif text.isdigit():
        for i in generate_alldays:
            if i == text:        
                value_input = func.user_input(value = text)
                value = func.value_plan(value_input = value_input)
                msg = bot.send_message(message.from_user.id, value, reply_markup=kb.input_day)
                bot.register_next_step_handler(msg, input_read_all_list)
    else:
        msg = bot.send_message(message.from_user.id, 'Пожалуйста, введите значение!', reply_markup=kb.input_read_all_list)
        bot.register_next_step_handler(msg, input_read_all_list)

def delete_check_all_list(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if text == '🔙 Назад':
        msg = bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.input_read_all_list)
        bot.register_next_step_handler(msg, input_read_all_list)
    else:
        logging.info(f"Успешное удаление отметки о прочтении дня {text}, для {user_name}, {user_first_name}.")
        func.delete_check(user_id = user_id, delete_day = text)
        msg = bot.send_message(message.from_user.id, f"Отметка о прочтении {text}-го дня удалена", reply_markup=kb.delete_more)
        bot.register_next_step_handler(msg, input_read_all_list)
# ------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------



# Функция-вывод отставания менее 8 дней
# ------------------------------------------------------------------------------------------
def reading_input_lag(message):
    text = message.text
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    user_id = message.from_user.id
    # print('Ветка "Отставание менее 8" Основная ветка ', user_name, user_first_name)
    tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
    today = tconv(message.date)
    today = func.addiction_stat(day = today)
    today = re.sub("[)|(|,)]", "", str(today))
    read_data = func.whats_read(user_id = user_id)
    stat_read = func.stat_reading(today = today, text = read_data)
    res_msg_reading = func.result_msg_read(stat_read = stat_read, user_id = user_id)
    res_msg_reading_len = str(len(stat_read))
    if text == '✅ Всё прочитано':
        logging.info(f"Всё прочитано {user_name}, {user_first_name}.")
        if int(res_msg_reading_len) > 1:
            # print('Ветка "Отставание менее 8" Всё прочитано ', user_name, user_first_name)
            msg_check = bot.send_message(message.from_user.id, f'❗️ *Внимание!*\nПосле выполнения этого действия все пропущенные дни будут отмечены как прочитанные.\nВы уверены что хотите это сделать?', parse_mode= "Markdown", reply_markup=kb.yes_no)
            bot.register_next_step_handler(msg_check, check_all_lag)
        else:
            bot.send_message(message.chat.id, "Нет непрочитанных дней!", parse_mode= "Markdown", reply_markup=kb.menu)
    elif text == '✍️ Отметить день':
        print('Отметить день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_sev_days_lag)
    elif message.text == '❌ Удалить отметку о прочтении':
        print('Удалить отметку о прочтении ', user_name, user_first_name)
        logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
        bot.register_next_step_handler(msg, delete_check_lag)
    elif message.text == '❌ Удалить другой день':
        print('Удалить другой день ', user_name, user_first_name)
        logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
        bot.register_next_step_handler(msg, delete_check_lag)
    elif text == '🔙 Назад':
        bot.send_message(message.from_user.id, "Вы в главном меню", reply_markup=kb.menu)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!', reply_markup=kb.menu)
        logging.info(f"Введено некорректное значение при отметке прочитанного (вручн) {user_name}, {user_first_name}.")


def input_sev_days_lag(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    # print('Ветка "Отставание менее 8" input_sev_days_lag ', user_name, user_first_name)
    generate_alldays = sorted(map(str, range(1, 365+1)))
    if text == '🔙 Назад':
            msg = bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.check_lag)
            bot.register_next_step_handler(msg, reading_input_lag)
    elif text.isdigit()==False:
        logging.info(f"Введено некорректное значение при ручном вводе дня {user_name}, {user_first_name}.")
        bot.send_message(message.from_user.id, 'Пожалуйста, введите корректное значение!', reply_markup=kb.check_lag)
    elif text.isdigit():
            for i in generate_alldays:
                if i == text:
                    value_input = func.user_input(value = text)
                    func.addiction(day = value_input)
                    func.reading(user_id = user_id)
                    # func.check_all(user_id = user_id, stat_read = text)
            msg = bot.send_message(message.from_user.id, f'День №{text} отмечен как прочитанный!', reply_markup=kb.check_day)
            bot.register_next_step_handler(msg, check_lag)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, введите значение!', reply_markup=kb.check_lag)


def check_lag(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    # print('Ветка "Отставание менее 8" check_lag ', user_name, user_first_name)
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
            bot.register_next_step_handler(msg, check_all_lag)
        else:
            bot.send_message(message.chat.id, "Нет непрочитанных дней!", parse_mode= "Markdown", reply_markup=kb.menu)
    elif text == '✍️ Отметить день':
        print('Отметить день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_sev_days_lag)
    elif text == '✍️ Ввести другой день':
        print('Ввести другой день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_sev_days_lag)
    elif message.text == '🔙 Назад':
            msg = bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.check_lag)
            bot.register_next_step_handler(msg, reading_input_lag)
    else:
        bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.check_lag)


def delete_check_lag(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    # print('Ветка "Отставание менее 8" delete_check_lag ', user_name, user_first_name)
    if text == '🔙 Назад':
        msg = bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.check_lag)
        bot.register_next_step_handler(msg, reading_input_lag)
    else:
        logging.info(f"Успешное удаление отметки о прочтении дня {text}, для {user_name}, {user_first_name}.")
        func.delete_check(user_id = user_id, delete_day = text)
        msg = bot.send_message(message.from_user.id, f"Отметка о прочтении {text}-го дня удалена", reply_markup=kb.delete_more)
        bot.register_next_step_handler(msg, reading_input_lag)


# Функция по отметке всех пропущенных дней
def check_all_lag(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    # print('Ветка "Отставание менее 8" Check_all ', user_name, user_first_name)
    if text == '❌ Нет!':
        msg = bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.check_lag)
        bot.register_next_step_handler(msg, reading_input_lag)
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
        bot.send_message(message.from_user.id, "Пожалуйста, используйте кнопки!", reply_markup=kb.check_lag)
# ------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------



# Функция-вывод при отстовании более чем на 8 дней
# ------------------------------------------------------------------------------------------
def lag_more_8(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    text = message.text
    if message.text == '✍️ Ввести номер дня':
        print('Вводит день вручную ', user_name, user_first_name)
        logging.info(f"Вводит день вручную {user_name}, {user_first_name}.")
        tconv = lambda x: time.strftime("%d.%m.%Y", time.localtime(x))
        today = tconv(message.date)
        today = func.addiction_stat(day = today)
        today = re.sub("[)|(|,)]", "", str(today))
        msg = bot.send_message(message.from_user.id, f'Введите порядковый номер дня в формате "1", например сегодня день № *{today}*.', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day_more_8)
    elif message.text == '🗓 Отметить дни как прочитанные':
        msg = bot.send_message(message.from_user.id, f'Выберите действие', reply_markup=kb.check)
        bot.register_next_step_handler(msg, check_more_8)
    elif message.text == '❌ Удалить отметку о прочтении':
        print('Удалить отметку о прочтении ', user_name, user_first_name)
        logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
        bot.register_next_step_handler(msg, delete_check_more_8)
    elif message.text == '❌ Удалить другой день':
        print('Удалить другой день ', user_name, user_first_name)
        logging.info(f"Удалить отметку о прочтении {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Введите день с которого нужно удалить отметку о прочтении", reply_markup=kb.back)
        bot.register_next_step_handler(msg, delete_check_more_8)
    elif text == '🔙 Назад':
        bot.send_message(message.from_user.id, "Вы в главном меню", reply_markup=kb.menu)


# Функция получение информации о введенном вручную дне
def input_day_more_8(message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username
    generate_alldays = sorted(map(str, range(1, 365+1)))
    text = message.text
    global value_input
    if message.text == '🔙 Назад': 
        msg = bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.statistics)
        bot.register_next_step_handler(msg, lag_more_8)
    elif text.isdigit()==False:
        logging.info(f"Введено некорректное значение при ручном вводе дня {user_name}, {user_first_name}.")
        bot.send_message(message.from_user.id, 'Пожалуйста, введите корректное значение!', reply_markup=kb.statistics)
    elif text.isdigit():
        for i in generate_alldays:
            if i == text:        
                value_input = func.user_input(value = text)
                value = func.value_plan(value_input = value_input)
                msg = bot.send_message(message.from_user.id, value, reply_markup=kb.input_day)
                bot.register_next_step_handler(msg, check_more_8)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, введите значение!', reply_markup=kb.statistics)


def check_more_8(message):
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
            bot.register_next_step_handler(msg, check_all_more_8)
        else:
            bot.send_message(message.chat.id, "Нет непрочитанных дней!", parse_mode= "Markdown", reply_markup=kb.menu)
    elif text == "✅ Прочитано!":
            print('Отметка о прочтении (вручн) ', user_name, user_first_name)
            logging.info(f"Отметка о прочтении (вручн) {user_name}, {user_first_name}.")
            func.addiction(day = value_input)
            func.reading(user_id = user_id)
            stic = random.choice(stic_list.read_stick)
            msg = bot.send_message(message.from_user.id, f'Отлично! {stic}', reply_markup=kb.check_day)
            bot.register_next_step_handler(msg, check_more_8)
    elif text == '✍️ Отметить день':
        print('Отметить день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_sev_days_more_8)
    elif text == '✍️ Отметить другой день':
        print('Отметить день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_sev_days_more_8)
    elif text == '✍️ Ввести другой день':
        print('Ввести другой день ', user_name, user_first_name)
        msg = bot.send_message(message.from_user.id, f'Введите день, который хотите отметить прочитанным в формате "1"', parse_mode= "Markdown", reply_markup=kb.back)
        bot.register_next_step_handler(msg, input_day_more_8)
    elif message.text == '🔙 Назад':
        msg = bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.statistics)
        bot.register_next_step_handler(msg, lag_more_8)
    else:
        msg = bot.send_message(message.chat.id, "Пожалуйста, воспользуйтесь кнопками!", reply_markup=kb.statistics)
        bot.register_next_step_handler(msg, lag_more_8)


def input_sev_days_more_8(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    generate_alldays = sorted(map(str, range(1, 365+1)))
    if text == '🔙 Назад':
        msg = bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=kb.check)
        bot.register_next_step_handler(msg, check_more_8)
    elif text.isdigit()==False:
        logging.info(f"Введено некорректное значение при ручном вводе дня {user_name}, {user_first_name}.")
        bot.send_message(message.from_user.id, 'Пожалуйста, введите корректное значение!', reply_markup=kb.statistics)
    elif text.isdigit():
            for i in generate_alldays:
                if i == text:
                    value_input = func.user_input(value = text)
                    func.addiction(day = value_input)
                    func.reading(user_id = user_id)
                    # func.check_all(user_id = user_id, stat_read = text)
            msg = bot.send_message(message.from_user.id, f'День №{text} отмечен как прочитанный!', reply_markup=kb.check__sev_day)
            bot.register_next_step_handler(msg, check_more_8)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, введите значение!', reply_markup=kb.statistics)


def delete_check_more_8(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if text == '🔙 Назад':
        msg = bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.statistics)
        bot.register_next_step_handler(msg, lag_more_8)
    else:
        logging.info(f"Успешное удаление отметки о прочтении дня {text}, для {user_name}, {user_first_name}.")
        func.delete_check(user_id = user_id, delete_day = text)
        msg = bot.send_message(message.from_user.id, f"Отметка о прочтении {text}-го дня удалена", reply_markup=kb.delete_more)
        bot.register_next_step_handler(msg, lag_more_8)


# Функция по отметке всех пропущенных дней
def check_all_more_8(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if text == '❌ Нет!':
        msg = bot.send_message(message.from_user.id, "Выберите кнопку", reply_markup=kb.check)
        bot.register_next_step_handler(msg, check_more_8)
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
        msg = bot.send_message(message.from_user.id, "Пожалуйста, используйте кнопки!", reply_markup=kb.menu)
        bot.register_next_step_handler(msg, lag_more_8)
# ------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------










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
        stic = random.choice(stic_list.read_stick)
        bot.send_message(message.from_user.id, f'Отлично! {stic}', reply_markup=kb.menu)
    elif text == '🔙 Назад':
        bot.send_message(message.from_user.id, "Вы в главном меню", reply_markup=kb.menu)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!')
        logging.info(f"Введено некорректное значение при отметке прочитанного (авто) {user_name}, {user_first_name}.")

def quesch_msg(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if message.text == '🔙 Назад':
        bot.send_message(message.chat.id, "Вы в главном меню", reply_markup=kb.menu)
    elif text == '✉️ Отправить сообщение':
        logging.info(f"Отправить сообщение {user_name}, {user_first_name}.")
        msg = bot.send_message(message.chat.id, "Пожалуйста, введите ваше сообщение", reply_markup=kb.back)
        bot.register_next_step_handler(msg, quesch)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, используйте кнопки!', reply_markup=kb.menu)


# Функция по отправке сообщения ОС
def quesch(message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name
    text = message.text
    if message.text == '🔙 Назад':
            bot.send_message(message.chat.id, "Вы в главном меню", reply_markup=kb.menu)
    else:
        logging.info(f"Отправка сообщения от {user_name}, {user_first_name}.")
        info = channel_adm
        bot.send_message(message.chat.id, text=' Ваше сообщение отправляется')
        bot.send_message(info, f'Входящее сообщение!\n\nID: `{user_id}`\nUsername: @{user_name}\nИмя: {user_first_name}\n\nСообщение: {str(text)}', parse_mode= "Markdown")
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
            bot.send_message(message.chat.id, "Вы в главном меню", reply_markup=kb.menu)
    else:
        info = func.admin_message()
        bot.send_message(message.chat.id, text=' Рассылка начата!')
        cnt = 0
        for i in range(len(info)):
            try:
                time.sleep(1)
                bot.send_message(info[i][0], f'{str(text)}')
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
            bot.send_message(message.chat.id, "Вы в главном меню", reply_markup=kb.menu)
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




# # Поддержание работы
app = flask.Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url = URL)
    app.run(host = HOST, port = PORT, debug = False)



# bot.polling(none_stop=True)
# bot.infinity_polling()
# # print('Нажми выход еще раз')
# # bot.polling()
