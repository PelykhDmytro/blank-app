import streamlit as st
import random
import os
import json
from streamlit_drawable_canvas import st_canvas

# Настройка страницы
st.set_page_config(page_title="Fake Artist Мультиплеер", page_icon="🎨", layout="centered")

ADMIN_PASSWORD = "123"

def load_words_from_file():
    base_words = {"Еда 🍔": ["Бургер", "Пицца"]}
    filename = "words.txt"
    if not os.path.exists(filename):
        return base_words
    loaded_words = {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                theme, words_str = line.split(":", 1)
                words_list = [w.strip() for w in words_str.split(",") if w.strip()]
                if theme.strip() and words_list:
                    loaded_words[theme.strip()] = words_list
        return loaded_words if loaded_words else base_words
    except Exception:
        return base_words

WORDS_BANK = load_words_from_file()

class GameState:
    def __init__(self):
        self.theme = None
        self.word = None
        self.round_id = 0
        self.roles_pool = []
        self.claimed_count = 0
        self.themes_pool = []
        self.canvas_data = None  

    def start_new_round(self):
        if not self.themes_pool:
            self.themes_pool = list(WORDS_BANK.keys())
            random.shuffle(self.themes_pool)
        
        self.theme = self.themes_pool.pop()
        self.word = random.choice(WORDS_BANK[self.theme])
        self.round_id += 1
        self.claimed_count = 0
        self.canvas_data = None  
        
        self.roles_pool = ["ХУДОЖНИК", "ХУДОЖНИК", "ХУДОЖНИК", "ХУДОЖНИК"]
        spy_index = random.randint(0, 3)
        self.roles_pool[spy_index] = "ШПИОН"

    def reset_game_completely(self):
        self.theme = None
        self.word = None
        self.round_id = 0
        self.roles_pool = []
        self.claimed_count = 0
        self.themes_pool = []
        self.canvas_data = None

@st.cache_resource
def get_global_game():
    return GameState()

shared_game = get_global_game()

st.title("🎨 Fake Artist: Живое Обновление")
st.caption(f"Успешно загружено тем: {len(WORDS_BANK)}")

# Панель ведущего
with st.sidebar:
    st.header("⚙️ Панель ведущего")
    pass_input = st.text_input("Введите пароль:", type="password")
    
    if pass_input == ADMIN_PASSWORD:
        st.success("Доступ разрешен!")
        if st.button("🔄 Сгенерировать новый раунд", type="primary", use_container_width=True):
            shared_game.start_new_round()
            st.success(f"🎉 Раунд №{shared_game.round_id} запущен!")
            st.rerun()
            
        st.write("---")
        if st.button("❌ Сбросить всю игру с нуля", type="secondary", use_container_width=True):
            shared_game.reset_game_completely()
            st.success("Игра полностью сброшена!")
            st.rerun()
    else:
        st.caption("Панель только для создателя игры.")

st.divider()

# Автообновление зоны игры каждые 3 секунды
@st.fragment(run_every=3)
def live_game_zone():
    if shared_game.round_id == 0 or shared_game.theme is None:
        st.warning("Организатор еще не запустил раунд. Ждем...")
        return

    st.subheader(f"Текущий раунд №{shared_game.round_id}")
    role_key = f"role_r{shared_game.round_id}"
    
    if role_key not in st.session_state:
        if shared_game.claimed_count < 4:
            if st.button("👁️ Узнать мою роль", use_container_width=True):
                st.session_state[role_key] = shared_game.roles_pool[shared_game.claimed_count]
                shared_game.claimed_count += 1
                st.rerun()
        else:
            st.error("🛑 Все роли разобраны пацанами!")
    else:
        my_role = st.session_state[role_key]
        show_card = st.checkbox("Показать мою карточку", key=f"show_v_{shared_game.round_id}")
        if show_card:
            st.info(f"📋 Категория: **{shared_game.theme}**")
            if my_role == "ШПИОН":
                st.error("🕵️ ТЫ ШПИОН! Ты не знаешь слова. Рисуй аккуратно!")
            else:
                st.success(f"✏️ ТЫ ХУДОЖНИК! Загаданное слово: **{shared_game.word}**")

    st.write("---")
    st.subheader("🖼️ Общая онлайн доска")
    st.caption("Сделай свой ход (нарисуй одну линию) и нажми кнопку ниже, чтобы отправить её остальным:")

    # Намертво фиксируем настройки без динамических ключей, вызывающих сбои в реакте
    canvas_kwargs = {
        "fill_color": "rgba(255, 165, 0, 0.3)",
        "stroke_width": 4,
        "stroke_color": "#000000",
        "background_color": "#FFFFFF",
        "update_vis_cycle": True,
        "height": 400,
        "width": 500,
        "drawing_mode": "freedraw",
        "key": "stable_shared_canvas"
    }

    # Жесткая и безопасная проверка рисунка перед передачей
    if shared_game.canvas_data is not None:
        try:
            if isinstance(shared_game.canvas_data, str):
                # Проверяем, что это валидный JSON, а не мусор
                json.loads(shared_game.canvas_data)
                canvas_kwargs["initial_drawing"] = shared_game.canvas_data
            else:
                canvas_kwargs["initial_drawing"] = json.dumps(shared_game.canvas_data)
        except Exception:
            # Если там битая структура, просто игнорим её во избежание падения
            pass

    # Капсулируем холст в try/except — если реакт-компонент заглючит, юзер не увидит красную ошибку
    canvas_result = None
    try:
        canvas_container = st.container()
        with canvas_container:
            canvas_result = st_canvas(**canvas_kwargs)
    except Exception:
        st.info("🔄 Синхронизация холста... Нарисуйте линию, если поле очистилось.")

    # Проверяем и отправляем данные, только если холст успешно отрендерился
    if canvas_result is not None and canvas_result.json_data is not None:
        # Защита: отправляем, только если данные реально отличаются от глобальных
        if canvas_result.json_data != shared_game.canvas_data:
            lines = canvas_result.json_data.get("objects", [])
            if lines:
                if st.button("📤 Отправить мою линию на доску", type="primary", use_container_width=True):
                    shared_game.canvas_data = canvas_result.json_data
                    st.success("Линия зафиксирована!")
                    st.rerun()

live_game_zone()