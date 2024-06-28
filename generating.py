import random
import re

import pymorphy2


class Generator:
    def __init__(self):
        self.morph = pymorphy2.MorphAnalyzer()

    def analyzing(self, file_name: str) -> list:
        # Метод принимает название файла со стихотворением, возвращает вложенные списки-строки с элементами строк:
        # если слово знаменательное слово, то оно заменяется на объект pymorphy2, иначе остаётся тем же
        with open(file_name, encoding='utf-8', errors='ignore') as file_with_verse:
            verse = file_with_verse.read()

        # Получаем список со всеми элементами файла: словами, знаками препинания и переноса строки
        corpus_of_verse = re.split(r'(\b\w+\b|\S)', verse)
        verse_words = [x for x in corpus_of_verse if x != '' and x != ' ']

        # Создаём список со списками-строками (пока что пустыми)
        lines_amount = len(re.findall(r'\n', string=''.join(verse_words)))
        verse_lines = [[] for line in range(lines_amount)]

        # Корректно записываем строки во вложенные списки
        current_line = 0
        for sequence in verse_words:
            escape_sequences = re.findall(r'\n', sequence)
            if escape_sequences:
                for escape in escape_sequences:
                    verse_lines[current_line].append(escape)
                    current_line += 1
            else:
                verse_lines[current_line].append(sequence)

        # Список с pymorphy-тегами служебных частей речи
        function_words_tags = ['PREP', 'CONJ', 'PRCL', 'INTJ']

        # Работа над элементами вложенных списков
        for line in range(len(verse_lines)):
            for element in range(len(verse_lines[line])):
                if (verse_lines[line][element][0].isalpha()
                        and self.morph.parse(verse_lines[line][element])[0].tag.POS not in function_words_tags):
                    verse_lines[line][element] = self.morph.parse(verse_lines[line][element])[0]

        return verse_lines

    def replacing(self, line_array: list, morph_dict: dict) -> str:
        # Метод принимает список с элементами строки и частеречный словарь, возвращает переработанную строку
        new_word = None
        new_verse_line = [None for x in line_array]

        # Пробегаем по строке
        for i in range(len(line_array)):
            if isinstance(line_array[i], pymorphy2.analyzer.Parse):
                tag = line_array[i].tag
                needed_chars = set(re.findall(r'\b[-\w]+\b', str(tag)))  # Множество нужных тегов
                part_of_speech = tag.POS
                try:
                    available_variants = list(morph_dict[part_of_speech])  # Список всех слов нужной части речи из словаря
                except KeyError:
                    new_verse_line[i] = line_array[i]
                    continue
                random.shuffle(available_variants)  # Перемешиваем для гарантии выбора случайного слова

                # Пробегаем по списку подходящих слов
                for variant in available_variants:
                    lexeme = self.morph.parse(variant)[0].lexeme  # Получаем все возможные грамматические формы слова
                    available_tags = set()  # Множество всех тегов, которые можно применить к слову
                    for parse in lexeme:
                        new_available_tags = re.findall(r'\b[-\w]+\b', str(parse.tag))
                        for new_available_tag in new_available_tags:
                            available_tags.add(new_available_tag)  # Добавляем во множество
                    if needed_chars.issubset(available_tags):
                        try:
                            # Если нужные грамматические формы принадлежат морфологической парадигме слова, то используем их
                            new_word = self.morph.parse(variant)[0].inflect(needed_chars).word
                            break
                        except AttributeError:
                            continue
                    else:
                        continue

                new_verse_line[i] = new_word
            else:
                new_verse_line[i] = line_array[i]

        # Проверяем, нужно ли привести слово к написанию с большой буквы
        for j in range(len(new_verse_line)):
            if j == 0 or new_verse_line[j - 1] in ['.', '!', '?', '«']:
                new_verse_line[j] = str(new_verse_line[j]).capitalize()
            morph_check = re.findall(r'\b[-\w]+\b', str(self.morph.parse(new_verse_line[j])[0].tag))
            for element in morph_check:
                if element in ['Name', 'Surn', 'Patr', 'Geox', 'Orgn']:
                    new_verse_line[j] = str(new_verse_line[j]).capitalize()
                    break
                elif element == 'Abbr':
                    new_verse_line[j] = str(new_verse_line[j]).upper()
                    break

        # Корректно записываем в строку
        new_verse_string = ''
        for index in range(len(new_verse_line) - 1):
            current = str(new_verse_line[index])
            next_ = str(new_verse_line[index + 1])

            new_verse_string += new_verse_line[index]

            if current[0].isalnum() and (next_[0].isalnum() or next_ in ['-', '«', '—']):
                new_verse_string += ' '
            elif current in ['.', ',', ':', ';', '»', '!', '?', '-', '—'] and (
                    next_[0].isalnum() or next_ in ['-', '«', '—']):
                new_verse_string += ' '
        new_verse_string += str(new_verse_line[-1])

        return new_verse_string


generator = Generator()
