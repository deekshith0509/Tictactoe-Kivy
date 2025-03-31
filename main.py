from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.utils import platform
from datetime import datetime
import random
from kivy.graphics.vertex_instructions import RoundedRectangle


class GameData:
    def __init__(self):
        if platform == 'android':
            from android.storage import app_storage_path
            json_path = app_storage_path() + '/game_data.json'
        else:
            json_path = 'game_data.json'
        self.store = JsonStore(json_path)
        self.stats = self.store.get('stats') if self.store.exists('stats') else {'total_time': 0, 'games': 0, 'x_wins': 0, 'o_wins': 0, 'draws': 0}
        self.ratings = self.store.get('ratings') if self.store.exists('ratings') else {'easy': 1200, 'medium': 1200, 'hard': 1200}
    def save(self): self.store.put('stats', **self.stats); self.store.put('ratings', **self.ratings)
    def update_time(self, elapsed): self.stats['total_time'] += elapsed; self.save()
    def update_game(self, result):
        self.stats['games'] += 1
        if result in ['X', 'O']: self.stats[f'{result.lower()}_wins'] += 1
        else: self.stats['draws'] += 1
        self.save()

class AIEngine:
    def __init__(self, difficulty='medium'):
        self.depths = {'easy': 2, 'medium': 4, 'hard': 6}
        self.depth = self.depths[difficulty]
    def get_move(self, board):
        empty = [i for i, x in enumerate(board) if not x]
        if not empty: return None
        best_score, best_move, alpha, beta = float('-inf'), empty[0], float('-inf'), float('inf')
        for pos in empty:
            board[pos] = 'O'
            score = self.minimax(board, self.depth, False, alpha, beta)
            board[pos] = ''
            if score > best_score:
                best_score, best_move = score, pos
            alpha = max(alpha, best_score)
            if beta <= alpha: break
        return best_move
    def minimax(self, board, depth, is_max, alpha, beta):
        winner = self.check_winner(board)
        if winner: return 100 if winner == 'O' else -100
        if depth == 0 or '' not in board: return self.evaluate_board(board)
        empty = [i for i, x in enumerate(board) if not x]
        if not empty: return 0
        if is_max:
            max_score = float('-inf')
            for pos in empty:
                board[pos] = 'O'
                score = self.minimax(board, depth - 1, False, alpha, beta)
                board[pos] = ''
                max_score = max(max_score, score)
                alpha = max(alpha, max_score)
                if beta <= alpha: break
            return max_score
        else:
            min_score = float('inf')
            for pos in empty:
                board[pos] = 'X'
                score = self.minimax(board, depth - 1, True, alpha, beta)
                board[pos] = ''
                min_score = min(min_score, score)
                beta = min(beta, min_score)
                if beta <= alpha: break
            return min_score
    def evaluate_board(self, board):
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        score = 0
        for w in wins:
            line = [board[i] for i in w]
            if line.count('O') == 2 and line.count('') == 1: score += 5
            elif line.count('X') == 2 and line.count('') == 1: score -= 5
            elif line.count('O') == 3: score += 100
            elif line.count('X') == 3: score -= 100
        return score
    def check_winner(self, board):
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for i, j, k in wins:
            if board[i] and board[i] == board[j] == board[k]: return board[i]
        return None

class StyledButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.color = (0.1, 0.1, 0.1, 1)
        self.font_size = dp(18)

    def on_size(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.93, 0.93, 0.93, 1)  # Light gray background
            Rectangle(pos=self.pos, size=self.size)
            Color(0, 0, 0, 1)  # Black border
            Line(rectangle=(self.x, self.y, self.width, self.height), width=1.5)

            # Professional gradient effect
            Color(0.2, 0.4, 0.6, 0.2)  # Subtle blue tint
            Rectangle(pos=(self.x, self.y), size=(self.width, self.height/2))



class GameButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.mark = ''
        self.bind(size=self.enforce_square)  # Ensure square size

    def enforce_square(self, *args):
        """Ensure the button remains a perfect square."""
        min_side = min(self.size)  # Take the smallest dimension
        self.size = (min_side, min_side)  # Force square shape

    def on_size(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)  # Light gray background
            Rectangle(pos=self.pos, size=self.size)
            Color(0, 0, 0, 1)  # Black border
            Line(rectangle=(self.x, self.y, self.width, self.height), width=2)

    def set_mark(self, mark):
        self.mark = mark
        self.canvas.after.clear()
        if mark == 'X':
            with self.canvas.after:
                Color(0.8, 0.2, 0.2, 1)  # Professional red
                Line(points=[self.x + dp(10), self.y + dp(10),
                            self.x + self.width - dp(10), self.y + self.height - dp(10)],
                    width=dp(3))
                Line(points=[self.x + self.width - dp(10), self.y + dp(10),
                            self.x + dp(10), self.y + self.height - dp(10)],
                    width=dp(3))
        elif mark == 'O':
            with self.canvas.after:
                Color(0.2, 0.4, 0.8, 1)  # Professional blue
                Line(ellipse=(self.x + dp(10), self.y + dp(10),
                            self.width - dp(20), self.height - dp(20)),
                    width=dp(3))



class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

        title_layout = BoxLayout(size_hint_y=0.2)
        title = Label(text="Tic Tac Toe", font_size=dp(40), color=(0.1, 0.3, 0.5, 1))
        title_layout.add_widget(title)

        layout.add_widget(title_layout)

        buttons_layout = BoxLayout(orientation='vertical', spacing=dp(20), size_hint_y=0.5)

        # Create professional buttons
        single_btn = StyledButton(text="Single Player", size_hint=(0.7, 0.4))
        multi_btn = StyledButton(text="Two Players", size_hint=(0.7, 0.4))
        stats_btn = StyledButton(text="Statistics", size_hint=(0.7, 0.4))
        logs_btn = StyledButton(text="Game Logs", size_hint=(0.7, 0.4))

        single_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'difficulty'))
        multi_btn.bind(on_release=lambda x: self.start_game('medium', False))
        stats_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'stats'))
        logs_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'logs'))

        for btn in [single_btn, multi_btn, stats_btn, logs_btn]:
            btn_layout = BoxLayout()
            btn_layout.add_widget(BoxLayout(size_hint_x=0.15))
            btn_layout.add_widget(btn)
            btn_layout.add_widget(BoxLayout(size_hint_x=0.15))
            buttons_layout.add_widget(btn_layout)

        layout.add_widget(buttons_layout)
        layout.add_widget(BoxLayout(size_hint_y=0.3))

        with self.canvas.before:
            Color(0.97, 0.97, 0.97, 1)  # Professional white background
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def start_game(self, difficulty, is_ai):
        game_screen = self.manager.get_screen('game')
        game_screen.setup_game(difficulty, is_ai)
        self.manager.current = 'game'

class DifficultyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

        header = BoxLayout(size_hint_y=0.15)
        back_btn = Button(text="back", size_hint=(0.15, 1), background_normal='',
                         font_size=dp(30), color=(0,0,0))
        with back_btn.canvas.before:
            Color(0.1, 0.3, 0.5, 1)  # Professional blue
            Rectangle(pos=back_btn.pos, size=back_btn.size)
            Color(0, 0, 0, 1)  # Black border
            Line(rectangle=(back_btn.pos[0], back_btn.pos[1], back_btn.width, back_btn.height), width=1)
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        back_btn.bind(pos=self._update_back_btn, size=self._update_back_btn)
        header.add_widget(back_btn)
        header.add_widget(Label(text="Select Difficulty", font_size=dp(28), color=(0.1, 0.3, 0.5, 1)))
        header.add_widget(BoxLayout(size_hint_x=0.15))

        layout.add_widget(header)
        layout.add_widget(BoxLayout(size_hint_y=0.1))

        buttons_layout = BoxLayout(orientation='vertical', spacing=dp(20), size_hint_y=0.6)

        for diff, color in [('easy', (0.1, 0.6, 0.3, 1)), ('medium', (0.7, 0.5, 0.1, 1)), ('hard', (0.7, 0.1, 0.1, 1))]:
            btn = Button(text=diff.title(), size_hint=(0.7, 0.33),
                         background_normal='', font_size=dp(24), color=(0,0,0))
            with btn.canvas.before:
                Color(*color)
                Rectangle(pos=btn.pos, size=btn.size)
                Color(0, 0, 0, 1)  # Black border
                Line(rectangle=(btn.pos[0], btn.pos[1], btn.width, btn.height), width=1)
            btn.bind(on_release=lambda x, d=diff: self.start_game(d))
            btn.bind(pos=lambda instance, value, b=btn, c=color: self._update_btn(b, c),
                   size=lambda instance, value, b=btn, c=color: self._update_btn(b, c))

            btn_layout = BoxLayout()
            btn_layout.add_widget(BoxLayout(size_hint_x=0.15))
            btn_layout.add_widget(btn)
            btn_layout.add_widget(BoxLayout(size_hint_x=0.15))
            buttons_layout.add_widget(btn_layout)

        layout.add_widget(buttons_layout)
        layout.add_widget(BoxLayout(size_hint_y=0.15))

        with self.canvas.before:
            Color(0.97, 0.97, 0.97, 1)  # Professional white background
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _update_back_btn(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.1, 0.3, 0.5, 1)  # Professional blue
            Rectangle(pos=instance.pos, size=instance.size)
            Color(0, 0, 0, 1)  # Black border
            Line(rectangle=(instance.x, instance.y, instance.width, instance.height), width=1)

    def _update_btn(self, btn, color):
        btn.canvas.before.clear()
        with btn.canvas.before:
            Color(*color)
            Rectangle(pos=btn.pos, size=btn.size)
            Color(0, 0, 0, 1)  # Black border
            Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=1)

    def start_game(self, difficulty):
        game_screen = self.manager.get_screen('game')
        game_screen.setup_game(difficulty, True)
        self.manager.current = 'game'

