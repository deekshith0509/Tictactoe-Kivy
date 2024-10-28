from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.behaviors import RoundedRectangularElevationBehavior
from kivymd.uix.textfield import MDTextField
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.animation import Animation
from datetime import datetime
import random, math, numpy as np
from kivy.utils import platform

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
        if not empty:
            return None
        
        best_score = float('-inf')
        best_move = empty[0]
        alpha = float('-inf')
        beta = float('inf')
        
        for pos in empty:
            board[pos] = 'O'
            score = self.minimax(board, self.depth, False, alpha, beta)
            board[pos] = ''
            if score > best_score:
                best_score = score
                best_move = pos
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_move

    def minimax(self, board, depth, is_max, alpha, beta):
        winner = self.check_winner(board)
        if winner:
            return 100 if winner == 'O' else -100
        
        if depth == 0 or '' not in board:
            return self.evaluate_board(board)
        
        empty = [i for i, x in enumerate(board) if not x]
        if not empty:
            return 0
            
        if is_max:
            max_score = float('-inf')
            for pos in empty:
                board[pos] = 'O'
                score = self.minimax(board, depth - 1, False, alpha, beta)
                board[pos] = ''
                max_score = max(max_score, score)
                alpha = max(alpha, max_score)
                if beta <= alpha:
                    break
            return max_score
        else:
            min_score = float('inf')
            for pos in empty:
                board[pos] = 'X'
                score = self.minimax(board, depth - 1, True, alpha, beta)
                board[pos] = ''
                min_score = min(min_score, score)
                beta = min(beta, min_score)
                if beta <= alpha:
                    break
            return min_score

    def evaluate_board(self, board):
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        score = 0
        for w in wins:
            line = [board[i] for i in w]
            if line.count('O') == 2 and line.count('') == 1:
                score += 5
            elif line.count('X') == 2 and line.count('') == 1:
                score -= 5
            elif line.count('O') == 3:
                score += 100
            elif line.count('X') == 3:
                score -= 100
        return score

    def check_winner(self, board):
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for i, j, k in wins:
            if board[i] and board[i] == board[j] == board[k]:
                return board[i]
        return None
        
        
class GameButton(MDRaisedButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = dp(24)
        self.size_hint = (1, 1)
        self.elevation = 3
        self.md_bg_color = [0.95, 0.95, 0.95, 1]
class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))
        header = MDBoxLayout(size_hint_y=0.1)
        logs_btn = MDIconButton(icon="text-box-outline", pos_hint={'center_y': 0.5})
        stats_btn = MDIconButton(icon="trophy-outline", pos_hint={'center_y': 0.5})
        logs_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'logs'))
        stats_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'stats'))
        header.add_widget(logs_btn)
        header.add_widget(MDLabel(text="Tic Tac Toe", halign='center', font_style='H5'))
        header.add_widget(stats_btn)
        layout.add_widget(header)
        modes = [('single', 'Single Player'), ('multi', 'Two Players')]
        for mode, text in modes:
            btn = MDRaisedButton(text=text, size_hint=(None, None), size=(dp(200), dp(50)), pos_hint={'center_x': 0.5})
            btn.bind(on_release=lambda x, m=mode: self.select_mode(m))
            layout.add_widget(btn)
        self.add_widget(layout)
    def select_mode(self, mode):
        if mode == 'single': self.manager.current = 'difficulty'
        else: self.start_game('medium', False)
    def start_game(self, difficulty, is_ai):
        game_screen = self.manager.get_screen('game')
        game_screen.setup_game(difficulty, is_ai)
        self.manager.current = 'game'
class DifficultyScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))
        back_btn = MDIconButton(icon="arrow-left", pos_hint={'center_x': 0.1})
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        layout.add_widget(back_btn)
        layout.add_widget(MDLabel(text="Select Difficulty", halign='center', font_style='H5'))
        for diff in ['easy', 'medium', 'hard']:
            btn = MDRaisedButton(text=diff.title(), size_hint=(None, None), size=(dp(200), dp(50)), pos_hint={'center_x': 0.5})
            btn.bind(on_release=lambda x, d=diff: self.start_game(d))
            layout.add_widget(btn)
        self.add_widget(layout)
    def start_game(self, difficulty):
        game_screen = self.manager.get_screen('game')
        game_screen.setup_game(difficulty, True)
        self.manager.current = 'game'
