# -*- coding: utf-8 -*-
# main.py

import os
from datetime import datetime
# --- שינוי: ייבוא ספריות נדרשות ---
import pyminizip
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.window import Window
from kivy.utils import get_color_from_hex, platform
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import BooleanProperty, NumericProperty, StringProperty

# --- בדיקת פלטפורמה (חשוב לשמירת קבצים באנדרואיד) ---
if platform == 'android':
    from android.storage import primary_external_storage_path
    DOWNLOADS_DIR = os.path.join(primary_external_storage_path(), 'Download')
else:
    # למקרה שמריצים על מחשב, ישמור בתיקיית המשתמש
    DOWNLOADS_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')

import arabic_reshaper
from bidi.algorithm import get_display

# =============================================================================
# 1. הגדרות ופונקציות עזר
# =============================================================================

FONT_NAME = 'Heebo-Regular.ttf'
ZIP_PASSWORD = "0544596776"

colors = {
    "background": get_color_from_hex("#F5F7FA"),
    "card": get_color_from_hex("#FFFFFF"),
    "primary": get_color_from_hex("#4A90E2"),
    "text_dark": get_color_from_hex("#333333"),
    "text_light": get_color_from_hex("#FFFFFF"),
    "button_normal": get_color_from_hex("#E0E0E0"),
    "button_na": get_color_from_hex("#A0A0A0"),
}
Window.clearcolor = colors["background"]

def fix_hebrew(text):
    if not text: return ""
    return get_display(arabic_reshaper.reshape(text))

WELCOME_SCREEN = 'welcome'
RESULTS_SCREEN = 'results'
EXPORT_SCREEN = 'export'
PRE_Q12_SCREEN = 'pre_question_12'
def get_q_screen_name(index):
    return f'question_{index}'

# =============================================================================
# 2. ווידג'טים מעוצבים בהתאמה אישית
# =============================================================================

class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(rgba=colors["card"])
            self.rect = RoundedRectangle(radius=[15])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class StyledButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = colors["primary"]
        self.color = colors["text_light"]
        self.font_name = FONT_NAME
        self.font_size = '20sp'