class GameScreen(Screen):
    current_player = StringProperty('X')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_data = GameData()
        self.start_time = None
        self.setup_ui()
    def _adjust_board_size(self, instance, value):
        """Force the board to remain a square and center it."""
        size = min(instance.width, instance.height) * 0.8  # 80% of the smaller dimension
        instance.children[0].size = (size, size)  # Update board_container size

    def setup_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        header = BoxLayout(size_hint_y=0.15)
        back_btn = Button(
            text="Back",
            size_hint=(None, None),  # Allow manual size control
            font_size=dp(30),
            color=(0, 0, 0),
            background_normal='',
            padding=(dp(10), dp(10)),  # Padding for spacing
            pos_hint={'x': 0, 'top': 1}  # Fixed to top-left corner
        )
        with back_btn.canvas.before:
            Color(0.1, 0.3, 0.5, 1)  # Professional blue
            Rectangle(pos=back_btn.pos, size=back_btn.size)
            Color(0, 0, 0, 1)  # Black border
            Line(rectangle=(back_btn.pos[0], back_btn.pos[1], back_btn.width, back_btn.height), width=1)
        back_btn.bind(on_release=self.go_back)
        back_btn.bind(pos=self._update_back_btn, size=self._update_back_btn)
        header.add_widget(back_btn)

        self.status_label = Label(text='', font_size=dp(22), color=(0.1, 0.3, 0.5, 1))
        header.add_widget(self.status_label)
        header.add_widget(BoxLayout(size_hint_x=0.15))

        layout.add_widget(header)

        # Centering the board and forcing square shape
        board_container = BoxLayout(size_hint=(None, None), size=(dp(300), dp(300)), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.board = GridLayout(cols=3, rows=3, spacing=0, size_hint=(1, 1))  # No spacing for joined blocks

        self.buttons = [GameButton() for _ in range(9)]
        for i, btn in enumerate(self.buttons):
            btn.bind(on_release=lambda x, idx=i: self.make_move(idx))
            self.board.add_widget(btn)

        board_container.add_widget(self.board)
        layout.add_widget(board_container)

        # Bind size to ensure it's a square
        layout.bind(size=self._adjust_board_size)


        with self.canvas.before:
            Color(0.97, 0.97, 0.97, 1)  # Professional white background
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _update_back_btn(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.1, 0.3, 0.5, 1)  # Professional blue
            Rectangle(pos=instance.pos, size=instance.size)
            Color(0, 0, 0, 1)  # Black border
            Line(rectangle=(instance.x, instance.y, instance.width, instance.height), width=1)

    def setup_game(self, difficulty, is_ai):
        self.difficulty = difficulty
        self.is_ai = is_ai
        self.ai = AIEngine(difficulty) if is_ai else None
        self.reset_game()
        self.start_time = datetime.now()

        # Update game logs
        log_screen = self.manager.get_screen('logs')
        mode = f"AI ({difficulty})" if is_ai else "Two Players"
        log_screen.add_log(f"Started new game: {mode}")

    def make_move(self, idx):
        if self.game_over or self.buttons[idx].mark: return
        self.buttons[idx].set_mark(self.current_player)
        if self.check_game_state():
            if self.is_ai and self.current_player == 'O' and not self.game_over:
                Clock.schedule_once(lambda dt: self.make_ai_move(), 0.5)

    def make_ai_move(self):
        board = [btn.mark for btn in self.buttons]
        move = self.ai.get_move(board)
        if move is not None:
            self.buttons[move].set_mark('O')
            self.check_game_state()

    def check_game_state(self):
        board = [btn.mark for btn in self.buttons]
        winner = self.check_winner(board)
        if winner:
            self.handle_game_end(winner)
            return False
        elif '' not in board:
            self.handle_game_end('draw')
            return False
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        self.status_label.text = f"{'Your' if self.current_player == 'X' else 'AI' if self.is_ai else 'Player O'}'s Turn"
        return True

    def handle_game_end(self, result):
        self.game_over = True
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self.game_data.update_time(elapsed)
        self.game_data.update_game(result)

        if result == 'draw':
            msg = "It's a Draw!"
            log_msg = "Game ended in a draw"
        elif result == 'X':
            msg = "You Won!"
            log_msg = "Player X won the game"
        elif result == 'O':
            msg = "AI Wins!" if self.is_ai else "Player O Wins!"
            log_msg = f"{'AI' if self.is_ai else 'Player O'} won the game"

        # Update game logs
        log_screen = self.manager.get_screen('logs')
        log_screen.add_log(log_msg)

        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text=msg, font_size=dp(24)))
        btn = Button(text="PLAY AGAIN", size_hint=(0.5, None), height=dp(50),
                    background_normal='', color=(0,0,0))
        with btn.canvas.before:
            Color(0.1, 0.3, 0.5, 1)  # Professional blue
            Rectangle(pos=btn.pos, size=btn.size)
            Color(0, 0, 0, 1)  # Black border
            Line(rectangle=(btn.pos[0], btn.pos[1], btn.width, btn.height), width=1)
        btn.bind(pos=self._update_popup_btn, size=self._update_popup_btn)

        btn_layout = BoxLayout()
        btn_layout.add_widget(BoxLayout())
        btn_layout.add_widget(btn)
        btn_layout.add_widget(BoxLayout())
        content.add_widget(btn_layout)

        popup = Popup(title="Game Over", content=content, size_hint=(0.8, 0.4),
                     title_color=(0.1, 0.3, 0.5, 1), title_size=dp(20))
        btn.bind(on_release=lambda x: self.handle_replay(popup))
        popup.open()

    def _update_popup_btn(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.1, 0.3, 0.5, 1)  # Professional blue
            Rectangle(pos=instance.pos, size=instance.size)
            Color(0, 0, 0, 1)  # Black border
            Line(rectangle=(instance.x, instance.y, instance.width, instance.height), width=1)

    def handle_replay(self, popup):
        popup.dismiss()
        self.reset_game()

        # Update game logs
        log_screen = self.manager.get_screen('logs')
        mode = f"AI ({self.difficulty})" if self.is_ai else "Two Players"
        log_screen.add_log(f"Started new game: {mode}")

    def reset_game(self):
        self.game_over = False
        self.current_player = 'X'
        for btn in self.buttons:
            btn.mark = ''
            btn.canvas.after.clear()
        self.status_label.text = "Your Turn"
        self.start_time = datetime.now()

    def check_winner(self, board):
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for i, j, k in wins:
            if board[i] and board[i] == board[j] == board[k]:
                return board[i]
        return None

    def go_back(self, *args):
        if self.start_time:
            self.game_data.update_time((datetime.now() - self.start_time).total_seconds())
        self.manager.current = 'home'

class StatsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20))

        header = BoxLayout(size_hint_y=0.15)
        back_btn = Button(text="←", size_hint=(0.15, 1), background_normal='',
                         font_size=dp(30), color=(1, 1, 1, 1))
        with back_btn.canvas.before:
            Color(0.1, 0.3, 0.5, 1)  # Professional blue
            Rectangle(pos=back_btn.pos, size=back_btn.size)
            Color(0, 0, 0, 1)  # Black border
            Line(rectangle=(back_btn.pos[0], back_btn.pos[1], back_btn.width, back_btn.height), width=1)
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        back_btn.bind(pos=self._update_back_btn, size=self._update_back_btn)
        header.add_widget(back_btn)
        header.add_widget(Label(text="Statistics", font_size=dp(28), color=(0.1, 0.3, 0.5, 1)))
        header.add_widget(BoxLayout(size_hint_x=0.15))

        layout.add_widget(header)

        stats_container = BoxLayout(padding=dp(10))
        self.stats_layout = GridLayout(cols=2, spacing=dp(10), padding=dp(20))
        stats_container.add_widget(self.stats_layout)
        layout.add_widget(stats_container)

        with self.canvas.before:
            Color(0.97, 0.97, 0.97, 1)  # Professional white background
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _update_back_btn(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.1, 0.3, 0.5, 1)  # Professional blue
            Rectangle(pos=instance.pos, size=instance.size)
            Color(0, 0, 0, 1)  # Black border
            Line(rectangle=(instance.x, instance.y, instance.width, instance.height), width=1)

    def on_enter(self):
        self.stats_layout.clear_widgets()
        game_data = GameData()
        stats = game_data.stats
        hours = stats['total_time'] // 3600
        minutes = (stats['total_time'] % 3600) // 60

        stat_items = [
            ("Total Time", f"{int(hours)}h {int(minutes)}m"),
            ("Games Played", str(stats['games'])),
            ("X Wins", str(stats['x_wins'])),
            ("O Wins", str(stats['o_wins'])),
            ("Draws", str(stats['draws'])),
            ("Easy Rating", str(int(game_data.ratings['easy']))),
            ("Medium Rating", str(int(game_data.ratings['medium']))),
            ("Hard Rating", str(int(game_data.ratings['hard'])))
        ]

        for key, value in stat_items:
            label1 = Label(text=key, font_size=dp(18), color=(0.1, 0.1, 0.1, 1), halign='right')
            label2 = Label(text=value, font_size=dp(18), color=(0.1, 0.3, 0.5, 1), halign='left')
            self.stats_layout.add_widget(label1)
            self.stats_layout.add_widget(label2)




class LogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20))

        header = BoxLayout(size_hint_y=0.15)
        back_btn = Button(text="back", size_hint=(0.15, 1), background_color=(0,0,0),
                         font_size=dp(30), background_normal='')
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        header.add_widget(back_btn)
        header.add_widget(Label(text="Game Logs", font_size=dp(28), color=(0.2, 0.6, 0.8, 1)))
        header.add_widget(BoxLayout(size_hint_x=0.15))

        layout.add_widget(header)

        self.log_label = Label(text="Game Logs\n", font_size=dp(16), color=(0.2, 0.2, 0.2, 1), halign='left', valign='top')
        self.log_label.bind(size=self.log_label.setter('text_size'))
        scroll_layout = BoxLayout(padding=dp(10))
        scroll_layout.add_widget(self.log_label)
        layout.add_widget(scroll_layout)

        with self.canvas.before:
            Color(0.95, 0.95, 0.98, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def add_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_label.text += f"[{timestamp}] {message}\n"

class TicTacToeApp(App):
    def build(self):
        sm = ScreenManager()
        screens = [
            HomeScreen(name='home'),
            DifficultyScreen(name='difficulty'),
            GameScreen(name='game'),
            StatsScreen(name='stats'),
            LogScreen(name='logs')
        ]
        for screen in screens:
            sm.add_widget(screen)
        return sm

    def on_start(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE,
                               Permission.READ_MEDIA_IMAGES, Permission.READ_MEDIA_VIDEO, Permission.READ_MEDIA_AUDIO])

if __name__ == '__main__':
    TicTacToeApp().run()
