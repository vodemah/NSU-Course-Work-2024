# Файл для создания базы данных со стихотворениями на основе данных сайта Культура.ру

import os
import sqlite3
import time
import uuid

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Создаём папку, куда будем помещать стихотворения, не забывая о проверке на существование
if not (os.path.isdir('Verses')):
    os.mkdir('Verses')


class DatabaseGeneration:
    def __init__(self):
        # Подключаемся к БД. Если такой БД нет, она создастся
        self.connection = sqlite3.connect('verses.db')
        self.cursor = self.connection.cursor()

        # Создаём таблицу для авторов с их ID и именами
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Authors (
        author_id integer primary key autoincrement,
        author_name text)
        ''')

        # Создаём таблицу для тем стихотворений с их ID, с ID их авторов и с названиями тем
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Subjects (
        subject_id integer primary key autoincrement,
        author_id integer,
        subject text,
        FOREIGN KEY (author_id) REFERENCES Authors(author_id))
        ''')

        # Создаём таблицу для самих стихотворений с их ID, с ID их авторов,
        # с ID их тем, с их названиями и с названиями файлов, которые их содержат
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Verses (
        verse_id integer primary key autoincrement,
        author_id integer,
        subject_id integer,
        verse_name text,
        file_name text,
        FOREIGN KEY (author_id) REFERENCES Authors(author_id),
        FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id))
        ''')

    def program(self, url, name):
        # Добавляем запись об авторе в таблицу авторов
        self.cursor.execute('INSERT INTO Authors (author_name) VALUES (?)',
                            (f'{name}',))
        self.cursor.execute('COMMIT')
        author_id = \
            self.cursor.execute('SELECT author_id FROM Authors WHERE author_name = (?)',
                                (f'{name}',)).fetchone()[0]

        # Загружаем нужную HTML-страницу
        response = requests.get(url)
        html = response.text

        # Создаём объект BeautifulSoup
        soup_of_initial_page = BeautifulSoup(html, 'html.parser')

        # Получаем строки с тегом '<а>' и классом 'HEX1L' - именно в них записаны темы стихотворений
        data = soup_of_initial_page.findAll('a', href=True, class_='HEX1L')

        # Создаём список со ссылками на страницы со стихотворениями по темам
        links_with_subjects = []

        # Создаём список с темами
        subject_list = []
        counter = 0
        for i in data:
            links_with_subjects.append('https://www.culture.ru' + i['href'])
            subject_list.append(i.text)
            # Добавляем запись о теме в таблицу тем
            self.cursor.execute('INSERT INTO Subjects (author_id, subject) VALUES (?, ?)',
                                (author_id, f'{subject_list[counter]}'))
            self.cursor.execute('COMMIT')
            counter += 1

        links_with_subjects.pop(0)  # Убираем ссылку на страницу с тегом "Все темы"
        subject_list.pop(0)  # Убираем тег "Все темы"

        for element in range(len(links_with_subjects)):
            subject_id = self.cursor.execute('SELECT subject_id'
                                             'FROM Subjects WHERE subject = (?) AND author_id = (?)',
                                             (f'{subject_list[element]}', author_id)).fetchone()[0]

            # Парсируем страницу со стихотворениями по теме
            while True:
                try:
                    session = requests.Session()
                    retry = Retry(connect=3, backoff_factor=0.5)
                    adapter = HTTPAdapter(max_retries=retry)
                    session.mount('http://', adapter)
                    session.mount('https://', adapter)
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                                      ' Chrome/124.0.0.0 Safari/537.36'}
                    response = session.get(links_with_subjects[element], headers=headers)
                    break
                except requests.exceptions.ConnectionError:
                    time.sleep(5)
                    continue

            html = response.text
            soup_of_subject_page = BeautifulSoup(html, 'html.parser')

            # Находим записи ссылок на стихотворения
            data_with_verses = soup_of_subject_page.findAll('a', href=True, class_='_9OVEn')

            # Создаём список со ссылками на отдельные стихотворения
            links_with_verses = []
            for i in data_with_verses:
                links_with_verses.append('https://www.culture.ru' + i['href'])

            for k in range(len(links_with_verses)):
                # Парсируем страницу со стихотворением
                while True:
                    try:
                        session = requests.Session()
                        retry = Retry(connect=3, backoff_factor=0.5)
                        adapter = HTTPAdapter(max_retries=retry)
                        session.mount('http://', adapter)
                        session.mount('https://', adapter)
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                                          ' (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
                        response = session.get(links_with_verses[k], headers=headers)
                        break
                    except requests.exceptions.ConnectionError:
                        time.sleep(5)
                        continue

                html = response.text
                soup_of_verse_page = BeautifulSoup(html, 'html.parser')
                verse_name = soup_of_verse_page.find('div', class_='xtEsw').text
                text_array = soup_of_verse_page.findAll(attrs={"data-content": "text"})

                # Используем uuid для названий файлов
                myUuid = str(uuid.uuid4())
                file_name = 'Verses/' + myUuid + '.txt'
                file = open(file_name, 'w', encoding="utf-8")

                for n in range(len(text_array)):
                    text = str(text_array[n])[34:-6]  # Отбрасываем лишний код страницы
                    # Не нужны строки с курсивом и жирным шрифтом
                    if '<em>' in text or '<strong>' in text:
                        continue
                    text = text.replace('<br/>', '\n')
                    text = text.replace('\xa0', ' ')  # Заменяем неразрывный пробел обычным
                    file.write(text + '\n\n')

                file.close()

                self.cursor.execute(
                    'INSERT INTO Verses (author_id, subject_id, verse_name, file_name) VALUES ( ?, ?, ?, ?)',
                    (author_id, subject_id, verse_name, file_name))
                self.cursor.execute('COMMIT')


data_base = DatabaseGeneration()

"""
Следующий код запускается лишь один раз для создания базы данных:
data_base.program('https://www.culture.ru/literature/poems/author-sergei-esenin', 'Сергей Есенин')
data_base.program('https://www.culture.ru/literature/poems/author-anna-akhmatova', 'Анна Ахматова')
data_base.program('https://www.culture.ru/literature/poems/author-aleksandr-blok', 'Александр Блок')
"""
