# Файл с функциями-обработчиками с декораторами (фильтрами)

import json
import random

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from generating import generator
import kb
import states

router = Router()  # Создаём роутер для дальнейшей привязки к нему обработчиков

author = None
topic = None
file_for_analyzing = None
lexicon = None


@router.message(Command(commands='start'))
async def start_handler(message: Message):
    # Запускает обработчик только если входящее сообщение - команда /start
    await message.answer('❤️Привет, {name}, я бот, который может генерировать псевдо-стихотворения '
                         'на основе стихотворений известных русских поэтов!'
                         .format(name=message.from_user.full_name), reply_markup=kb.menu)


@router.message(Command(commands='menu'))
async def menu(message: Message, state: FSMContext):
    # Запускает обработчик только если входящее сообщение - команда /menu
    await message.answer('Главное меню своей персоной!', reply_markup=kb.menu)
    await state.clear()


@router.message(Command(commands='cancel'),
                StateFilter(states.default_state))
async def process_cancel_command(message: Message):
    # Этот хэндлер будет срабатывать на команду "/cancel" в состоянии
    # по умолчанию и сообщать, что эта команда работает внутри машины состояний
    await message.answer(
        text='Отменять нечего. Вы вне машины состояний\n\n'
    )


@router.message(Command(commands='cancel'),
                ~StateFilter(states.default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    # Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях,
    # кроме состояния по умолчанию, и отключать машину состояний
    await message.answer(
        text='Вы вышли из машины состояний\n\n'
             'Чтобы снова перейти к генерации стихотворений - отправьте команду /start'
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


@router.message(Command(commands='info'))
async def get_information(message: Message):
    # Хэндлер, который срабатывает на команду /info
    await message.answer(
        text='Данный бот представляет из себя практическую часть курсовой работы по информатике студента @vodemah.\n\n'
             'При возникновении любых вопросов по работе бота вы можете обращаться к его автору'
    )


@router.callback_query(F.data == 'generate_verse',
                       StateFilter(states.default_state))
async def choose_author(callback: CallbackQuery, state: FSMContext):
    # Хэндлер, который срабатывает при нажатии на кнопку "Генерировать стихотворение"
    await callback.message.edit_text(text='Выберите автора:', reply_markup=kb.authors_table)
    await state.set_state(states.FSMGenerateVerses.choose_author_of_example)


@router.callback_query(F.data.in_(kb.authors_data.keys()),
                       StateFilter(states.FSMGenerateVerses.choose_author_of_example))
async def choose_topic(callback: CallbackQuery, state: FSMContext):
    # Хэндлер, который срабатывает при выборе автора в состоянии choose_author_of_example
    global author
    author = callback.data
    await callback.message.edit_text(
        f'🍃Автор: {author}. Теперь выберите тему стихотворения, которое будет взято за основу при генерации:',
        reply_markup=kb.topics_table_generating(author)
    )
    await state.set_state(states.FSMGenerateVerses.choose_topic_of_example)


@router.callback_query(StateFilter(states.FSMGenerateVerses.choose_topic_of_example))
async def get_topic(callback: CallbackQuery, state: FSMContext):
    # Хэндлер, который срабатывает при выборе темы стихотворения-примера
    global topic
    topic = callback.data
    await callback.message.edit_text('Стихотворение, которое послужит основой для генерации, выбрано.\n\n'
                                     f'Автор: {author}\nТема: {topic}\n')
    author_id = int(str(kb.connection.execute('SELECT author_id FROM Authors '
                                              'WHERE author_name = (?)',
                                              (f'{author}',)).fetchone())[1:-2])
    print(author_id)
    topic_id = int(str(kb.connection.execute('SELECT subject_id FROM Subjects '
                                             'WHERE subject = (?) AND author_id = (?)',
                                             (f'{topic}', author_id)).fetchone())[1:-2])
    print(topic_id)
    all_verses_of_topic = kb.connection.execute('SELECT file_name FROM Verses '
                                                'WHERE author_id = (?) AND subject_id = (?)',
                                                (author_id, topic_id)).fetchall()
    print(all_verses_of_topic)
    global file_for_analyzing
    file_for_analyzing = str(random.choice(all_verses_of_topic))[2:-3]
    verse_name = str(kb.connection.execute('SELECT verse_name FROM Verses '
                                           'WHERE file_name = (?)',
                                           (f'{file_for_analyzing}',)).fetchone())[2:-3]
    verse_name_for_user = verse_name.replace('\\xa0', ' ')
    await callback.message.edit_text('Стихотворение, которое послужит основой для генерации, выбрано.\n\n'
                                     f'Автор: {author}\nТема: {topic}\nНазвание: {verse_name_for_user}')
    with open(file_for_analyzing, 'r', encoding='utf-8') as f:
        data = f.read()
    if len(data) <= 4096:
        await callback.message.answer(data)
    else:
        parts = len(data) // 4096
        for part in range(parts):
            left, right = 4096 * part, 4096 * (part + 1)
            await callback.message.answer(data[left:right])
    await callback.message.answer('Теперь выберите автора, лексикон которого использовать при генерации.',
                                  reply_markup=kb.authors_table)
    await state.set_state(states.FSMGenerateVerses.choose_author_of_lexicon)


@router.callback_query(F.data.in_(kb.authors_data.keys()),
                       StateFilter(states.FSMGenerateVerses.choose_author_of_lexicon))
async def get_topic(callback: CallbackQuery, state: FSMContext):
    # Хэндлер, который срабатывает после выбора автора в состоянии choose_author_of_example.
    # Здесь вызываются важнейшие методы analyzing и replacing из модуля generating
    # и экранируется экранированное псевдо-стихотворение, а также происходит выход из машины состояний
    global lexicon
    lexicon = callback.data
    await callback.message.edit_text('При генерации будет использоваться лексикон автора ' + lexicon)

    with open('_'.join(lexicon.split()) + '_data.json') as file:
        corpus = json.load(file)

    verse_lines = generator.analyzing(file_for_analyzing)

    final_result = ''
    for line in range(len(verse_lines)):
        new_line = generator.replacing(line_array=verse_lines[line], morph_dict=corpus)
        final_result += new_line

    if len(final_result) <= 4096:
        await callback.message.answer(final_result)
    else:
        parts = len(final_result) // 4096
        for part in range(parts):
            left, right = 4096 * part, 4096 * (part + 1)
            await callback.message.answer(final_result[left:right])

    await callback.message.answer('Работа программы закончена, вы вышли из машины состояний.'
                                  '\n\nДля возобновления работы воспользуйтесь командой /start')
    await state.clear()
