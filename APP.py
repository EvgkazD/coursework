import sys
import time
import random
import decimal

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QMessageBox, QGridLayout, QScrollArea, QComboBox
)

from logic import Game_Solitaire

DB_AVAILABLE = None
DB_manage = None


def import_database():
    global DB_AVAILABLE, DB_manage
    if DB_AVAILABLE is not None:
        return DB_AVAILABLE
    try:
        import importlib
        database_module = importlib.import_module('database')
        DB_manage = database_module.DatabaseManager
        DB_AVAILABLE = True
        return True
    except Exception as e:
        print(f"Предупреждение: База данных недоступна: {e}")
        print("Игра будет работать без сохранения результатов в БД.")
        DB_AVAILABLE = False
        DB_manage = None
        return False

class NameInputWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("🂭 Добро пожаловать в SOLITAIRE! 🂭")
        title.setFont(QFont('Arial', 48, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        name_label = QLabel("Введите ваше имя:")
        name_label.setFont(QFont('Arial', 24))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: white;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setFont(QFont('Arial', 24))
        self.name_input.setMaximumWidth(400)
        self.name_input.setMinimumHeight(35)
        layout.addWidget(self.name_input, alignment=Qt.AlignCenter)

        mode_label = QLabel("Выберите режим сложности:")
        mode_label.setFont(QFont('Arial', 24))
        mode_label.setAlignment(Qt.AlignCenter)
        mode_label.setStyleSheet("color: white;")
        layout.addWidget(mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.setFont(QFont('Arial', 24))
        self.mode_combo.addItems(["Легкий", "Нормальный", "Сложный"])
        self.mode_combo.setMinimumWidth(200)
        self.mode_combo.setMaximumWidth(400)
        self.mode_combo.setMinimumHeight(40)
        layout.addWidget(self.mode_combo, alignment=Qt.AlignCenter)

        results_start_button = QPushButton("Просмотреть результаты")
        results_start_button.setFont(QFont('Arial', 24, QFont.Bold))
        results_start_button.setMinimumHeight(50)
        results_start_button.setStyleSheet("""
            QPushButton {
                background-color: #6A5ACD; 
                color: white;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #CC7000;
            }
        """)
        results_start_button.clicked.connect(
            self.parent_app.show_results if self.parent_app else lambda: None
        )
        layout.addWidget(results_start_button, alignment=Qt.AlignCenter)

        start_button = QPushButton("Начать игру")
        start_button.setFont(QFont('Arial', 24, QFont.Bold))
        start_button.setMinimumHeight(50)
        start_button.setMinimumWidth(200)
        start_button.setStyleSheet("""
            QPushButton {
                background-color: #6A5ACD;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #6A5ACD;
            }
        """)
        start_button.clicked.connect(self.start_game)
        layout.addWidget(start_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.name_input.setFocus()

    def start_game(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите ваше имя!")
            return

        if import_database() and DB_manage:
            try:
                db = DB_manage()
                db.init_database()
                if db.player_name_exists(name):
                    QMessageBox.warning(self, "Ошибка", "Игрок с таким именем уже существует!")
                    return
            except Exception as e:
                print(f"Предупреждение: не удалось проверить имя в БД: {e}")

        mode = self.mode_combo.currentText()
        mode_map = {"Легкий": "easy", "Нормальный": "medium", "Сложный": "hard"}
        difficulty = mode_map[mode]

        if self.parent_app:
            self.parent_app.start_game(name, difficulty)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Solitaire APP")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet("background-color: #483D8B;")

        self.db = None
        if import_database() and DB_manage:
            try:
                self.db = DB_manage()
                self.db.init_database()
            except Exception as e:
                print(f"Не удалось инициализировать базу данных: {e}")
                self.db = None

        self.player_name = ""
        self.difficulty = "medium"
        self.strategy = None
        self.game = None
        self.start_time = None
        self.timer_running = False
        self.selected_card = None
        self.selected_source = None
        self.result_saved = False
        self.bg_color = '#2d5016'
        self.hints_remaining = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.form_for_name()

    def form_for_name(self):
        self.name_widget = NameInputWidget(self)
        self.setCentralWidget(self.name_widget)

    def start_game(self, name, difficulty):
        self.player_name = name
        self.difficulty = difficulty

        if difficulty == "easy":
            self.strategy = EasyStrategy()
        elif difficulty == "medium":
            self.strategy = MediumStrategy()
        else:
            self.strategy = HardStrategy()

        self.hints_remaining = self.strategy.get_initial_hints()

        self.game = Game_Solitaire()
        self.start_time = time.time()
        self.timer_running = True
        self.result_saved = False

        colors = {
            'зеленый': '#6B8E23',
            'honey': '#CD5C5C',
            'green_gray': '#2F4F4F',
        }
        color_name = random.choice(list(colors.keys()))
        self.bg_color = colors[color_name]
        print(f"Выбран цвет фона: {color_name}")

        self.board()
        self.timer.start(1000)
        self.timer_label.setText("Время: 00:00")

    def board(self):
        self.setStyleSheet(f"background-color: {self.bg_color};")

        central_widget = QWidget()
        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()

        name_label = QLabel(f"Игрок: {self.player_name} | Режим: {self.get_difficulty_name()}")
        name_label.setFont(QFont('Arial', 14, QFont.Bold))
        name_label.setStyleSheet("color: white;")
        top_layout.addWidget(name_label)

        top_layout.addStretch()

        self.timer_label = QLabel("Время: 00:00")
        self.timer_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.timer_label.setStyleSheet("color: Lavender;")
        top_layout.addWidget(self.timer_label)

        self.hints_label = QLabel(self.get_hints_text())
        self.hints_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.hints_label.setStyleSheet("color: PeachPuff;")
        top_layout.addWidget(self.hints_label)

        main_layout.addLayout(top_layout)

        game_layout = QHBoxLayout()

        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        deck_label = QLabel("Колода")
        deck_label.setFont(QFont('Arial', 24))
        deck_label.setAlignment(Qt.AlignCenter)
        deck_label.setStyleSheet("color: white;")
        left_panel.addWidget(deck_label)

        self.deck_button = QPushButton(f"({len(self.game.deck)} карт)")
        self.deck_button.setFont(QFont('Arial', 24, QFont.Bold))
        self.deck_button.setMinimumSize(120, 100)
        self.deck_button.setStyleSheet("""
            QPushButton { background-color: #1a237e; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #283593; }
        """)
        self.deck_button.clicked.connect(self.draw_card)
        left_panel.addWidget(self.deck_button)

        waste_label = QLabel("Сброс")
        waste_label.setFont(QFont('Arial', 24))
        waste_label.setAlignment(Qt.AlignCenter)
        waste_label.setStyleSheet("color: white;")
        left_panel.addWidget(waste_label)

        self.waste_button = QPushButton("Пусто")
        self.waste_button.setFont(QFont('Arial', 24, QFont.Bold))
        self.waste_button.setMinimumSize(120, 100)
        self.waste_button.setStyleSheet("""
            QPushButton { background-color: #4a148c; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #6a1b9a; }
        """)
        self.waste_button.clicked.connect(self.use_waste_card)
        left_panel.addWidget(self.waste_button)

        left_panel.addStretch()
        game_layout.addLayout(left_panel)

        foundations_layout = QVBoxLayout()

        foundation_label = QLabel("Фундаменты")
        foundation_label.setFont(QFont('Arial', 24))
        foundation_label.setAlignment(Qt.AlignCenter)
        foundation_label.setStyleSheet("color: white;")
        foundations_layout.addWidget(foundation_label)

        foundations_grid = QGridLayout()
        suits = ['♠', '♥', '♦', '♣']
        self.foundation_buttons = []
        for i, suit in enumerate(suits):
            btn = QPushButton(f"{suit}\nПусто")
            btn.setFont(QFont('Arial', 24, QFont.Bold))
            btn.setMinimumSize(100, 100)
            btn.setStyleSheet("""
                QPushButton { background-color: #8B008B; color: white; border-radius: 5px; }
                QPushButton:hover { background-color: #00897b; }
            """)
            btn.clicked.connect(lambda checked, idx=i: self.move_to_foundation(idx))
            foundations_grid.addWidget(btn, 0, i)
            self.foundation_buttons.append(btn)

        foundations_layout.addLayout(foundations_grid)
        foundations_layout.addStretch()
        game_layout.addLayout(foundations_layout)

        tableau_container = QWidget()
        tableau_layout = QVBoxLayout(tableau_container)

        tableau_label = QLabel("Игровые стопки")
        tableau_label.setFont(QFont('Arial', 24))
        tableau_label.setAlignment(Qt.AlignCenter)
        tableau_label.setStyleSheet("color: white;")
        tableau_layout.addWidget(tableau_label)

        self.tableau_widget = QWidget()
        self.tableau_grid = QGridLayout(self.tableau_widget)
        self.tableau_grid.setSpacing(2)
        self.tableau_buttons = [[] for _ in range(7)]

        for i in range(7):
            col_label = QLabel(f"Стопка {i+1}")
            col_label.setFont(QFont('Arial', 24))
            col_label.setAlignment(Qt.AlignCenter)
            col_label.setStyleSheet("color: white;")
            self.tableau_grid.addWidget(col_label, 0, i)

        tableau_layout.addWidget(self.tableau_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidget(tableau_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical { background-color: rgba(255,255,255,50); width: 12px; border-radius: 6px; }
            QScrollBar::handle:vertical { background-color: rgba(255,255,255,150); border-radius: 6px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background-color: rgba(255,255,255,200); }
            QScrollBar:horizontal { background-color: rgba(255,255,255,50); height: 12px; border-radius: 6px; }
            QScrollBar::handle:horizontal { background-color: rgba(255,255,255,150); border-radius: 6px; min-width: 20px; }
            QScrollBar::handle:horizontal:hover { background-color: rgba(255,255,255,200); }
        """)
        scroll_area.setMaximumHeight(500)
        scroll_area.setMinimumHeight(300)
        game_layout.addWidget(scroll_area)

        main_layout.addLayout(game_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        hint_button = QPushButton("Подсказка")
        hint_button.setFont(QFont('Arial', 24))
        hint_button.setMinimumHeight(40)
        hint_button.setStyleSheet("""
            QPushButton { background-color: #9370DB; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #9370DB; }
        """)
        hint_button.clicked.connect(self.use_hint)
        buttons_layout.addWidget(hint_button)

        results_button = QPushButton("Результаты")
        results_button.setFont(QFont('Arial', 24))
        results_button.setMinimumHeight(40)
        results_button.setStyleSheet("""
                    QPushButton { background-color: #800080; color: white; border-radius: 5px; }
                    QPushButton:hover { background-color: #800080; }
                """)
        results_button.clicked.connect(self.show_results)
        buttons_layout.addWidget(results_button)

        new_game_button = QPushButton("Новая игра")
        new_game_button.setFont(QFont('Arial', 24))
        new_game_button.setMinimumHeight(40)
        new_game_button.setStyleSheet("""
            QPushButton { background-color: #9932CC; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #9932CC; }
        """)
        new_game_button.clicked.connect(self.reset_game)
        buttons_layout.addWidget(new_game_button)

        exit_button = QPushButton("Выход из игры")
        exit_button.setFont(QFont('Arial', 24))
        exit_button.setMinimumHeight(40)
        exit_button.setStyleSheet("""
            QPushButton { background-color: #8B008B; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #8B008B; }
        """)
        exit_button.clicked.connect(self.exit_game)
        buttons_layout.addWidget(exit_button)

        main_layout.addLayout(buttons_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.draw_game()

    def get_difficulty_name(self):
        names = {"easy": "Легкий", "medium": "Нормальный", "hard": "Сложный"}
        return names.get(self.difficulty, "Нормальный")

    def get_hints_text(self):
        if self.strategy.is_infinite_hints(self.hints_remaining):
            return "Подсказки: ∞"
        return f"Подсказки: {int(self.hints_remaining)}"

    def use_hint(self):
        if not self.strategy.is_hints_allowed():
            QMessageBox.information(self, "Подсказки", "В этом режиме подсказки отключены!")
            return

        if self.strategy.has_no_hints_left(self.hints_remaining):
            QMessageBox.information(self, "Подсказки", "У вас закончились подсказки!")
            return

        QMessageBox.information(self, "Подсказка", "Попробуйте переместить карты из сброса на игровое поле или фундаменты.")

        self.hints_remaining = self.strategy.decrement_hints(self.hints_remaining)
        self.hints_label.setText(self.get_hints_text())

    def show_results(self):
        if not self.db:
            QMessageBox.information(self, "Результаты", "База данных недоступна — результаты не сохраняются.")
            return

        try:
            results = self.db.get_results(limit=20)
        except Exception as e:
            print(f"Ошибка загрузки результатов: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить результаты.")
            return

        if not results:
            QMessageBox.information(self, "Результаты", "Пока нет сохранённых игр.")
            return

        msg = "<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; font-size: 14px; width: 100%;'>"
        msg += "<tr style='background-color: #DA70D6; color: white; font-weight: bold;'><th>ID</th><th>Игрок</th><th>Время</th><th>Победа</th><th>Сложность</th><th>Очки</th><th>Подсказки осталось</th></tr>"

        for row in results:
            id_, name, secs, won, diff, score, hints = row

            if secs is None:
                time_str = "Неизвестно"
            elif isinstance(secs, (int, float, decimal.Decimal)):
                try:
                    total_secs = int(secs)
                    minutes = total_secs // 60
                    seconds = total_secs % 60
                    time_str = f"{minutes:02d}:{seconds:02d}"
                except (ValueError, TypeError, decimal.InvalidOperation):
                    time_str = "Ошибка"
            else:
                time_str = "Неизвестно"

            won_str = "Да" if won else "Нет"
            diff_str = {"easy": "Легкий", "medium": "Нормальный", "hard": "Сложный"}.get(diff or "medium", "Нормальный")
            hints_str = "∞" if hints == -1 else (str(hints) if hints is not None else "-")
            score_display = score if score is not None else 0

            bg = "#f9f9f9" if id_ % 2 == 0 else "#ffffff"
            msg += f"<tr style='background-color: {bg};'><td>{id_}</td><td>{name}</td><td>{time_str}</td><td>{won_str}</td>"
            msg += f"<td>{diff_str}</td><td>{score_display}</td><td>{hints_str}</td></tr>"

        msg += "</table>"

        dialog = QMessageBox(self)
        dialog.setText("Результаты игр")
        dialog.setInformativeText(msg)
        dialog.setTextFormat(Qt.RichText)
        dialog.setMinimumWidth(900)
        dialog.setMinimumHeight(600)
        dialog.exec_()

    def draw_game(self):
        self.deck_button.setText(f"({len(self.game.deck)} карт)")

        if self.game.waste:
            waste_text = str(self.game.waste[-1])
            is_selected = (self.selected_source and self.selected_source[0] == 'waste')
            if is_selected:
                self.waste_button.setStyleSheet("""
                    QPushButton { background-color: #ffeb3b; color: black; border-radius: 5px; }
                """)
            else:
                self.waste_button.setStyleSheet("""
                    QPushButton { background-color: #4a148c; color: white; border-radius: 5px; }
                    QPushButton:hover { background-color: #6a1b9a; }
                """)
        else:
            waste_text = "Пусто"
            self.waste_button.setStyleSheet("""
                QPushButton { background-color: #4a148c; color: white; border-radius: 5px; }
                QPushButton:hover { background-color: #6a1b9a; }
            """)
        self.waste_button.setText(waste_text)
        self.waste_button.setFont(QFont('Arial', 24, QFont.Bold))

        for i, foundation in enumerate(self.game.foundations):
            if foundation:
                text = f"{foundation[-1].suit}\n{foundation[-1].rank}"
            else:
                suits = ['♠', '♥', '♦', '♣']
                text = f"{suits[i]}\nПусто"
            self.foundation_buttons[i].setText(text)
            self.foundation_buttons[i].setFont(QFont('Arial', 24, QFont.Bold))

        for i in range(7):
            for j in range(len(self.tableau_buttons[i])):
                btn = self.tableau_buttons[i][j]
                self.tableau_grid.removeWidget(btn)
                btn.setParent(None)
                btn.deleteLater()
            self.tableau_buttons[i] = []

        for i in range(7):
            if not self.game.tableau[i]:
                empty_btn = QPushButton("Пусто")
                empty_btn.setFont(QFont('Arial', 24))
                empty_btn.setMinimumSize(110, 70)
                empty_btn.setMaximumSize(110, 70)
                empty_btn.setStyleSheet("""
                    QPushButton { background-color: #424242; color: white; border-radius: 3px; }
                    QPushButton:hover { opacity: 0.8; }
                """)
                empty_btn.clicked.connect(lambda checked, col=i: self.try_move_card(col, None))
                self.tableau_grid.addWidget(empty_btn, 1, i)
                self.tableau_buttons[i].append(empty_btn)
            else:
                for j, card in enumerate(self.game.tableau[i]):
                    is_selected = (self.selected_source and
                                   self.selected_source[0] == 'tableau' and
                                   self.selected_source[1] == i and
                                   self.selected_source[2] == j)

                    if card.face_up:
                        card_text = f"{card.rank}{card.suit}"
                        bg_color = '#ffeb3b' if is_selected else ('#ffffff' if card.color == 'red' else '#e0e0e0')
                        fg_color = '#d32f2f' if card.color == 'red' else '#000000'
                    else:
                        card_text = "🃏"
                        bg_color = '#ffeb3b' if is_selected else '#1a237e'
                        fg_color = 'white'

                    btn = QPushButton(card_text)
                    btn.setFont(QFont('Arial', 24, QFont.Bold))
                    btn.setMinimumSize(110, 70)
                    btn.setMaximumSize(110, 70)
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {bg_color};
                            color: {fg_color};
                            border-radius: 3px;
                        }}
                        QPushButton:hover {{ opacity: 0.8; }}
                    """)
                    btn.clicked.connect(lambda checked, col=i, idx=j: self.select_tableau_card(col, idx))
                    self.tableau_grid.addWidget(btn, j + 1, i)
                    self.tableau_buttons[i].append(btn)

        if self.check_win():
            self.end_game(True)

    def draw_card(self):
        if not self.game.deck:
            self.game.deck = self.game.waste[::-1]
            self.game.waste = []
        if self.game.deck:
            card = self.game.deck.pop()
            card.face_up = True
            self.game.waste.append(card)
            self.draw_game()

    def use_waste_card(self):
        if not self.game.waste:
            return
        self.selected_card = self.game.waste[-1]
        self.selected_source = ('waste', None)
        self.draw_game()

    def select_tableau_card(self, column, index):
        if index < len(self.game.tableau[column]) and self.game.tableau[column][index].face_up:
            if self.selected_card and self.selected_source:
                if (self.selected_source[0] == 'tableau' and
                        self.selected_source[1] == column and
                        self.selected_source[2] == index):
                    self.clear_selection()
                    self.draw_game()
                else:
                    self.try_move_card(column, index)
            else:
                self.selected_card = self.game.tableau[column][index]
                self.selected_source = ('tableau', column, index)
                self.draw_game()

    def try_move_card(self, target_column, target_index=None):
        if not self.selected_card or not self.selected_source:
            return

        card = self.selected_card
        source_type = self.selected_source[0]
        target_col = target_column

        if not self.game.tableau[target_col]:
            if card.rank == 'K':
                if source_type == 'tableau':
                    source_col = self.selected_source[1]
                    source_idx = self.selected_source[2]
                    cards_to_move = self.game.tableau[source_col][source_idx:]
                    self.game.tableau[target_col].extend(cards_to_move)
                    self.game.tableau[source_col] = self.game.tableau[source_col][:source_idx]
                    if self.game.tableau[source_col] and not self.game.tableau[source_col][-1].face_up:
                        self.game.tableau[source_col][-1].face_up = True
                elif source_type == 'waste':
                    self.game.waste.pop()
                    self.game.tableau[target_col].append(card)
                self.clear_selection()
                self.draw_game()
                return
        else:
            top_card = self.game.tableau[target_col][-1]
            if self.game.game_stopka(card, top_card):
                if source_type == 'waste':
                    self.game.waste.pop()
                    self.game.tableau[target_col].append(card)
                elif source_type == 'tableau':
                    source_col = self.selected_source[1]
                    source_idx = self.selected_source[2]
                    cards_to_move = self.game.tableau[source_col][source_idx:]
                    if all(c.face_up for c in cards_to_move):
                        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
                        is_valid_sequence = True
                        for k in range(len(cards_to_move) - 1):
                            c1 = cards_to_move[k]
                            c2 = cards_to_move[k + 1]
                            if c1.color == c2.color:
                                is_valid_sequence = False
                                break
                            idx1 = ranks.index(c1.rank)
                            idx2 = ranks.index(c2.rank)
                            if idx2 != idx1 - 1:
                                is_valid_sequence = False
                                break
                        if is_valid_sequence:
                            self.game.tableau[target_col].extend(cards_to_move)
                            self.game.tableau[source_col] = self.game.tableau[source_col][:source_idx]
                            if self.game.tableau[source_col] and not self.game.tableau[source_col][-1].face_up:
                                self.game.tableau[source_col][-1].face_up = True
                        else:
                            self.game.tableau[target_col].append(cards_to_move[0])
                            self.game.tableau[source_col] = self.game.tableau[source_col][:source_idx + 1]
                            if self.game.tableau[source_col] and not self.game.tableau[source_col][-1].face_up:
                                self.game.tableau[source_col][-1].face_up = True
                    else:
                        self.game.tableau[target_col].append(cards_to_move[0])
                        self.game.tableau[source_col] = self.game.tableau[source_col][:source_idx + 1]
                        if self.game.tableau[source_col] and not self.game.tableau[source_col][-1].face_up:
                            self.game.tableau[source_col][-1].face_up = True
                self.clear_selection()
                self.draw_game()
                return

        self.clear_selection()
        self.draw_game()

    def move_to_foundation(self, foundation_index):
        if not self.selected_card:
            return
        card = self.selected_card
        foundation = self.game.foundations[foundation_index]
        if self.game.can_move_to_foundation(card, foundation):
            source_type = self.selected_source[0]
            if source_type == 'waste':
                self.game.waste.pop()
            elif source_type == 'tableau':
                source_col = self.selected_source[1]
                source_idx = self.selected_source[2]
                self.game.tableau[source_col].pop(source_idx)
                if self.game.tableau[source_col] and not self.game.tableau[source_col][-1].face_up:
                    self.game.tableau[source_col][-1].face_up = True
            foundation.append(card)
            self.clear_selection()
            self.draw_game()

    def clear_selection(self):
        self.selected_card = None
        self.selected_source = None

    def update_timer(self):
        if self.timer_running and self.start_time:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.timer_label.setText(f"Время: {minutes:02d}:{seconds:02d}")

    def check_win(self):
        for foundation in self.game.foundations:
            if len(foundation) != 13:
                return False
        return True

    def end_game(self, won=False):
        self.timer_running = False
        self.timer.stop()

        if won:
            elapsed = time.time() - self.start_time
            total_seconds = int(elapsed)
            base_score = 1000
            time_penalty = total_seconds
            hint_bonus = self.strategy.calculate_hint_bonus(self.hints_remaining)

            final_score = max(0, base_score - time_penalty + hint_bonus)

            saved = False
            if self.db:
                try:
                    saved = self.db.save_result(
                        self.player_name,
                        total_seconds,
                        True,
                        self.difficulty,
                        final_score,
                        self.strategy.get_hints_for_db(self.hints_remaining)
                    )
                    self.result_saved = True
                except Exception as e:
                    print(f"Ошибка при сохранении результата: {e}")

            save_message = "\nРезультат сохранен в базу данных." if saved else "\nРезультат не сохранен (БД недоступна)."

            msg = QMessageBox(self)
            msg.setWindowTitle("Поздравляем!")
            msg.setText(
                f"Вы выиграли!\n"
                f"Время: {total_seconds // 60:02d}:{total_seconds % 60:02d}\n"
                f"Очки: {final_score}{save_message}"
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

            reply = QMessageBox.question(
                self, 'Новая игра', 'Хотите сыграть еще раз?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.reset_game()
            else:
                self.close()
        else:
            QMessageBox.information(self, "Игра завершена", "Молодец!")

    def exit_game(self):
        self.save_current_result_if_needed()
        self.close()

    def closeEvent(self, event):
        self.save_current_result_if_needed()
        event.accept()

    def save_current_result_if_needed(self):
        if self.game and self.start_time and not self.result_saved:
            elapsed = time.time() - self.start_time
            if self.db:
                try:
                    self.db.save_result(
                        self.player_name,
                        int(elapsed),
                        False,
                        self.difficulty,
                        0,
                        self.strategy.get_hints_for_db(self.hints_remaining) if self.strategy else -1
                    )
                    self.result_saved = True
                except Exception as e:
                    print(f"Ошибка при сохранении результата: {e}")

    def reset_game(self):
        self.save_current_result_if_needed()
        self.timer_running = False
        self.timer.stop()
        self.form_for_name()


class DifficultyStrategy:
    def get_initial_hints(self):
        raise NotImplementedError

    def is_hints_allowed(self):
        raise NotImplementedError

    def has_no_hints_left(self, hints_remaining):
        raise NotImplementedError

    def decrement_hints(self, hints_remaining):
        raise NotImplementedError

    def is_infinite_hints(self, hints_remaining):
        raise NotImplementedError

    def calculate_hint_bonus(self, hints_remaining):
        raise NotImplementedError

    def get_hints_for_db(self, hints_remaining):
        raise NotImplementedError


class EasyStrategy(DifficultyStrategy):
    def get_initial_hints(self):
        return float('inf')

    def is_hints_allowed(self):
        return True

    def has_no_hints_left(self, hints_remaining):
        return False

    def decrement_hints(self, hints_remaining):
        return hints_remaining

    def is_infinite_hints(self, hints_remaining):
        return True

    def calculate_hint_bonus(self, hints_remaining):
        return 250

    def get_hints_for_db(self, hints_remaining):
        return -1


class MediumStrategy(DifficultyStrategy):
    def get_initial_hints(self):
        return 5

    def is_hints_allowed(self):
        return True

    def has_no_hints_left(self, hints_remaining):
        return hints_remaining <= 0

    def decrement_hints(self, hints_remaining):
        return hints_remaining - 1

    def is_infinite_hints(self, hints_remaining):
        return False

    def calculate_hint_bonus(self, hints_remaining):
        return int(hints_remaining) * 50

    def get_hints_for_db(self, hints_remaining):
        return int(hints_remaining)


class HardStrategy(DifficultyStrategy):
    def get_initial_hints(self):
        return 0

    def is_hints_allowed(self):
        return False

    def has_no_hints_left(self, hints_remaining):
        return True
    def decrement_hints(self, hints_remaining):
        return hints_remaining

    def is_infinite_hints(self, hints_remaining):
        return False

    def calculate_hint_bonus(self, hints_remaining):
        return 0

    def get_hints_for_db(self, hints_remaining):
        return 0


def main():
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()