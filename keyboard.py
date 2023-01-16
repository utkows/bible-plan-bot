from telebot import types
import sqlite3


# import functions as func

admin = types.InlineKeyboardMarkup(row_width=2)
admin.add(
    types.InlineKeyboardButton('Рассылка', callback_data='admin_msg'),
    types.InlineKeyboardButton('Сообщение пользователю', callback_data='admin_msg_user'),
    types.InlineKeyboardButton('Статистика', callback_data='statistics'),
    types.InlineKeyboardButton('Выгрузка БД', callback_data='subd'),
    types.InlineKeyboardButton('Логи', callback_data='logging')
)

menu = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
whats_read = types.InlineKeyboardButton('🎁 Что читаем сегодня?', callback_data='whats_read')
stat = types.InlineKeyboardButton('📊 Отчет', callback_data='reading')
help = types.InlineKeyboardButton('🆘 Помощь', callback_data='help')
menu.add(whats_read)
menu.add(stat, help)


read = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
read.add(
    types.InlineKeyboardButton('✅ Прочитано!', callback_data='read'),
    types.InlineKeyboardButton('🔙 Назад', callback_data='back'),
)

back = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
back.add(
    types.InlineKeyboardButton('🔙 Назад', callback_data='back'),
)

statistics = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
statistics.add(
    types.InlineKeyboardButton('✍️ Ввести номер дня', callback_data='input_day'), 
    types.InlineKeyboardButton('🗓 Отметить дни как прочитанные', callback_data='check_all_days'),
    types.InlineKeyboardButton('🔙 Назад', callback_data='back'),
    types.InlineKeyboardButton('❌ Удалить отметку о прочтении', callback_data='input_day'),
    # types.InlineKeyboardButton('📊 Обновить отчет', callback_data='update_stat')
)

input_read_advance = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
input_read_advance.add(
    types.InlineKeyboardButton('✍️ Ввести номер дня', callback_data='input_day'),
    types.InlineKeyboardButton('🗞 Показать все прочитанные дни', callback_data='input_day_advance'),
    types.InlineKeyboardButton('🔙 Назад', callback_data='back'),
    types.InlineKeyboardButton('❌ Удалить отметку о прочтении', callback_data='input_day')
)

yes_no = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
yes_no.add(
    types.InlineKeyboardButton('❌ Нет!', callback_data='no'),
    types.InlineKeyboardButton('✅ Да!', callback_data='yes')
)

input_read_all_list = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
input_read_all_list.add(
    types.InlineKeyboardButton('✍️ Ввести номер дня', callback_data='input_day'), 
    types.InlineKeyboardButton('❌ Удалить отметку о прочтении', callback_data='input_day'),
    types.InlineKeyboardButton('🔙 Назад', callback_data='back')
)


quesch = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
quesch.add(
    types.InlineKeyboardButton('✉️ Отправить сообщение', callback_data='send_msg'),
    types.InlineKeyboardButton('🔙 Назад', callback_data='back'),
)

input_day = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
input_day.add(
    types.InlineKeyboardButton('✅ Прочитано!', callback_data='read'),
    types.InlineKeyboardButton('✍️ Ввести другой день', callback_data='input_day'), 
    types.InlineKeyboardButton('🔙 Назад', callback_data='back')
)

check = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
check.add(
    types.InlineKeyboardButton('✍️ Отметить день', callback_data='input_day'), 
    types.InlineKeyboardButton('✅ Всё прочитано', callback_data='check_all_days'),
    types.InlineKeyboardButton('🔙 Назад', callback_data='back'),
    types.InlineKeyboardButton('❌ Удалить отметку о прочтении', callback_data='input_day')
)

check_day = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
check_day.add(
    types.InlineKeyboardButton('✍️ Ввести другой день', callback_data='input_day'), 
    types.InlineKeyboardButton('🔙 Назад', callback_data='back')
)

delete_more = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
delete_more.add(
    types.InlineKeyboardButton('❌ Удалить другой день', callback_data='input_day'), 
    types.InlineKeyboardButton('🔙 Назад', callback_data='back')
)

inline_read = types.InlineKeyboardMarkup(row_width=1)
inline_read.add(
    types.InlineKeyboardButton('👌 Я прочитал!', callback_data='inline_read')
)


today_verify = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
check_ver = types.InlineKeyboardButton('✅ Прочитано!', callback_data='input_day')
del_check_ver = types.InlineKeyboardButton('❌ Удалить отметку о прочтении', callback_data='input_day')
back_ver = types.InlineKeyboardButton('🔙 Назад', callback_data='back')
today_verify.add(check_ver)
today_verify.add(back_ver, del_check_ver)

