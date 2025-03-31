# Импорты необходимых модулей
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QInputDialog
from database import DatabaseManager
from test_manager import TestManager, QuestionType
import sys
import os
import json
from pathlib import Path
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt

# Создание директории для хранения тестов
TESTS_DIR = Path(__file__).parent / 'tests'
TESTS_DIR.mkdir(exist_ok=True)

class MainWindow(QtWidgets.QMainWindow):
    """Класс главного окна приложения"""
    def __init__(self):
        super().__init__()
        # Загрузка интерфейса из файла
        uic.loadUi('ui/main_window.ui', self)

        # Инициализация менеджера базы данных
        self.db = DatabaseManager()

        # Настройка обработчиков кнопок
        self.btn_create_test.clicked.connect(self.open_test_creator)
        self.btn_pass_test.clicked.connect(self.open_test_passer)
        self.btn_view_results.clicked.connect(self.open_results_viewer)

    def open_test_creator(self):
        """Открытие диалога создания теста"""
        dialog = TestCreator(self)
        dialog.exec_()

    def open_test_passer(self):
        """Открытие диалога прохождения теста"""
        dialog = TestPasser(self.db, self)
        dialog.exec_()

    def open_results_viewer(self):
        """Открытие диалога просмотра результатов"""
        dialog = ResultsViewer(self.db, self)
        dialog.exec_()


