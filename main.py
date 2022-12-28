import telebot
from telebot import types
import time
from config import TOKEN, admins
import sqlite3
import keyboard as kb
import config as config
import functions as func
from config import db, TOKEN
import codecs




bot = telebot.TeleBot(TOKEN)
bot_username = bot.get_me().username

# Запись в Базу Данных
@bot.message_handler(commands=['start'])
def get_text_message(message):
    chat_id = message.chat.id
    username = message.from_user.username
    print('Присоединился ', username, message.from_user.id)
    func.first_join(user_id=chat_id, username=username)
    bot.send_message(message.from_user.id, 'Привет!\nЯ - бот НБЦ для чтения Библии по плану.\n\nХотите узнать, что читаем сегодня? Напишите сегодняшнюю дату в формате "31.12"!\n\nНа данный момент я еще не слишком умный, поэтому чтобы отметить прочитанный день, просто напишите мне "Прочитано". Так вы сможете отслеживать свою статистику в первое время.\n\nЕсли понадобится помощь - пишите сюда: @utkows')
    
# Рассылка

@bot.message_handler(commands=['send'])
def message1(message):
    print('MAIN получена комманда на рассылку')
    chat_id = message.chat.id
    text = message.text
    command_sender = message.from_user.id
    if command_sender in admins:
        print('MAIN команда от админа')
        msg = bot.send_message(chat_id=chat_id, text='Введите текст для рассылки. \n\nДля отмены напишите "-" без кавычек!')
        bot.register_next_step_handler(msg, message1)
    else:
        print('MAIN команда НЕ от админа')
        bot.send_message(command_sender, f'Не выйдет, извини :(')
def message1(message):
    text = message.text
    if message.text.startswith('-'):
        bot.send_message(message.chat.id, text=cancel_operation)
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

#Функции бота
# @bot.callback_query_handler(func=lambda call: True)   
# def handler_call(call):
#     chat_id = call.message.chat.id
#     message_id = call.message.message_id
#     if call.data == 'statistics':
#             bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=func.stats(), reply_markup=kb.admin)
#     elif call.data == 'message':
#         msg = bot.send_message(chat_id=chat_id,
#                                text='Введите текст для рассылки. \n\nДля отмены напишите "-" без кавычек!')
#         bot.register_next_step_handler(msg, message1)
# def message1(message):
#     text = message.text
#     if message.text.startswith('-'):
#         bot.send_message(message.chat.id, text=cancel_operation)
#     else:
#         info = func.admin_message(text)
#         bot.send_message(message.chat.id, text=' Рассылка начата!')
#         for i in range(len(info)):
#             try:
#                 time.sleep(1)
#                 bot.send_message(info[i][0], str(text))
#             except:
#                 pass
#         bot.send_message(message.chat.id, text=' Рассылка завершена!')
#         print (info)


# Основная функция бота
@bot.message_handler(content_types=['text'])
def msg_user(message):
    print('Пишет ', message.from_user.id, message.from_user.username)
    chat_id = message.chat.id
    username = message.from_user.username
    user_id = message.from_user.id
    message1 = message.text
    print('Сообщение получено', message1)
    text_message = message1
    if text_message == "Прочитано":
        func.reading(user_id = user_id, day = message1)
        bot.send_message(message.from_user.id, 'Молодец!')
    elif text_message == "прочитано":
        func.reading(user_id = user_id, day = message1)
        bot.send_message(message.from_user.id, 'Молодец!')
    else:
        info = func.msg_plan(day_input=text_message)
        print('Вывожу сообщение')
        print(info)
        if info == ([]):
            bot.send_message(message.from_user.id, 'Введите корректную дату в формате "31.12".\nВсе сломалось? Пишите @utkows')
        else:
            bot.send_message(message.from_user.id, info)
        print('Конец сессии')
 


# Поддержание работы
bot.polling(none_stop=True)
bot.infinity_polling()