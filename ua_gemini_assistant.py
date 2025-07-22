# -*- coding: utf-8 -*-
import uno
import unohelper
# Імпортуємо константу для setPosSize один раз на початку
from com.sun.star.awt.PosSize import POS

try:
    # Цей імпорт має працювати, якщо ви виконали крок з `pip install`
    import google.generativeai as genai
except ImportError:
    genai = None

from com.sun.star.awt import XActionListener

# --- КОНФІГУРАЦІЯ ---
API_KEY = "Your_API_key"
AI_MODEL = "gemini-2.5-flash"

# --- СИСТЕМНИЙ ПРОМПТ ---
SYSTEM_PROMPT_TEMPLATE = """
###Роль: 
Ти – мій віртуальний асистент, що діє в ролі досвідченого та компетентного державного службовця.
###Основна мета:
Твоя головна задача – надавати мені професійну допомогу в роботі з текстами, суворо дотримуючись моїх вказівок.
###Ключові принципи поведінки:
Тон спілкування: Завжди використовуй офіційно-діловий стиль. Твої відповіді мають бути стриманими, безособовими, логічними та фактичними.
###Етика: 
Дій відповідно до етики державного службовця: будь об'єктивним, неупередженим, точним та конфіденційним. Уникай емоційних оцінок, особистих думок та будь-якої інформації, що не стосується справи.
###Виконання вказівок: 
Ти повинен чітко і беззаперечно виконувати мої команди. НЕ задавай уточнюючих питань. НЕ пропонуй альтернатив і НЕ перепитуй. Якщо моя вказівка недостатньо детальна, виконай її, спираючись на загальноприйняті норми ділового листування та наданий раніше контекст.
###Сфери компетенції:
Твої основні обов'язки включають:
Написання проєктів відповідей на листи та запити.
Складання офіційних та службових листів.
Структурний аналіз документів із виділенням ключових тез.
Редагування та покращення наданих мною текстів для відповідності діловому стилю.
###Формат відповіді: 
Надавай відповідь виключно по суті запиту. Не додавай вітань, прощань чи іншого супровідного тексту, якщо цього безпосередньо не вимагає завдання.

{user_instructions}
"""

# Глобальні змінні для доступу до сервісів UNO
CTX = uno.getComponentContext()
SM = CTX.getServiceManager()

def show_message_box(message, title="Повідомлення"):
    """Показує нативне вікно з повідомленням."""
    try:
        desktop = SM.createInstanceWithContext("com.sun.star.frame.Desktop", CTX)
        frame = desktop.getActiveFrame()
        if not frame: return
        
        window = frame.getContainerWindow()
        toolkit = window.getToolkit()
        msgbox = toolkit.createMessageBox(window, "MESSAGEBOX", 1, title, str(message))
        msgbox.execute()
    except Exception:
        pass