class TestCreator(QtWidgets.QDialog):
    """Класс для создания новых тестов"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Загрузка интерфейса
        uic.loadUi('ui/test_creator.ui', self)

        # Инициализация менеджера тестов и списка вопросов
        self.test_manager = TestManager()
        self.questions = []

        # Подключение обработчиков кнопок
        self.btn_add_question.clicked.connect(self.add_question)
        self.btn_remove_question.clicked.connect(self.remove_question)
        self.btn_save_test.clicked.connect(self.save_test)

        # Первоначальное обновление списка вопросов
        self.update_questions_list()

    def add_question(self):
        """Добавление нового вопроса в тест"""
        # Получение типа вопроса от пользователя
        question_type, ok = QInputDialog.getItem(
            self, 'Тип вопроса', 'Выбор типа вопроса:',
            [t.value for t in QuestionType], 0, False
        )

        if not ok:
            return

        # Получение текста вопроса
        question_text, ok = QInputDialog.getText(
            self, 'Текст вопроса', 'Ввод текста вопроса:'
        )

        if not ok or not question_text:
            return

        # Обработка различных типов вопросов
        if question_type == QuestionType.MULTIPLE_CHOICE.value:
            # Получение вариантов ответов
            options = []
            for i in range(4):
                option, ok = QInputDialog.getText(
                    self, f'Вариант {i + 1}', f'Текст варианта {i + 1}:'
                )
                if ok and option:
                    options.append(option)

            if not options:
                return

            # Выбор правильного ответа
            correct_option, ok = QInputDialog.getItem(
                self, 'Правильный ответ', 'Выбор правильного варианта:',
                options, 0, False
            )

            if not ok:
                return

            # Создание вопроса с вариантами ответов
            question = TestManager.create_question(
                question_text,
                QuestionType.MULTIPLE_CHOICE,
                options=options,
                correct_answer=correct_option
            )

        else:  # Вопрос с текстовым ответом
            correct_answer, ok = QInputDialog.getText(
                self, 'Правильный ответ', 'Ввод правильного ответа:'
            )

            if not ok or not correct_answer:
                return

            # Создание вопроса с текстовым ответом
            question = TestManager.create_question(
                question_text,
                QuestionType.TEXT_ANSWER,
                correct_answer=correct_answer
            )

        # Добавление вопроса в список
        self.questions.append(question)
        self.update_questions_list()

    def remove_question(self):
        """Удаление выбранного вопроса"""
        selected = self.listWidget_questions.currentRow()
        if selected >= 0:
            self.questions.pop(selected)
            self.update_questions_list()

    def update_questions_list(self):
        """Обновление отображения списка вопросов"""
        self.listWidget_questions.clear()
        for i, question in enumerate(self.questions, 1):
            self.listWidget_questions.addItem(f"{i}. {question['text']} ({question['type']})")

    def save_test(self):
        """Сохранение теста в файл"""
        test_name = self.lineEdit_test_name.text().strip()
        if not test_name:
            QMessageBox.warning(self, 'Ошибка', 'Необходимо указать название теста')
            return

        if not self.questions:
            QMessageBox.warning(self, 'Ошибка', 'Необходимо добавить хотя бы один вопрос')
            return

        # Создание структуры теста
        test_data = TestManager.create_test(test_name, self.questions)

        # Формирование имени файла
        file_name = f"{test_name.replace(' ', '_')}.json"
        file_path = TESTS_DIR / file_name

        try:
            # Сохранение теста в файл
            TestManager.save_test(test_data, file_path)

            # Формирование относительного пути
            relative_path = os.path.join('tests', file_name)

            # Добавление теста в базу данных
            self.parent().db.add_test(test_name, relative_path)

            QMessageBox.information(self, 'Успех', f'Тест сохранен по пути:\n{file_path}')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка сохранения теста: {str(e)}')


class TestPasser(QtWidgets.QDialog):
    """Класс для прохождения тестов"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        # Загрузка интерфейса
        uic.loadUi('ui/test_passer.ui', self)

        # Инициализация переменных
        self.db = db
        self.current_question = 0
        self.answers = []
        self.test_data = None

        # Настройка элементов интерфейса
        self.radio_buttons = [
            self.radioButton_1,
            self.radioButton_2,
            self.radioButton_3,
            self.radioButton_4
        ]

        # Инициализация выпадающего списка тестов
        self.comboBox_tests.clear()
        self.comboBox_tests.addItem("Выбор теста", None)
        self.load_tests()

        # Подключение обработчиков событий
        self.comboBox_tests.currentIndexChanged.connect(self.load_selected_test)
        self.btn_prev.clicked.connect(self.prev_question)
        self.btn_next.clicked.connect(self.next_question)
        self.btn_submit.clicked.connect(self.submit_test)

        # Начальное состояние интерфейса
        self.set_buttons_enabled(False)
        self.label_question.setText("Выбор теста из списка")

        for rb in self.radio_buttons:
            rb.setVisible(False)

    def set_buttons_enabled(self, enabled):
        """Управление состоянием кнопок навигации"""
        self.btn_prev.setEnabled(enabled)
        self.btn_next.setEnabled(enabled)
        self.btn_submit.setEnabled(enabled)

    def load_tests(self):
        """Загрузка списка доступных тестов"""
        tests = self.db.get_all_tests()
        for test_id, name, path in tests:
            self.comboBox_tests.addItem(name, (test_id, path))

    def load_selected_test(self, index):
        """Загрузка выбранного теста"""
        if index == 0:
            self.set_buttons_enabled(False)
            self.label_question.setText("Выбор теста из списка")
            for rb in self.radio_buttons:
                rb.setVisible(False)
            return

        test_id, relative_path = self.comboBox_tests.currentData()

        # Преобразование относительного пути в абсолютный
        project_dir = Path(__file__).parent
        absolute_path = project_dir / relative_path

        try:
            # Загрузка данных теста
            self.test_data = TestManager.load_test(absolute_path)
            self.current_question = 0
            self.answers = [None] * len(self.test_data['questions'])
            self.show_question()
            self.set_buttons_enabled(True)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки теста: {str(e)}')
            self.set_buttons_enabled(False)
            for rb in self.radio_buttons:
                rb.setVisible(False)

    def show_question(self):
        """Отображение текущего вопроса"""
        if not self.test_data or not self.test_data['questions']:
            return

        question = self.test_data['questions'][self.current_question]
        self.label_question.setText(question['text'])

        if question['type'] == QuestionType.MULTIPLE_CHOICE.value:
            self.stackedWidget.setCurrentIndex(0)

            for rb in self.radio_buttons:
                rb.setVisible(False)
                rb.setChecked(False)

            for i, option in enumerate(question['options']):
                if i < len(self.radio_buttons):
                    rb = self.radio_buttons[i]
                    rb.setText(option)
                    rb.setVisible(True)
                    if self.answers[self.current_question] == option:
                        rb.setChecked(True)

        else:  # Вопрос с текстовым ответом
            self.stackedWidget.setCurrentIndex(1)
            self.lineEdit_answer.setText(self.answers[self.current_question] or "")
            for rb in self.radio_buttons:
                rb.setVisible(False)

        # Обновление индикатора прогресса
        total = len(self.test_data['questions'])
        self.progressBar.setValue(int((self.current_question + 1) / total * 100))

        # Обновление состояния кнопок навигации
        self.btn_prev.setEnabled(self.current_question > 0)
        self.btn_next.setEnabled(self.current_question < total - 1)

    def save_current_answer(self):
        """Сохранение ответа на текущий вопрос"""
        if not self.test_data or self.current_question >= len(self.answers):
            return

        question = self.test_data['questions'][self.current_question]

        if question['type'] == QuestionType.MULTIPLE_CHOICE.value:
            for rb in self.radio_buttons:
                if rb.isChecked() and rb.isVisible():
                    self.answers[self.current_question] = rb.text()
                    break
        else:
            self.answers[self.current_question] = self.lineEdit_answer.text()

    def prev_question(self):
        """Переход к предыдущему вопросу"""
        self.save_current_answer()
        self.current_question -= 1
        self.show_question()

    def next_question(self):
        """Переход к следующему вопросу"""
        self.save_current_answer()
        self.current_question += 1
        self.show_question()

    def submit_test(self):
        """Завершение теста и подсчет результатов"""
        if not self.test_data:
            return

        self.save_current_answer()

        # Проверка на неотвеченные вопросы
        unanswered = [i for i, ans in enumerate(self.answers) if ans is None]
        if unanswered:
            reply = QMessageBox.question(
                self, 'Неотвеченные вопросы',
                f'Количество неотвеченных вопросов: {len(unanswered)}. Завершить тест?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # Подсчет правильных ответов
        score = 0
        max_score = len(self.test_data['questions'])

        for i, question in enumerate(self.test_data['questions']):
            if self.answers[i] == question['correct_answer']:
                score += 1

        # Получение имени пользователя
        user_name, ok = QInputDialog.getText(
            self, 'Идентификация', 'Ввод имени пользователя:'
        )

        if not ok or not user_name:
            return

        # Сохранение результатов
        test_id, _ = self.comboBox_tests.currentData()
        self.db.add_result(test_id, user_name, score, max_score)

        # Отображение результатов
        QMessageBox.information(
            self, 'Результаты',
            f'Количество баллов: {score}/{max_score} ({score/max_score*100:.1f}%)'
        )

        self.accept()


class ResultsViewer(QtWidgets.QDialog):
    """Класс для просмотра результатов тестирования"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        # Загрузка интерфейса
        uic.loadUi('ui/results_viewer.ui', self)

        self.db = db

        # Инициализация выпадающего списка
        self.comboBox_tests.addItem("Выбор теста", None)
        self.load_tests()

        # Подключение обработчика
        self.comboBox_tests.currentIndexChanged.connect(self.load_results)

    def load_tests(self):
        """Загрузка списка тестов"""
        tests = self.db.get_all_tests()
        for test_id, name, path in tests:
            self.comboBox_tests.addItem(name, test_id)

    def load_results(self):
        """Загрузка результатов для выбранного теста"""
        if self.comboBox_tests.currentIndex() <= 0:
            self.tableWidget_results.setRowCount(0)
            return

        test_id = self.comboBox_tests.currentData()

        try:
            results = self.db.get_results_for_test(test_id)
            self.display_results(results)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки результатов: {str(e)}')
            self.tableWidget_results.setRowCount(0)

    def display_results(self, results):
        """Отображение результатов в таблице"""
        self.tableWidget_results.setRowCount(len(results))
        self.tableWidget_results.setColumnCount(4)

        # Настройка заголовков
        headers = ["Пользователь", "Баллы", "Дата", "Процент"]
        self.tableWidget_results.setHorizontalHeaderLabels(headers)

        for row, (user_name, score, max_score, completed_at) in enumerate(results):
            # Расчет процента правильных ответов
            percentage = (score / max_score) * 100 if max_score > 0 else 0

            # Заполнение строк таблицы
            self.tableWidget_results.setItem(row, 0, QtWidgets.QTableWidgetItem(user_name))
            self.tableWidget_results.setItem(row, 1, QtWidgets.QTableWidgetItem(f"{score}/{max_score}"))
            self.tableWidget_results.setItem(row, 2, QtWidgets.QTableWidgetItem(completed_at[:19]))
            self.tableWidget_results.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{percentage:.1f}%"))

            # Центрирование текста в ячейках
            for col in range(4):
                self.tableWidget_results.item(row, col).setTextAlignment(Qt.AlignCenter)

        # Автоматическое изменение ширины столбцов
        self.tableWidget_results.resizeColumnsToContents()


if __name__ == '__main__':
    # Создание и запуск приложения
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())