class GameScreen(MDScreen):
    current_player = StringProperty('X')
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_data = GameData()
        self.start_time = None
        self.setup_ui()
    def setup_ui(self):
        layout = MDBoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))
        header = MDBoxLayout(size_hint_y=0.1)
        back_btn = MDIconButton(icon="arrow-left")
        back_btn.bind(on_release=self.go_back)
        header.add_widget(back_btn)
        self.status_label = MDLabel(text='', halign='center')
        header.add_widget(self.status_label)
        layout.add_widget(header)
        self.board = MDGridLayout(cols=3, spacing=dp(8))
        self.buttons = [GameButton(text='') for _ in range(9)]
        for btn in self.buttons: 
            btn.bind(on_release=self.make_move)
            self.board.add_widget(btn)
        layout.add_widget(self.board)
        self.add_widget(layout)
    def setup_game(self, difficulty, is_ai):
        self.difficulty = difficulty
        self.is_ai = is_ai
        self.ai = AIEngine(difficulty) if is_ai else None
        self.reset_game()
        self.start_time = datetime.now()
    def make_move(self, button):
        if button.text or self.game_over: return
        button.text = self.current_player
        self.animate_button(button)
        if self.check_game_state():
            if self.is_ai and not self.game_over:
                Clock.schedule_once(lambda dt: self.make_ai_move(), 0.5)
    def make_ai_move(self):
        board = [btn.text for btn in self.buttons]
        move = self.ai.get_move(board)
        if move is not None:
            self.buttons[move].text = 'O'
            self.animate_button(self.buttons[move])
            self.check_game_state()
    def animate_button(self, button):
        anim = Animation(md_bg_color=[0.9, 0.7, 0.7, 1] if button.text == 'X' else [0.7, 0.7, 0.9, 1], duration=0.2)
        anim.start(button)
    def check_game_state(self):
        board = [btn.text for btn in self.buttons]
        winner = self.ai.check_winner(board) if self.is_ai else self.check_winner(board)
        if winner or '' not in board:
            self.handle_game_end(winner if winner else 'draw')
            return False
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        self.status_label.text = f"{'Your' if self.current_player == 'X' else 'AI' if self.is_ai else 'Player O'}'s Turn"
        return True

    def check_game_state(self):
        board = [btn.text for btn in self.buttons]
        winner = self.check_winner(board)  # Check for a winner

        # Check for draw condition before changing players
        if winner or '' not in board:  # If there's a winner or no empty spots
            self.handle_game_end(winner if winner else 'draw')  # Call end game with winner or draw
            return False  # Game is over

        # Switch players only if the game is not over
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        self.status_label.text = f"{'Your' if self.current_player == 'X' else 'AI' if self.is_ai else 'Player O'}'s Turn"
        return True

    def handle_game_end(self, result):
        self.game_over = True
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self.game_data.update_time(elapsed)
        self.game_data.update_game(result)

        # Display appropriate message based on the result
        if result == 'draw':
            msg = "It's a Draw!"
        elif result == 'X':
            msg = "You Won!"
        elif result == 'O':
            msg = "AI Wins!" if self.is_ai else "Player O Wins!"
        
        dialog = MDDialog(
            title="Game Over",
            text=msg,
            buttons=[MDFlatButton(text="PLAY AGAIN", on_release=lambda x: self.handle_replay(dialog))]
        )
        dialog.open()

    def handle_replay(self, dialog):
        dialog.dismiss()
        self.reset_game()
    def reset_game(self):
        self.game_over = False
        self.current_player = 'X'
        for btn in self.buttons:
            btn.text = ''
            btn.md_bg_color = [0.95, 0.95, 0.95, 1]
        self.status_label.text = "Your Turn"
        self.start_time = datetime.now()
    def check_winner(self, board):
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for i, j, k in wins:
            if board[i] and board[i] == board[j] == board[k]: return board[i]
        return None
    def go_back(self, *args):
        if self.start_time:
            self.game_data.update_time((datetime.now() - self.start_time).total_seconds())
        self.manager.current = 'home'
class StatsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical', padding=dp(16))
        back_btn = MDIconButton(icon="arrow-left")
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        layout.add_widget(back_btn)
        self.stats_label = MDLabel(halign='center')
        layout.add_widget(self.stats_label)
        self.add_widget(layout)
    def on_enter(self):
        game_data = GameData()
        stats = game_data.stats
        hours = stats['total_time'] // 3600
        minutes = (stats['total_time'] % 3600) // 60
        self.stats_label.text = f"""
Total Time: {int(hours)}h {int(minutes)}m
Games Played: {stats['games']}
X Wins: {stats['x_wins']}
O Wins: {stats['o_wins']}
Draws: {stats['draws']}
Ratings:
Easy: {int(game_data.ratings['easy'])}
Medium: {int(game_data.ratings['medium'])}
Hard: {int(game_data.ratings['hard'])}
"""
class LogScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical', padding=dp(16))
        back_btn = MDIconButton(icon="arrow-left")
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        layout.add_widget(back_btn)
        self.log_label = MDLabel(text="Game Logs\n", halign='left')
        layout.add_widget(self.log_label)
        self.add_widget(layout)
    def add_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_label.text += f"[{timestamp}] {message}\n"


class TicTacToeApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        sm = MDScreenManager()
        
        # Add all screens to the screen manager
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
            from android.permissions import request_permissions, Permission, check_permission
            from android.storage import primary_external_storage_path
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE,Permission.READ_MEDIA_IMAGES,Permission.READ_MEDIA_VIDEO,Permission.READ_MEDIA_AUDIO])

if __name__ == '__main__':
    TicTacToeApp().run()