class StyledToggleButton(ToggleButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = colors["button_normal"]
        self.background_down = ''
        self.color = colors["text_dark"]
        self.font_name = FONT_NAME
        self.font_size = '18sp'
        self.bind(state=self.on_state_change)

    def on_state_change(self, instance, value):
        if value == 'down':
            self.background_color = colors["primary"]
            self.color = colors["text_light"]
        else:
            self.background_color = colors["button_normal"]
            self.color = colors["text_dark"]

# =============================================================================
# 3. תוכן השאלון
# =============================================================================

QUESTIONS = [
    "במהלך השבוע האחרון, האם חשת בעיניים רגישות לאור?",
    "במהלך השבוע האחרון, האם חשבת שיש לך גוף זר בעיניים?",
    "במהלך השבוע האחרון, האם חשת כאב בעיניים?",
    "במהלך השבוע האחרון, האם חווית ראייה מטושטשת?",
    "במהלך השבוע האחרון, האם חווית ראייה ירודה?",
    "במהלך השבוע האחרון, האם חווית קושי בקריאה?",
    "במהלך השבוע האחרון, האם חווית קושי בנהיגה בלילה?",
    "במהלך השבוע האחרון, האם חווית קושי בעבודה עם מסך מחשב או צפייה בטלוויזיה?",
    "במהלך השבוע האחרון, האם חווית קושי במקומות עם רוח?",
    "במהלך השבוע האחרון, האם חווית קושי במקומות יבשים?",
    "במהלך השבוע האחרון, האם חווית קושי במקומות ממוזגים?",
    "במהלך השבוע האחרון, האם חווית קושי בעת הרכבת עדשות מגע?"
]
ANSWERS = {"כל הזמן": 4, "רוב הזמן": 3, "מחצית מהזמן": 2, "לעתים": 1, "אף פעם": 0}
NA_QUESTIONS_INDICES = [5, 6, 7]

# =============================================================================
# 4. הגדרת המסכים של האפליקציה
# =============================================================================

class BaseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root_layout = FloatLayout()
        self.card = Card(orientation='vertical', padding=30, spacing=15, 
                         size_hint=(0.9, 0.9), 
                         pos_hint={'center_x': 0.5, 'center_y': 0.5})
        root_layout.add_widget(self.card)
        self.add_widget(root_layout)

    def on_enter(self, *args):
        self.apply_font_scaling()

    def apply_font_scaling(self):
        app = App.get_running_app()
        multiplier = 1.25 if app.accessibility_mode else 1.0
        
        for widget in self.walk():
            if hasattr(widget, 'font_size'):
                if not hasattr(widget, '_original_font_size'):
                    widget._original_font_size = widget.font_size
                
                font_size_value = float(str(widget._original_font_size).replace('sp',''))
                widget.font_size = f'{font_size_value * multiplier}sp'

class WelcomeScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = Label(text=fix_hebrew("שאלון OSDI"), font_name=FONT_NAME, font_size='32sp', color=colors["text_dark"], halign='center', size_hint_y=0.3)
        self.instructions = Label(text=fix_hebrew("ענה על השאלות הבאות לגבי התסמינים שחווית בשבוע האחרון."), font_name=FONT_NAME, font_size='18sp', color=colors["text_dark"], halign='center')
        start_button = StyledButton(text=fix_hebrew("התחל שאלון"), size_hint=(0.7, None), height=50, pos_hint={'center_x': 0.5})
        start_button.bind(on_press=lambda x: setattr(self.manager, 'current', get_q_screen_name(0)))

        self.card.bind(width=self.update_text_width)
        self.card.add_widget(self.title)
        self.card.add_widget(self.instructions)
        self.card.add_widget(start_button)
        
    def update_text_width(self, instance, width):
        self.instructions.text_size = (width * 0.9, None)

class QuestionScreen(BaseScreen):
    def __init__(self, question_text, question_index, **kwargs):
        super().__init__(**kwargs)
        self.question_index = question_index
        
        self.question_label = Label(text=fix_hebrew(f"שאלה {question_index + 1} מתוך 12:\n\n{question_text}"), font_name=FONT_NAME, font_size='22sp', color=colors["text_dark"], halign='center')
        self.card.add_widget(self.question_label)
        
        self.card.bind(width=self.update_text_width)

        answers_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.7)
        for answer_text, score in ANSWERS.items():
            btn = StyledToggleButton(text=fix_hebrew(answer_text), group=get_q_screen_name(question_index))
            btn.bind(on_press=lambda instance, s=score: self.select_answer(s))
            answers_layout.add_widget(btn)
        
        if self.question_index in NA_QUESTIONS_INDICES:
            na_btn = StyledToggleButton(text=fix_hebrew("לא רלוונטי"), group=get_q_screen_name(question_index))
            na_btn.background_color = colors["button_na"]
            na_btn.bind(on_press=lambda instance: self.select_answer(None))
            answers_layout.add_widget(na_btn)

        self.card.add_widget(answers_layout)

        self.next_button = StyledButton(text=fix_hebrew("הבא"), size_hint_y=None, height=50, disabled=True)
        self.next_button.bind(on_press=self.go_next)
        self.card.add_widget(self.next_button)
        
    def select_answer(self, score):
        self.manager.app.answers[self.question_index] = score
        self.next_button.disabled = False
        
    def go_next(self, instance):
        if self.question_index == 10: self.manager.current = PRE_Q12_SCREEN
        elif self.question_index == 11: self.manager.app.finish_quiz()
        else: self.manager.current = get_q_screen_name(self.question_index + 1)
            
    def update_text_width(self, instance, width):
        self.question_label.text_size = (width * 0.9, None)

