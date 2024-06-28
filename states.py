# Файл хранит вспомогательный класс для FSM (машины состояний)

from aiogram.fsm.state import default_state, State, StatesGroup


class FSMGenerateVerses(StatesGroup):
    # Создаем экземпляры класса State, последовательно перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодействия с пользователем
    choose_author_of_example = State()  # Состояние ожидания выбора автора стихотворения-примера
    choose_topic_of_example = State()  # Состояние ожидания выбора темы стихотворения-примера
    choose_author_of_lexicon = State()  # Состояние ожидания выбора автора, лексику которого использовать при генерации
