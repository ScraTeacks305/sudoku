from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.properties import NumericProperty
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.clock import Clock
import random

class SettingsDialog(Popup):
    def __init__(self, callback, allow_cancel=True, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.allow_cancel = allow_cancel
        self.title = ''
        self.separator_height = 0
        self.overlay_color = (0,0,0,0.5)
        self.background = ''
        self.size_hint = (0.85, None)
        self.height = dp(280)

        root = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(15))
        with root.canvas.before:
            Color(1,1,1,1)
            self.rect = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=self._update_rect, pos=self._update_rect)

        root.add_widget(Label(text="Новая игра", font_size=dp(20), bold=True, color=(0.1,0.1,0.1,1), size_hint_y=None, height=dp(30)))

        root.add_widget(Label(text="Сложность:", font_size=dp(14), color=(0.3,0.3,0.3,1)))
        self.diff_spinner = Spinner(
            text='Средний',
            values=['Очень лёгкий', 'Лёгкий', 'Средний', 'Сложный', 'Эксперт'],
            size_hint=(1, None),
            height=dp(40)
        )
        root.add_widget(self.diff_spinner)

        root.add_widget(Label(text="Макс. ошибок:", font_size=dp(14), color=(0.3,0.3,0.3,1)))
        self.err_input = TextInput(text="3", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        root.add_widget(self.err_input)

        root.add_widget(Label(text="Кол-во подсказок:", font_size=dp(14), color=(0.3,0.3,0.3,1)))
        self.hints_input = TextInput(text="3", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        root.add_widget(self.hints_input)

        btn_box = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(40))
        start_btn = Button(text="Начать", font_size=dp(16),
                           background_normal='', background_down='',
                           background_color=(0.2,0.6,1,1), color=(1,1,1,1))
        start_btn.bind(on_release=self.on_start)
        btn_box.add_widget(start_btn)
        if self.allow_cancel:
            cancel_btn = Button(text="Отмена", font_size=dp(16),
                                background_normal='', background_down='',
                                background_color=(0.9,0.9,0.9,1), color=(0.2,0.2,0.2,1))
            cancel_btn.bind(on_release=self.dismiss)
            btn_box.add_widget(cancel_btn)
        root.add_widget(btn_box)

        self.content = root

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_start(self, *args):
        try:
            diff_ranges = {
                'Очень лёгкий': (20, 25),
                'Лёгкий': (26, 32),
                'Средний': (33, 40),
                'Сложный': (41, 50),
                'Эксперт': (51, 55)
            }
            diff_min, diff_max = diff_ranges[self.diff_spinner.text]
            diff = random.randint(diff_min, diff_max)
            max_err = int(self.err_input.text)
            hints = int(self.hints_input.text)
            self.callback(diff, max_err, hints)
            self.dismiss()
        except ValueError:
            self.show_error("Введите целые числа")

    def show_error(self, msg):
        popup = Popup(title='', separator_height=0, overlay_color=(0,0,0,0.5),
                      background='', size_hint=(0.7, 0.25))
        layout = BoxLayout(orientation='vertical', padding=dp(15))
        with layout.canvas.before:
            Color(1,1,1,1)
            layout.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=lambda i,v: setattr(i.rect, 'size', v),
                    pos=lambda i,v: setattr(i.rect, 'pos', v))
        layout.add_widget(Label(text=msg, color=(0.2,0.2,0.2,1)))
        popup.content = layout
        popup.open()

