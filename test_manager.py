import json
from enum import Enum


class QuestionType(Enum):
    """Перечисление типов вопросов в тесте"""
    MULTIPLE_CHOICE = "тестовый вопрос"  # Вопрос с вариантами ответов
    TEXT_ANSWER = "с развернутым ответом"  # Вопрос с текстовым ответом


class TestManager:
    """Класс для управления тестами: создания, сохранения и загрузки"""

    @staticmethod
    def save_test(test_data, file_path):
        """
        Сохранение теста в файл формата JSON
        :param test_data: данные теста для сохранения
        :param file_path: путь к файлу для сохранения
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_test(file_path):
        """
        Загрузка теста из JSON-файла
        :param file_path: путь к файлу с тестом
        :return: данные теста
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def create_test(name, questions):
        """
        Создание структуры теста
        :param name: название теста
        :param questions: список вопросов
        :return: словарь с данными теста
        """
        return {
            "name": name,
            "questions": questions
        }

    @staticmethod
    def create_question(question_text, question_type, options=None, correct_answer=None):
        """
        Создание вопроса заданного типа
        :param question_text: текст вопроса
        :param question_type: тип вопроса
        :param options: варианты ответов (для тестового вопроса)
        :param correct_answer: правильный ответ
        :return: словарь с данными вопроса
        """
        question = {
            "text": question_text,
            "type": question_type.value if isinstance(question_type, QuestionType) else question_type,
        }

        # Добавление специфичных полей в зависимости от типа вопроса
        if question_type == QuestionType.MULTIPLE_CHOICE:
            question["options"] = options  # Список вариантов ответов
            question["correct_answer"] = correct_answer  # Правильный вариант
        elif question_type == QuestionType.TEXT_ANSWER:
            question["correct_answer"] = correct_answer  # Текст правильного ответа

        return question