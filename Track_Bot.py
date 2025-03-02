from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.graphics import Line, Color, Ellipse, RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window
import math

class DrawingWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path_points = []
        self.bot = None
        self.bot_index = 0
        self.bot_speed = 3
        self.moving = False
        self.paused = False
        self.distance_label = None  

        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def calculate_distance(self):
        if len(self.path_points) < 2:
            return
        distance_px = sum(
            math.dist(self.path_points[i], self.path_points[i - 1])
            for i in range(1, len(self.path_points))
        )
        distance_cm = distance_px * 0.1  
        distance_m = distance_cm / 100  
        if self.distance_label:
            self.distance_label.text = f"Distance: {distance_cm:.2f} cm = {distance_m:.2f} m"

    def on_touch_down(self, touch):
        if not self.moving and self.collide_point(*touch.pos):
            self.path_points = [(touch.x, touch.y)]
            with self.canvas:
                Color(0.0, 0.6, 1, 1)  
                touch.ud["line"] = Line(points=[touch.x, touch.y], width=2, joint="round")

    def on_touch_move(self, touch):
        if not self.moving and self.collide_point(*touch.pos) and "line" in touch.ud:
            touch.ud["line"].points += [touch.x, touch.y]
            self.path_points.append((touch.x, touch.y))
            self.calculate_distance()

    def clear_canvas(self, *_):
        self.canvas.clear()
        self.path_points = []
        self.bot = None
        self.bot_index = 0
        self.moving = False
        self.paused = False
        Clock.unschedule(self.move_bot)
        if self.distance_label:
            self.distance_label.text = "Distance: 0.00 cm = 0.00 m"
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])

    def create_bot(self, *_):
        if self.path_points:
            x, y = self.path_points[0]
            with self.canvas:
                Color(0.0, 1, 1, 1)  
                self.bot = Ellipse(pos=(x - 10, y - 10), size=(20, 20))
            self.bot_index = 0
            self.moving = False

    def move_bot(self, dt):
        if self.bot and self.bot_index < len(self.path_points) - 1:
            if not self.paused:
                x1, y1 = self.bot.pos[0] + 10, self.bot.pos[1] + 10
                x2, y2 = self.path_points[self.bot_index + 1]
                dx, dy = x2 - x1, y2 - y1
                distance = math.dist((x1, y1), (x2, y2))

                if distance < self.bot_speed:
                    self.bot_index += 1
                else:
                    ratio = self.bot_speed / distance
                    new_x = x1 + dx * ratio
                    new_y = y1 + dy * ratio
                    self.bot.pos = (new_x - 10, new_y - 10)
        else:
            Clock.unschedule(self.move_bot)

    def start_moving(self, _):
        if not self.moving and self.bot:
            self.moving = True
            self.paused = False
            Clock.schedule_interval(self.move_bot, 0.02)

    def pause_resume_moving(self, _):
        if self.moving:
            self.paused = not self.paused

    def update_speed(self, _, value):
        self.bot_speed = int(value)

class TrackBotApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)  
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.drawing_area = DrawingWidget(size_hint=(1, 0.75))  

        control_layout = BoxLayout(size_hint=(1, 0.25), orientation="vertical", spacing=10, padding=(10, 5))

        # Speed Slider
        speed_layout = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        speed_label = Label(text="Speed:", size_hint=(None, None), size=(80, 50), color=(1, 1, 1, 1))
        speed_slider = Slider(min=1, max=10, value=3, size_hint=(1, None), height=50)
        speed_slider.bind(value=self.drawing_area.update_speed)
        speed_layout.add_widget(speed_label)
        speed_layout.add_widget(speed_slider)

        # Distance Label
        distance_layout = BoxLayout(size_hint=(1, None), height=40)
        self.drawing_area.distance_label = Label(
            text="Distance: 0.00 cm = 0.00 m",
            color=(1, 1, 1, 1)
        )
        distance_layout.add_widget(self.drawing_area.distance_label)

        # Toolbar (Buttons)
        toolbar = GridLayout(cols=4, size_hint=(1, None), height=50, spacing=10)
        button_size = (1, 1)  

        clear_button = Button(text="Clear", size_hint=button_size, background_color=(0.8, 0.2, 0.2, 1))
        send_button = Button(text="Create", size_hint=button_size, background_color=(0.2, 0.9, 0.2, 1))
        start_button = Button(text="Start", size_hint=button_size, background_color=(1, 0.8, 0.0, 1))
        pause_button = Button(text="P/R", size_hint=button_size, background_color=(0.6, 0.3, 1, 1))

        clear_button.bind(on_press=self.drawing_area.clear_canvas)
        send_button.bind(on_press=self.drawing_area.create_bot)
        start_button.bind(on_press=self.drawing_area.start_moving)
        pause_button.bind(on_press=self.drawing_area.pause_resume_moving)

        toolbar.add_widget(clear_button)
        toolbar.add_widget(send_button)
        toolbar.add_widget(start_button)
        toolbar.add_widget(pause_button)

        # Adding all sections to control layout
        control_layout.add_widget(speed_layout)
        control_layout.add_widget(distance_layout)
        control_layout.add_widget(toolbar)

        layout.add_widget(self.drawing_area)
        layout.add_widget(control_layout)

        return layout

if __name__ == "__main__":
    TrackBotApp().run()