class SudokuGrid(BoxLayout):
    difficulty = NumericProperty(40)
    max_errors = NumericProperty(3)
    hints_total = NumericProperty(3)
    hints_left = NumericProperty(3)
    errors_made = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 0
        self.padding = 0
        self.puzzle = None
        self.solution = None
        self.given = None
        self.selected_row = None
        self.selected_col = None
        self.buttons_enabled = True
        self.game_ended = False

        # Верхняя панель со счётчиками
        top_bar = BoxLayout(size_hint_y=0.045, spacing=dp(15), padding=(dp(10), dp(1)))
        with top_bar.canvas.before:
            Color(0.96, 0.96, 0.96, 1)
            self.top_bg = Rectangle(size=top_bar.size, pos=top_bar.pos)
        top_bar.bind(size=self._update_top_bg, pos=self._update_top_bg)
        self.error_label = Label(text="Ошибки: 0/3", font_size=dp(14), color=(0,0,0,1))
        self.hint_label = Label(text="Подсказки: 3/3", font_size=dp(14), color=(0,0,0,1))
        top_bar.add_widget(self.error_label)
        top_bar.add_widget(self.hint_label)
        self.top_bar = top_bar

        # Игровое поле
        self.field_box = BoxLayout(orientation='vertical', size_hint=(1, 0.70))
        with self.field_box.canvas.before:
            Color(0.96, 0.96, 0.96, 1)
            self.bg_rect = Rectangle()
        self.field_box.bind(size=self._update_bg, pos=self._update_bg)

        spacer_top = BoxLayout(size_hint=(1, 1))
        self.field_box.add_widget(spacer_top)

        self.grid = GridLayout(cols=9, spacing=0, padding=0,
                               size_hint=(None, None))
        self.cells = {}
        for i in range(9):
            for j in range(9):
                btn = Button(text='', font_size=dp(22),
                             background_normal='',
                             background_down='',
                             background_color=(1,1,1,1),
                             color=(0,0,0,1))
                btn.is_error = False
                btn.bind(on_release=self.on_cell_click)
                self.grid.add_widget(btn)
                self.cells[(i, j)] = btn
        self.field_box.add_widget(self.grid)

        spacer_bottom = BoxLayout(size_hint=(1, 1))
        self.field_box.add_widget(spacer_bottom)
        self.add_widget(self.top_bar)
        self.add_widget(self.field_box)

        self.digit_buttons = {}

        # Кнопки цифр с закруглёнными краями
        self.num_panel = BoxLayout(orientation='horizontal', spacing=dp(6), padding=(dp(8), dp(0)),
                                   size_hint_y=0.11)
        for num in range(1, 10):
            btn = Button(text=f'[size=64]{num}[/size]\n[size=32][color=888888]9[/color][/size]', markup=True, font_size=dp(16),
                         background_normal='', background_down='',
                         background_color=(0,0,0,0), # прозрачный фон
                         color=(0,0,0.8,1))
            with btn.canvas.before:
                Color(1,1,1,1)
                btn.bg_rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(10)])
            btn.bind(pos=self._update_btn_bg, size=self._update_btn_bg)
            btn.bind(on_release=lambda instance, n=num: self.on_digit_button(n))
            self.digit_buttons[num] = btn
            self.num_panel.add_widget(btn)
        clear_btn = Button(text='C', font_size=dp(16),
                           background_normal='', background_down='',
                           background_color=(0,0,0,0),
                           color=(0,0,0.8,1))
        with clear_btn.canvas.before:
            Color(1,1,1,1)
            clear_btn.bg_rect = RoundedRectangle(pos=clear_btn.pos, size=clear_btn.size, radius=[dp(10)])
        clear_btn.bind(pos=self._update_btn_bg, size=self._update_btn_bg)
        clear_btn.bind(on_release=lambda instance: self.clear_cell())
        self.num_panel.add_widget(clear_btn)
        self.add_widget(self.num_panel)

        # Главные кнопки управления
        ctrl_box = BoxLayout(size_hint_y=0.10, spacing=dp(8), padding=(dp(8), dp(4)))
        btn_new = Button(text="Новая", font_size=dp(18),
                         background_normal='', background_down='',
                         background_color=(1,1,1,1),
                         color=(0,0,0,1))
        btn_hint = Button(text="Подсказка", font_size=dp(18),
                          background_normal='', background_down='',
                          background_color=(1,1,1,1),
                          color=(0,0,0,1))
        btn_solve = Button(text="Решение", font_size=dp(18),
                           background_normal='', background_down='',
                           background_color=(1,1,1,1),
                           color=(0,0,0,1))
        btn_new.bind(on_release=self.ask_new_game)
        btn_hint.bind(on_release=self.use_hint)
        btn_solve.bind(on_release=self.show_solution)
        ctrl_box.add_widget(btn_new)
        ctrl_box.add_widget(btn_hint)
        ctrl_box.add_widget(btn_solve)
        self.add_widget(ctrl_box)

        self.bind(size=self.adjust_grid_size)
        self.bind(pos=self.adjust_grid_size)
        self.all_lines = []
        Clock.schedule_once(self.draw_all_lines, 0.5)
        self.new_game(self.difficulty, self.max_errors, self.hints_total)

    def _update_btn_bg(self, instance, value):
        instance.bg_rect.pos = instance.pos
        instance.bg_rect.size = instance.size

    def _update_top_bg(self, instance, value):
        self.top_bg.size = instance.size
        self.top_bg.pos = instance.pos

    def _update_bg(self, instance, *args):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def draw_all_lines(self, *args):
        for instr in self.all_lines:
            self.field_box.canvas.after.remove(instr)
        self.all_lines.clear()

        if self.grid.width == 0 or self.grid.height == 0:
            return

        w = self.grid.width
        h = self.grid.height
        cell = w / 9
        gx, gy = self.grid.pos

        with self.field_box.canvas.after:
            Color(0.6, 0.6, 0.6, 1)
            for col in range(1, 9):
                x = gx + col * cell
                line = Line(points=[x, gy, x, gy + h], width=0.5)
                self.all_lines.append(line)
            for row in range(1, 9):
                y = gy + h - row * cell
                line = Line(points=[gx, y, gx + w, y], width=0.5)
                self.all_lines.append(line)

            Color(0, 0, 0, 1)
            for col in (3, 6):
                x = gx + col * cell
                line = Line(points=[x, gy, x, gy + h], width=2)
                self.all_lines.append(line)
            for row in (3, 6):
                y = gy + h - row * cell
                line = Line(points=[gx, y, gx + w, y], width=2)
                self.all_lines.append(line)

            left_line = Line(points=[gx, gy, gx, gy + h], width=2)
            self.all_lines.append(left_line)
            right_line = Line(points=[gx + w, gy, gx + w, gy + h], width=2)
            self.all_lines.append(right_line)
            top_line = Line(points=[gx, gy + h, gx + w, gy + h], width=2)
            self.all_lines.append(top_line)
            bottom_line = Line(points=[gx, gy, gx + w, gy], width=2)
            self.all_lines.append(bottom_line)

    def adjust_grid_size(self, instance, size):
        cell_size = min(size[0] - dp(4), size[1] - dp(4)) / 9
        if cell_size > 0:
            self.grid.width = cell_size * 9
            self.grid.height = cell_size * 9
            self.grid.size = (cell_size * 9, cell_size * 9)
            for (r,c), btn in self.cells.items():
                btn.font_size = cell_size * 0.44
        self.draw_all_lines()

    def update_digit_counters(self):
        for num in range(1, 10):

            used = sum(row.count(num) for row in self.puzzle) if self.puzzle else 0

            left = max(0, 9 - used)

            if num in self.digit_buttons:

                btn = self.digit_buttons[num]

                btn.text = (
                    f'[size=64]{num}[/size]\n'
                    f'[size=32][color=888888]{left}[/color][/size]'
                )

                if left == 0:
                    btn.opacity = 0
                    btn.disabled = True
                else:
                    btn.opacity = 1
                    btn.disabled = False

    def update_status(self):
        self.error_label.text = f"Ошибки: {self.errors_made}/{self.max_errors}"
        self.hint_label.text = f"Подсказки: {self.hints_left}/{self.hints_total}"
    def draw_board(self):
        self.update_digit_counters()
        highlight_cells = set()
        same_digit_cells = set()
        if self.selected_row is not None and self.selected_col is not None and not self.game_ended:
            sr, sc = self.selected_row, self.selected_col
            selected_val = self.puzzle[sr][sc]
            for k in range(9):
                highlight_cells.add((sr, k))
                highlight_cells.add((k, sc))
            box_r, box_c = sr // 3 * 3, sc // 3 * 3
            for r in range(box_r, box_r + 3):
                for c in range(box_c, box_c + 3):
                    highlight_cells.add((r, c))
            if selected_val != 0:
                for i in range(9):
                    for j in range(9):
                        if self.puzzle[i][j] == selected_val and (i, j) != (sr, sc):
                            same_digit_cells.add((i, j))

        for i in range(9):
            for j in range(9):
                val = self.puzzle[i][j]
                btn = self.cells[(i, j)]
                btn.text = str(val) if val != 0 else ''

                # Сначала определяем цвет текста (ошибка -> красный)
                if btn.is_error:
                    btn.color = (0.9, 0.1, 0.1, 1) # тёмно-красный текст
                elif self.given[i][j]:
                    btn.color = (0,0,0,1) # чёрный для исходных
                elif val != 0:
                    btn.color = (0,0,0.8,1) # синий для введённых верных
                else:
                    btn.color = (0,0,0,1) # чёрный для пустых

                # Фон всегда белый (кроме подсветок), не меняем при ошибке
                if not self.game_ended and i == self.selected_row and j == self.selected_col:
                    btn.background_color = (0.75, 0.9, 1, 1) # голубой выделенной
                elif (i, j) in same_digit_cells:
                    btn.background_color = (0.85, 0.95, 1, 1) # светлее голубой для одинаковых цифр
                elif (i, j) in highlight_cells:
                    btn.background_color = (0.941, 0.941, 0.941, 1) # светло-серый для строки/столбца/квадрата
                else:
                    btn.background_color = (1,1,1,1) # обычный белый

    def new_game(self, diff, max_err, hints):
        self.difficulty = diff
        self.max_errors = max_err
        self.hints_total = hints
        self.hints_left = hints
        self.errors_made = 0
        self.update_status()
        self.puzzle, self.solution = self.generate_puzzle(diff)
        self.given = [[self.puzzle[i][j] != 0 for j in range(9)] for i in range(9)]
        for (i,j), btn in self.cells.items():
            btn.is_error = False
        self.selected_row = None
        self.selected_col = None
        self.game_ended = False
        self.buttons_enabled = True
        for btn in self.digit_buttons.values():
            btn.opacity = 1
            btn.disabled = False
        self.draw_board()

    def on_cell_click(self, instance):
        if self.game_ended or not self.buttons_enabled:
            return
        for (r,c), btn in self.cells.items():
            if btn == instance:
                self.cell_touched(r, c)
                break

    def cell_touched(self, row, col):
        if self.selected_row == row and self.selected_col == col:
            self.selected_row = None
            self.selected_col = None
        else:
            self.selected_row = row
            self.selected_col = col
        self.draw_board()

    def on_digit_button(self, num):
        if self.game_ended or not self.buttons_enabled:
            return

        if self.selected_row is None or self.selected_col is None:
            return

        row, col = self.selected_row, self.selected_col

        if self.given[row][col]:
            return

        self.set_cell(row, col, num)

    def clear_cell(self, instance=None):
        if self.game_ended or not self.buttons_enabled or self.selected_row is None:
            return
        row, col = self.selected_row, self.selected_col
        if self.given[row][col]:
            return
        self.puzzle[row][col] = 0
        self.cells[(row, col)].is_error = False
        self.draw_board()

    def set_cell(self, row, col, num):
        if self.game_ended:
            return
        if num == self.solution[row][col]:
            self.puzzle[row][col] = num
            self.cells[(row, col)].is_error = False
            self.draw_board()
            if self.is_solved():
                self.show_victory()
        else:
            # Ставим цифру, делаем её красной, засчитываем ошибку
            self.puzzle[row][col] = num
            self.cells[(row, col)].is_error = True
            self.add_error()
            self.draw_board()

    def add_error(self):
        if self.game_ended:
            return
        self.errors_made += 1
        self.update_status()
        if self.errors_made >= self.max_errors:
            self.game_over()

    def use_hint(self, *args):
        if self.game_ended or not self.buttons_enabled:
            return
        if self.hints_left <= 0:
            self.show_error("Подсказки закончились")
            return
        empty = [(i, j) for i in range(9) for j in range(9) if self.puzzle[i][j] == 0]
        if not empty:
            self.show_error("Нет пустых клеток")
            return
        r, c = random.choice(empty)
        self.puzzle[r][c] = self.solution[r][c]
        self.cells[(r, c)].is_error = False
        self.hints_left -= 1
        self.update_status()
        self.draw_board()
        if self.is_solved():
            self.show_victory()

    def show_solution(self, *args):
        if self.game_ended:
            return
        for i in range(9):
            for j in range(9):
                self.puzzle[i][j] = self.solution[i][j]
                self.cells[(i, j)].is_error = False
        self.draw_board()
        if self.is_solved():
            self.show_victory()

    def show_error(self, msg):
        self.buttons_enabled = False
        popup = Popup(title='', separator_height=0, overlay_color=(0,0,0,0.5),
                      background='', size_hint=(0.6, 0.3))
        layout = BoxLayout(orientation='vertical', padding=dp(15))
        with layout.canvas.before:
            Color(1,1,1,1)
            layout.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=lambda i,v: setattr(i.rect, 'size', v),
                    pos=lambda i,v: setattr(i.rect, 'pos', v))
        layout.add_widget(Label(text=msg, color=(0.2,0.2,0.2,1)))
        popup.content = layout
        popup.bind(on_dismiss=lambda *_: setattr(self, 'buttons_enabled', True))
        popup.open()

    def show_victory(self):
        self.game_ended = True
        self.buttons_enabled = False
        popup = Popup(title='', separator_height=0, overlay_color=(0,0,0,0.5),
                      background='', size_hint=(0.6, 0.3),
                      auto_dismiss=False)
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15))
        with layout.canvas.before:
            Color(1,1,1,1)
            layout.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=lambda i,v: setattr(i.rect, 'size', v),
                    pos=lambda i,v: setattr(i.rect, 'pos', v))
        layout.add_widget(Label(text="Судоку решено верно!", font_size=dp(16), color=(0.2,0.2,0.2,1)))
        new_btn = Button(text="Новая игра", font_size=dp(16),
                         background_normal='', background_down='',
                         background_color=(0.2,0.6,1,1), color=(1,1,1,1))
        new_btn.bind(on_release=lambda *_: (popup.dismiss(), self.ask_new_game()))
        layout.add_widget(new_btn)
        popup.content = layout
        popup.open()

    def game_over(self):
        self.game_ended = True
        self.buttons_enabled = False
        popup = Popup(
            title='',
            separator_height=0,
            overlay_color=(0, 0, 0, 0.5),
            background='',
            size_hint=(0.6, 0.3),
            auto_dismiss=False
        )
        layout = BoxLayout(orientation='vertical', padding=dp(15))
        with layout.canvas.before:
            Color(1,1,1,1)
            layout.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=lambda i,v: setattr(i.rect, 'size', v),
                    pos=lambda i,v: setattr(i.rect, 'pos', v))
        layout.add_widget(Label(text=f"Вы исчерпали лимит попыток ({self.max_errors}).", color=(0.2,0.2,0.2,1)))
        popup.content = layout
        popup.bind(on_dismiss=lambda *_: self.show_forced_settings())
        popup.open()

    def show_forced_settings(self):
        SettingsDialog(callback=self.new_game, allow_cancel=False).open()

    def ask_new_game(self, *args):
        SettingsDialog(
            callback=self.new_game,
            allow_cancel=True
        ).open()

    # Генератор судоку
    def solve(self, board):
        find = find_empty(board)
        if not find:
            return True
        row, col = find
        for num in random.sample(range(1, 10), 9):
            if self.valid(board, num, (row, col)):
                board[row][col] = num
                if self.solve(board):
                    return True
                board[row][col] = 0
        return False

    def count_solutions(self, board, limit=2):
        find = find_empty(board)
        if not find:
            return 1
        row, col = find
        count = 0
        for num in range(1, 10):
            if self.valid(board, num, (row, col)):
                board[row][col] = num
                count += self.count_solutions(board, limit - count)
                board[row][col] = 0
                if count >= limit:
                    break
        return count

    def valid(self, board, num, pos):
        row, col = pos
        if num in board[row]:
            return False
        if num in [board[i][col] for i in range(9)]:
            return False
        box_x, box_y = col // 3, row // 3
        for i in range(box_y * 3, box_y * 3 + 3):
            for j in range(box_x * 3, box_x * 3 + 3):
                if board[i][j] == num:
                    return False
        return True

    def generate_puzzle(self, difficulty):
        full_board = [[0]*9 for _ in range(9)]
        self.solve(full_board)
        puzzle = [row[:] for row in full_board]
        cells = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(cells)
        removed = 0
        for (i, j) in cells:
            if removed >= difficulty:
                break
            backup = puzzle[i][j]
            puzzle[i][j] = 0
            if self.count_solutions([row[:] for row in puzzle], limit=2) == 1:
                removed += 1
            else:
                puzzle[i][j] = backup
        return puzzle, full_board

    def is_solved(self):
        for i in range(9):
            for j in range(9):
                if self.puzzle[i][j] != self.solution[i][j]:
                    return False
        return True

def find_empty(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return (i, j)
    return None

class SudokuApp(App):
    def build(self):
        Window.clearcolor = (0.85, 0.85, 0.85, 1) # светлый серый фон
        Window.set_title('Судоку')
        return SudokuGrid()

if __name__ == '__main__':
    SudokuApp().run()