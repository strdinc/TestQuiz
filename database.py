# Импорт необходимых модулей
import sqlite3
from datetime import datetime
import os


class DatabaseManager:
    """Класс для управления базой данных SQLite, хранящей тесты и результаты"""

    def __init__(self, db_name='tests.db'):
        """
        Инициализация менеджера базы данных
        :param db_name: имя файла базы данных
        """
        self.db_name = db_name
        self._init_db()  # Создание структуры БД при инициализации

    def _init_db(self):
        """Инициализация структуры базы данных"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Создание таблицы тестов (если она не существует)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,          -- Название теста
                    path TEXT NOT NULL,          -- Путь к файлу теста
                    created_at TEXT NOT NULL     -- Дата создания
                )
            ''')

            # Создание таблицы результатов (если она не существует)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id INTEGER NOT NULL,    -- ID связанного теста
                    user_name TEXT NOT NULL,     -- Имя пользователя
                    score INTEGER NOT NULL,      -- Количество баллов
                    max_score INTEGER NOT NULL,  -- Максимальный балл
                    completed_at TEXT NOT NULL,  -- Дата завершения
                    FOREIGN KEY (test_id) REFERENCES tests (id)
                )
            ''')

            conn.commit()

    def add_test(self, name, path):
        """
        Добавление нового теста в базу данных
        :param name: название теста
        :param path: путь к файлу теста
        :return: ID добавленного теста
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO tests (name, path, created_at) VALUES (?, ?, ?)',
                (name, path, datetime.now().isoformat())
            )
            conn.commit()
            return cursor.lastrowid

    def get_all_tests(self):
        """
        Получение списка всех тестов
        :return: список кортежей (id, name, path)
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, path FROM tests')
            return cursor.fetchall()

    def add_result(self, test_id, user_name, score, max_score):
        """
        Добавление результата прохождения теста
        :param test_id: ID теста
        :param user_name: имя пользователя
        :param score: полученные баллы
        :param max_score: максимальные баллы
        :return: ID добавленной записи
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO results 
                (test_id, user_name, score, max_score, completed_at) 
                VALUES (?, ?, ?, ?, ?)''',
                (test_id, user_name, score, max_score, datetime.now().isoformat())
            )
            conn.commit()
            return cursor.lastrowid

    def get_results_for_test(self, test_id):
        """
        Получение результатов для конкретного теста
        :param test_id: ID теста
        :return: список кортежей (user_name, score, max_score, completed_at)
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT user_name, score, max_score, completed_at 
                FROM results WHERE test_id = ? ORDER BY completed_at DESC''',
                (test_id,)
            )
            return cursor.fetchall()