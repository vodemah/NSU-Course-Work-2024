# Файл со всеми клавиатурами, используемыми ботом

from aiogram import Bot
from aiogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import data_base_with_verses


async def set_main_menu(bot: Bot):
    # Список команд с командами и их описанием для кнопки menu
    main_menu_commands = [
        BotCommand(command='/start',
                   description='Начать работу'),
        BotCommand(command='/cancel',
                   description='Выйти из текущего состояния'),
        BotCommand(command='/menu',
                   description='Выйти в меню'),
        BotCommand(command='/info',
                   description='Информация о боте')
    ]
    await bot.set_my_commands(main_menu_commands)


menu = [[
    InlineKeyboardButton(text="📝Генерировать стихотворение",
                         callback_data='generate_verse')
]]
menu = InlineKeyboardMarkup(inline_keyboard=menu)

exit_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='◀️ Выйти в меню')]],
                              resize_keyboard=True)
exit_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='◀️ Выйти в меню')]],
                               callback_data='menu')

# Подключаемся к БД для получения данных об авторах и их темах
connection = data_base_with_verses.data_base.cursor
authors = connection.execute('SELECT author_name FROM Authors').fetchall()
authors_ids = []

for author in range(len(authors)):
    authors[author] = str(authors[author])[2:-3]
    authors_ids.append(int((str(connection.execute('SELECT author_id FROM Authors WHERE author_name = (?)',
                                                   (f'{authors[author]}',)).fetchone()))[1:-2]))
authors_data = {}

for author in range(len(authors)):
    topics = connection.execute('SELECT subject FROM Subjects WHERE author_id = (?)',
                                (f'{authors_ids[author]}',)).fetchall()
    topics.remove(topics[0])
    for topic in range(len(topics)):
        topics[topic] = str(topics[topic])[2:-3]
    authors_data.update({authors[author]: topics})


# Клавиатура для выбора автора
builder_one = InlineKeyboardBuilder()
for i in range(len(authors)):
    builder_one.button(text=f'{authors[i]}',
                       callback_data=f'{authors[i]}')
builder_one.adjust(2)
authors_table = builder_one.as_markup()


# Клавиатура для выбора темы
def topics_table_generating(author_name):
    author_topics = authors_data.get(author_name)
    builder_two = InlineKeyboardBuilder()
    for data in range(len(author_topics)):
        builder_two.button(text=f'{author_topics[data]}',
                           callback_data=f'{author_topics[data]}')
    builder_two.adjust(2)
    return builder_two.as_markup()
