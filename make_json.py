# Файл для записи частеречных словарей лексиконов авторов в json-файлы. Запускается один раз

import json
import re

import pymorphy2

import data_base_with_verses


class Corpus:
    def __init__(self):
        self.connection = data_base_with_verses.data_base.cursor
        self.morph = pymorphy2.MorphAnalyzer()

    def make_corpus(self, author_name) -> None:
        #  Метод принимает имя автора и создаёт корпус лексики из всех его стихотворений из базы данных по частям речи
        author_id = int(str(self.connection.execute('SELECT author_id FROM Authors WHERE author_name = (?)',
                                                    (f'{author_name}',)).fetchone())[1:-2])
        all_verses_of_author = self.connection.execute('SELECT file_name FROM Verses WHERE author_id = (?)',
                                                       (f'{author_id}',)).fetchall()

        # Список с названиями файлов всех стихотворений автора
        file_names = [str(file_name)[2:-3] for file_name in all_verses_of_author]

        morph_word_dict = {}

        for current_file in file_names:
            # Получаем разметку
            with open(current_file, encoding='utf-8', errors='ignore') as file:
                text = file.read().lower()

            # Разбиваем текст на отдельные слова, знаки препинания и \n
            corpus_of_current_verse = re.findall(r'(\b[-\w]+\b)', text)

            # Добавляем в словарь
            for word in corpus_of_current_verse:
                word_parse = self.morph.parse(word)[0]
                part_of_speech = word_parse.tag.POS
                if part_of_speech in morph_word_dict.keys():
                    morph_word_dict[part_of_speech].add(word)
                else:
                    morph_word_dict[part_of_speech] = {word}

        # Так как значения ключей являются множествами, меняем их на списки для дальнейшей конвертации в json
        for key in morph_word_dict.keys():
            morph_word_dict[key] = list(morph_word_dict[key])

        # Записываем данные словаря в json-файл автора
        with open('_'.join(author_name.split()) + '_data.json', 'w') as file:
            json.dump(morph_word_dict, file, ensure_ascii=False)


maker = Corpus()
for name in ['Сергей Есенин', 'Анна Ахматова', 'Александр Блок']:
    maker.make_corpus(name)
