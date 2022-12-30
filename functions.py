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

def first_join(user_id, username):
    connection = sqlite3.connect(db)
    q = connection.cursor()
    q = q.execute('SELECT * FROM users WHERE user_id IS '+str(user_id))
    row = q.fetchone()
    if row is None:
        q.execute("INSERT INTO users (user_id,  nick) VALUES ('%s', '%s')"%(user_id,username))
        connection.commit()
    connection.close()
def admin_message(text):
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
    row = cursor.fetchall()
    print('FUNC данные в таблице получены ', row)
    return row
    print(row)
    conn.close()

def user_input(value):
    # print('FUNC получена инфа о ручном вводе дня', value)
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q = q.execute(f'SELECT day FROM addiction WHERE value = "{value}"')
    value_input = q.fetchone()
    # value_input = value_input
    value_input = re.sub("[)|(|,)]", "", str(value_input))
    return value_input
    conn.close()

def value_plan(value_input):
    # print('FUNC получена инфа о дне в БД', value_input)
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q = q.execute(f'SELECT read FROM plan WHERE day IS '+str(value_input))
    value_plan = q.fetchone()
    # print('FUNC передаю инфу из плана', value_plan)
    return value_plan
    conn.close()

def addiction(day):
    day = day.replace("'", "")
    # print('FUNC получена инфа о дне', day)
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q = q.execute(f'SELECT value FROM addiction WHERE day = "{day}"')
    global value_day
    value_day = q.fetchone()
    # print('FUNC дню присвоено значение ', value_day)
    return value_day
    conn.close()
    
def reading(user_id):
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q.execute("INSERT INTO reading (user_id, day) VALUES ('%s', '%s')"%(user_id, value_day))
    # print('FUNC данные о прочтении записаны ', user_id, value_day)
    conn.commit()
    conn.close()


def whats_read(user_id):
    # print('FUNC получен запрос на список прочитанного от ', user_id)
    conn = sqlite3.connect(db)
    q = conn.cursor()
    q = q.execute(f'SELECT day FROM reading WHERE user_id = "{user_id}"')
    whats_read_data = q.fetchall()
    # print('FUNC передаю инфу польователю ', whats_read_data)
    return whats_read_data
    conn.close()


    # Запись в Google Sheet Bot
def add_to_gsheet(read_data):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(gcredentials, gscope)
    gc = gspread.authorize(credentials)
    wks = gc.open(gdocument).sheet1 
    wks.append_row(
        [read_data])