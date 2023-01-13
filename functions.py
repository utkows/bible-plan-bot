from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Google
gscope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
gcredentials = 'parameters.json'
gdocument = 'bd_bot'


import sqlite3
import telebot
import config as config
from config import db, TOKEN
import re
import numpy as np
import logging

def first_join(user_id, username):
    connection = sqlite3.connect(db)
    q = connection.cursor()
    q = q.execute('SELECT * FROM users WHERE user_id IS '+str(user_id))
    row = q.fetchone()
    if row is None:
        q.execute("INSERT INTO users (user_id,  nick) VALUES ('%s', '%s')"%(user_id,username))
        connection.commit()
    connection.close()
def admin_message():
    # print('FUNC получено сообщение ', text)
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    # print('FUNC получение id из БД')
    cursor.execute(f'SELECT user_id FROM users')
    row = cursor.fetchall()
    # print('FUNC отправка id в main')
    return row
    conn.close()
def stats():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    row = cursor.execute(f'SELECT user_id FROM users').fetchone()
    amount_user_all = 0
    while row is not None:
        amount_user_all += 1
        row = cursor.fetchone()
    msg = ' Информация:\n\n Пользователей в боте - ' + str(amount_user_all)
    return msg
    conn.close()


def msg_plan(day_input):
    # print('FUNC дата получена ', day_input)
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(f'SELECT read FROM plan WHERE day = "{day_input}"')
    row = cursor.fetchall()[0][0]
    # print('FUNC данные в таблице получены ', row)
    return row
    conn.close()






def user_input(value):
    # print('FUNC получена инфа о ручном вводе дня', value)
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q = q.execute(f'SELECT numbers FROM plan WHERE numbers = "{value}"')
    value_input = q.fetchone()[0]
    return value_input
    conn.close()


def value_plan(value_input):
    # print('FUNC получена инфа о дне в БД', value_input)
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q = q.execute(f'SELECT read FROM plan WHERE numbers IS {value_input}')
    value_plan = q.fetchone()
    # print('FUNC передаю инфу из плана', value_plan)
    return value_plan
    conn.close()


def addiction_stat(day):
    # day = day.replace("'", "")
    # print('FUNC получена инфа о дне', day)
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q = q.execute(f'SELECT numbers FROM plan WHERE day = "{day}"')
    global value_day
    value_day = q.fetchone()[0]
    # print('FUNC дню присвоено значение ', value_day)
    return value_day
    conn.close()


def addiction(day):
    # day = day.replace("'", "")
    # print('FUNC получена инфа о дне', day)
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q = q.execute(f'SELECT numbers FROM plan WHERE numbers = "{day}"')
    global value_day
    value_day = q.fetchone()[0]
    # print('FUNC дню присвоено значение ', value_day)
    return value_day
    conn.close()
    

def reading(user_id):
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q = q.execute(f'SELECT * FROM reading WHERE day = "{value_day}" AND user_id = {user_id}')
    row = q.fetchone()
    if row is None:
        q.execute("INSERT INTO reading (user_id, day) VALUES ('%s', '%s')"%(user_id, value_day))
        conn.commit()
        # print('FUNC данные о прочтении записаны ', user_id, value_addiction)
        logging.info(f"FUNC данные о прочтении записаны {user_id}, {value_day}.")
    conn.close()


def whats_read(user_id):
    # print('FUNC получен запрос на список прочитанного от ', user_id)
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q = q.execute(f'SELECT day FROM reading WHERE user_id = "{user_id}" ORDER BY day')
    whats_read_data = q.fetchall()
    # print('FUNC инфа о прочитанных днях ', whats_read_data)
    # print('FUNC инфа о прочитанных днях (список инт) ', whats_read_data)
    logging.info(f"FUNC инфа о прочитанных днях (список инт) {user_id}, {whats_read_data}.")
    return whats_read_data
    conn.close()


def stat_reading(today, text):
    # print('FUNC получен список прочитанных дней', text)
    global text_clear
    text_clear = []
    for i in text:
        list_text = list(map(int, i))
        text_clear += list_text
    # print('FUNC список прочитанных дней отформатирован в список ', text_clear)
    # print('FUNC получен номер дня', today)
    generate_days = sorted(map(str, range(0,int(today)+1)))
    # print('FUNC строки сгенерированных дней ', generate_days)
    gen_clear = sorted(list(map(int, generate_days)))
    # print('FUNC строки сгенерированных дней преобразованы в список', gen_clear)
    statistics = set(gen_clear).difference(text_clear)
    # print('FUNC вывожу разницу между списками ', statistics)
    # print('FUNC вывожу пропущенные дни ', statistics)
    return statistics
def result_msg_read(stat_read, user_id):
    text_clear_msg = text_clear
    # print('FUNC вывожу прочитанные дни из переменной ', text_clear_msg)
    return text_clear_msg


def stat_read_full(stat_read):
    # print('FUNC получены непрочитанные дни ', stat_read)
    # stat_read_list = [int(x) for x in stat_read]
    # print('FUNC непрочитанные дни отформатированы в список ', stat_read_list)
    conn = sqlite3.connect(db)
    q = conn.cursor()
    stat_read_full = []
    for i in stat_read:
        if i != 0:
            q = q.execute(f'SELECT read FROM plan WHERE numbers = {i}')
            stat_read_full_bd = q.fetchall()[0][0]
            stat_read_full += [str('\n'.join([f'{i} - {stat_read_full_bd}']))]
            # print('FUNC найдены отрывки по пропущенным дням', stat_read_full)
    stat_read_full_msg = '\n'.join(stat_read_full)
    # print('FUNC конец вывода ', stat_read_full_msg)
    return stat_read_full_msg
    conn.close()


def check_all(user_id, stat_read):
    for i in stat_read:
        if i != 0:
            conn = sqlite3.connect(db)
            q = conn.cursor()
            q.execute("INSERT INTO reading (user_id, day) VALUES ('%s', '%s')"%(user_id, i))
            conn.commit()
    # print(f"FUNC данные о прочтении записаны {user_id}, {stat_read}.")
    logging.info(f"FUNC данные о прочтении записаны {user_id}, {stat_read}.")
    conn.close()

def delete_check(user_id, delete_day):
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q.execute(f"DELETE FROM reading WHERE day = '{delete_day}' AND user_id = {user_id}")
    conn.commit()
    # logging.info(f"FUNC данные о прочтении записаны {user_id}, {stat_read}.")
    conn.close()




    # Запись в Google Sheet Bot
# def add_to_gsheet(read_data):
#     credentials = ServiceAccountCredentials.from_json_keyfile_name(gcredentials, gscope)
#     gc = gspread.authorize(credentials)
#     wks = gc.open(gdocument).sheet1 
#     wks.append_row(
#         [read_data])