class DialogHandler(unohelper.Base, XActionListener):
    """Клас для створення та керування нативним діалоговим вікном LibreOffice."""

    def __init__(self, component):
        self.component = component
        self.dialog = self._create_dialog()

    def _create_dialog(self):
        """Створює та налаштовує всі елементи діалогового вікна програмно."""
        dialog = SM.createInstanceWithContext("com.sun.star.awt.UnoControlDialog", CTX)
        dialog_model = SM.createInstanceWithContext("com.sun.star.awt.UnoControlDialogModel", CTX)

        # --- ЗМІНА 1: Збільшуємо висоту вікна для нових полів ---
        dialog_model.Width = 320
        dialog_model.Height = 180 # Збільшили висоту
        dialog_model.Title = "AI Асистент"
        dialog.setModel(dialog_model)
        dialog.setPosSize(100, 100, 0, 0, POS)

        # 1. Мітка для випадаючого списку
        action_label = dialog_model.createInstance("com.sun.star.awt.UnoControlFixedTextModel")
        action_label.PositionX = 10
        action_label.PositionY = 10
        action_label.Width = 300
        action_label.Height = 10
        action_label.Label = "1. Виберіть дію (необов'язково):"
        dialog_model.insertByName("ActionLabel", action_label)
        
        # 2. Випадаючий список (ComboBox)
        action_selector_model = dialog_model.createInstance("com.sun.star.awt.UnoControlComboBoxModel")
        action_selector_model.PositionX = 10
        action_selector_model.PositionY = 25
        action_selector_model.Width = 300
        action_selector_model.Height = 15
        action_selector_model.Name = "ActionSelector" # Нове ім'я
        action_selector_model.Dropdown = True
        # --- ЗМІНА 2: Додаємо порожній елемент на початок ---
        action_selector_model.StringItemList = (
            "", # Пусте значення за замовчуванням
            "Покращ текст.",
            "Про що йдеться тут.",
            "Зроби текст довшим.",
            "Скороти текст."
        )
        action_selector_model.Text = "" # Встановлюємо порожній текст за замовчуванням
        dialog_model.insertByName("ActionSelector", action_selector_model)
        
        # 3. Мітка для текстового поля
        prompt_label = dialog_model.createInstance("com.sun.star.awt.UnoControlFixedTextModel")
        prompt_label.PositionX = 10
        prompt_label.PositionY = 50
        prompt_label.Width = 300
        prompt_label.Height = 10
        prompt_label.Label = "2. Введіть основний запит або текст:"
        dialog_model.insertByName("PromptLabel", prompt_label)

        # --- ЗМІНА 3: Повертаємо багаторядкове текстове поле ---
        text_field_model = dialog_model.createInstance("com.sun.star.awt.UnoControlEditModel")
        text_field_model.PositionX = 10
        text_field_model.PositionY = 65
        text_field_model.Width = 300
        text_field_model.Height = 70
        text_field_model.Name = "PromptInput" # Нове ім'я
        text_field_model.MultiLine = True
        text_field_model.VScroll = True
        dialog_model.insertByName("PromptInput", text_field_model)

        # 4. Кнопка OK
        ok_button_model = dialog_model.createInstance("com.sun.star.awt.UnoControlButtonModel")
        ok_button_model.PositionX = 200
        ok_button_model.PositionY = 150 # Змінили позицію
        ok_button_model.Width = 50
        ok_button_model.Height = 14
        ok_button_model.Label = "OK"
        ok_button_model.PushButtonType = 0
        ok_button_model.DefaultButton = True
        dialog_model.insertByName("OkButton", ok_button_model)

        # 5. Кнопка Скасувати
        cancel_button_model = dialog_model.createInstance("com.sun.star.awt.UnoControlButtonModel")
        cancel_button_model.PositionX = 255
        cancel_button_model.PositionY = 150 # Змінили позицію
        cancel_button_model.Width = 55
        cancel_button_model.Height = 14
        cancel_button_model.Label = "Скасувати"
        cancel_button_model.PushButtonType = 2
        dialog_model.insertByName("CancelButton", cancel_button_model)
        
        dialog.getControl("OkButton").addActionListener(self)
        
        self.dialog = dialog
        return self.dialog

    def show(self):
        self.dialog.setVisible(True)
        return self.dialog.execute()

    def actionPerformed(self, action_event):
        """Ця функція виконується, коли натискається кнопка OK."""
        # --- НОВА ЛОГІКА ВАЛІДАЦІЇ ---
        # 1. Отримуємо текст з ОБОХ полів
        action_text = self.dialog.getControl("ActionSelector").getText().strip()
        prompt_text = self.dialog.getControl("PromptInput").getText().strip()

        # 2. Перевіряємо, чи ОБИДВА поля порожні
        if not action_text and not prompt_text:
            show_message_box("Промпт не може бути порожнім. Виберіть дію або введіть текст.", "Помилка")
            return
            
        # 3. Об'єднуємо два поля в один фінальний запит
        if action_text and prompt_text:
            # Якщо є обидва значення, об'єднуємо їх
            user_input = f"{action_text}: {prompt_text}"
        elif action_text:
            # Якщо є тільки дія зі списку
            user_input = action_text
        else:
            # Якщо є тільки текст у полі
            user_input = prompt_text

        # --- Подальший код залишається без змін ---
        
        # Надійна логіка отримання тексту
        selected_text = ""
        try:
            selection = self.component.getCurrentSelection()
            if hasattr(selection, 'supportsService') and selection.supportsService("com.sun.star.text.TextRanges") and len(selection) > 0:
                text_range = selection.getByIndex(0)
                selected_text = text_range.String
            elif hasattr(selection, 'String'):
                selected_text = selection.String
        except Exception:
            selected_text = ""
        
        instructions = f"Інструкції:\n{user_input}"
        if selected_text:
            instructions += f"\n\nТекст для роботи:\n{selected_text}"
        
        final_prompt = SYSTEM_PROMPT_TEMPLATE.format(user_instructions=instructions)
        
        self.dialog.endExecute()
#        show_message_box("Надсилаю запит до AI...", "Генерація")

        try:
            genai.configure(api_key=API_KEY)
            ai_model = genai.GenerativeModel(AI_MODEL)
            response = ai_model.generate_content(final_prompt)
            
#            show_message_box(str(response), "Повна відповідь від API")
            
            generated_text = response.text
            
            current_selection = self.component.getCurrentSelection()
            range_to_write = current_selection.getByIndex(0) if hasattr(current_selection, 'getByIndex') else current_selection
            range_to_write.setString(generated_text)
            
        except Exception as e:
            show_message_box(f"Не вдалося згенерувати текст:\n{e}", "Помилка API")

def generate_text_with_ai():
    """Головна функція-тригер для макросу."""
    if not genai:
        show_message_box("Бібліотека 'google-generativeai' не знайдена. Будь ласка, встановіть її в Python-середовище LibreOffice.", "Критична помилка")
        return
        
    if not API_KEY or API_KEY == "Your_API_key":
        show_message_box("Будь ласка, вставте ваш Google AI API ключ у код скрипту.", "Помилка конфігурації")
        return

    desktop = SM.createInstanceWithContext("com.sun.star.frame.Desktop", CTX)
    model = desktop.getCurrentComponent()

    if not hasattr(model, "getCurrentSelection"):
        show_message_box("Цей скрипт можна запустити лише в текстовому документі.", "Помилка")
        return
        
    handler = DialogHandler(model)
    handler.show()

# Експортуємо функцію, щоб LibreOffice міг її викликати
g_exportedScripts = (generate_text_with_ai,)