class PreQuestion12Screen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.question_label = Label(text=fix_hebrew("האם הרכבת עדשות מגע במהלך השבוע האחרון?"), font_name=FONT_NAME, font_size='22sp', color=colors["text_dark"], halign='center')
        yes_button = StyledButton(text=fix_hebrew("כן"), size_hint_y=None, height=50)
        yes_button.bind(on_press=lambda x: setattr(self.manager, 'current', get_q_screen_name(11)))
        no_button = StyledButton(text=fix_hebrew("לא"), size_hint_y=None, height=50)
        no_button.bind(on_press=self.answer_no)

        self.card.add_widget(self.question_label)
        self.card.add_widget(yes_button)
        self.card.add_widget(no_button)

    def answer_no(self, instance):
        self.manager.app.answers[11] = None
        self.manager.app.finish_quiz()

class ResultsScreen(BaseScreen):
    score = NumericProperty(0)
    interpretation = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.score_label = Label(font_name=FONT_NAME, font_size='28sp', color=colors["text_dark"], halign='center', bold=True)
        self.interpretation_label = Label(font_name=FONT_NAME, font_size='22sp', color=colors["text_dark"], halign='center')
        
        export_button = StyledButton(text=fix_hebrew("שמור והמשך"), size_hint=(0.7, None), height=50, pos_hint={'center_x': 0.5})
        export_button.bind(on_press=lambda x: setattr(self.manager, 'current', EXPORT_SCREEN))
        
        self.card.add_widget(self.score_label)
        self.card.add_widget(self.interpretation_label)
        self.card.add_widget(export_button)

    def on_enter(self, *args):
        super().on_enter(*args)
        self.score_label.text = fix_hebrew(f"הציון שלך: {self.score:.1f}")
        self.interpretation_label.text = fix_hebrew(f"פרשנות: {self.interpretation}")

class ExportScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = Label(text=fix_hebrew("שמירת נתונים"), font_name=FONT_NAME, font_size='28sp', color=colors["text_dark"], halign='center', size_hint_y=0.2)
        
        self.customer_id_input = TextInput(hint_text=fix_hebrew("הזן מספר לקוח"), multiline=False, size_hint_y=None, height=50, font_name=FONT_NAME, font_size='18sp')
        self.customer_name_input = TextInput(hint_text=fix_hebrew("הזן שם לקוח"), multiline=False, size_hint_y=None, height=50, font_name=FONT_NAME, font_size='18sp')
        self.customer_phone_input = TextInput(hint_text=fix_hebrew("הזן מספר טלפון"), multiline=False, size_hint_y=None, height=50, font_name=FONT_NAME, font_size='18sp', input_filter='int')
        
        # --- חדש: חיבור פונקציה להגבלת אורך הטקסט ---
        self.customer_phone_input.bind(text=self.limit_phone_input)

        self.status_label = Label(text="", font_name=FONT_NAME, font_size='16sp', size_hint_y=0.3)
        save_button = StyledButton(text=fix_hebrew("שמור קובץ מאובטח"), size_hint=(0.7, None), height=50, pos_hint={'center_x': 0.5})
        save_button.bind(on_press=self.save_data)

        self.card.add_widget(self.title)
        self.card.add_widget(self.customer_id_input)
        self.card.add_widget(self.customer_name_input)
        self.card.add_widget(self.customer_phone_input)
        self.card.add_widget(save_button)
        self.card.add_widget(self.status_label)
    
    def limit_phone_input(self, instance, value):
        """פונקציה שמוודאת שהטקסט בשדה הטלפון לא ארוך מ-10 תווים"""
        if len(value) > 10:
            instance.text = value[:10]

    def save_data(self, instance):
        app = App.get_running_app()
        customer_id = self.customer_id_input.text
        customer_name = self.customer_name_input.text
        customer_phone = self.customer_phone_input.text

        if not all([customer_id, customer_name, customer_phone]):
            self.status_label.text = fix_hebrew("שגיאה: יש למלא את כל השדות")
            return
            
        # --- חדש: בדיקת תקינות נוספת לאורך מספר הטלפון ---
        if len(customer_phone) != 10:
            self.status_label.text = fix_hebrew("שגיאה: מספר הטלפון חייב להכיל 10 ספרות")
            return

        report_lines = [
            "תוצאות שאלון OSDI", "=====================",
            f"תאריך: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "",
            f"מספר לקוח: {customer_id}", f"שם לקוח: {customer_name}",
            f"מספר טלפון: {customer_phone}", "", "--- תוצאות ---",
            f"ציון OSDI: {app.final_score:.1f}", f"פרשנות: {app.final_interpretation}"
        ]
        file_content = "\n".join(report_lines)
        
        current_time = datetime.now()
        time_str = current_time.strftime('%H_%M')
        date_str = current_time.strftime('%d-%m-%Y')
        
        temp_txt_filename = f"temp_report_{current_time.strftime('%Y%m%d%H%M%S')}.txt"
        final_zip_filename = f"{customer_name}--{customer_id}--{time_str}_{date_str}.zip"
        
        temp_txt_filepath = os.path.join(DOWNLOADS_DIR, temp_txt_filename)
        final_zip_filepath = os.path.join(DOWNLOADS_DIR, final_zip_filename)

        try:
            with open(temp_txt_filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            pyminizip.compress(temp_txt_filepath, None, final_zip_filepath, ZIP_PASSWORD, 9)
            
            self.status_label.text = fix_hebrew(f"הקובץ המאובטח נשמר בהצלחה:\n{final_zip_filename}")

        except Exception as e:
            self.status_label.text = fix_hebrew(f"שגיאה בשמירת הקובץ המאובטח: {e}")
        finally:
            if os.path.exists(temp_txt_filepath):
                os.remove(temp_txt_filepath)

# =============================================================================
# 5. המחלקה הראשית של האפליקציה
# =============================================================================
class OSDIApp(App):
    accessibility_mode = BooleanProperty(False)
    final_score = NumericProperty(0)
    final_interpretation = StringProperty('')

    def build(self):
        if not os.path.exists(FONT_NAME):
            return Label(text=f"Error: Font file '{FONT_NAME}' not found.")

        self.answers = {}
        
        root_layout = FloatLayout()
        self.sm = ScreenManager(transition=FadeTransition(duration=0.2))
        self.sm.app = self

        self.sm.add_widget(WelcomeScreen(name=WELCOME_SCREEN))
        for i, q_text in enumerate(QUESTIONS):
            self.sm.add_widget(QuestionScreen(name=get_q_screen_name(i), question_text=q_text, question_index=i))
        self.sm.add_widget(PreQuestion12Screen(name=PRE_Q12_SCREEN))
        self.sm.add_widget(ResultsScreen(name=RESULTS_SCREEN))
        self.sm.add_widget(ExportScreen(name=EXPORT_SCREEN))
        
        self.sm.current = WELCOME_SCREEN
        root_layout.add_widget(self.sm)

        access_button = Button(text=fix_hebrew("נגישות"), font_name=FONT_NAME, size_hint=(None, None), size=('120dp', '50dp'), pos_hint={'top': 0.98, 'right': 0.98}, background_color=(0,0,0,0.5))
        access_button.bind(on_press=self.toggle_accessibility)
        root_layout.add_widget(access_button)

        return root_layout

    def toggle_accessibility(self, instance):
        self.accessibility_mode = not self.accessibility_mode
        self.sm.current_screen.apply_font_scaling()
    
    def finish_quiz(self):
        self.calculate_score()
        self.sm.current = RESULTS_SCREEN

    def calculate_score(self):
        valid_answers = {k: v for k, v in self.answers.items() if v is not None}
        
        num_questions_answered = len(valid_answers)
        if num_questions_answered == 0: score = 0
        else:
            total_score = sum(valid_answers.values())
            score = (total_score * 25) / num_questions_answered
        
        if score <= 12: interpretation = "תקין"
        elif score <= 22: interpretation = "יובש קל"
        elif score <= 32: interpretation = "יובש בינוני"
        else: interpretation = "יובש חמור"
        
        self.final_score = score
        self.final_interpretation = interpretation

        results_screen = self.sm.get_screen(RESULTS_SCREEN)
        results_screen.score = self.final_score
        results_screen.interpretation = self.final_interpretation
        
    def restart_app(self):
        self.answers.clear()
        self.sm.current = WELCOME_SCREEN

if __name__ == '__main__':
    OSDIApp().run()
