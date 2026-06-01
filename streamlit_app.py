import streamlit as st
import random
import os
import json
from streamlit_canvas import st_canvas

# Настройка страницы
st.set_page_config(page_title="Fake Artist Мультиплеер", page_icon="🎨", layout="centered")

ADMIN_PASSWORD = "123"

def load_words_from_file():
    base_words = {"Еда 🍔": ["Бургер", "Пицца", "Суши", "Кебаб"]}
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
        self.all_strokes = []  # Храним чистые словари объектов (рисунков)

    def start_new_round(self):
        if not self.themes_pool:
            self.themes_pool = list(WORDS_BANK.keys())
            random.shuffle(self.themes_pool)
        
        self.theme = self.themes_pool.pop()
        self.word = random.choice(WORDS_BANK[self.theme])
        self.round_id += 1
        self.claimed_count = 0
        self.all_strokes = []  
        
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
        self.all_strokes = []

@st.cache_resource
def get_global_game():
    return GameState()

shared_game = get_global_game()

st.title("🎨 Fake Artist Мультиплеер")

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

if shared_game.round_id == 0 or shared_game.theme is None:
    st.warning("Организатор еще не запустил раунд. Ждем...")
else:
    # --- ЗОНА СТАТУСА ---
    @st.fragment(run_every=3)
    def live_status_zone():
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
        
        st.caption(f"👥 Взяли роли: {shared_game.claimed_count} из 4")

    live_status_zone()

    st.write("---")
    st.subheader("🖼️ Общая онлайн-доска")

    # Пересобираем холст на основе сохраненных объектов линий
    initial_drawing = {"objects": shared_game.all_strokes, "background": ""}

    # Родной и стабильный холст
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0)",  # Прозрачный фон
        stroke_width=4,
        stroke_color="#111111",
        background_color="#ffffff",
        height=350,
        width=500,
        drawing_mode="freedraw",
        initial_drawing=initial_drawing,
        update_ some_data=True,
        key=f"canvas_classic_r{shared_game.round_id}"
    )

    st.write("### 📥 Шаг 2: Фиксация линии")
    if st.button("🚀 Отправить мой ход в игру", type="primary", use_container_width=True):
        if canvas_result.json_data is not None:
            current_objects = canvas_result.json_data.get("objects", [])
            
            if len(current_objects) > len(shared_game.all_strokes):
                # Берем только НОВУЮ нарисованную линию
                new_stroke = current_objects[-1]
                
                # Защита от JSON-ошибки: переводим в строку и обратно, получая чистый Python dict
                clean_dict = json.loads(json.dumps(new_stroke))
                
                shared_game.all_strokes.append(clean_dict)
                st.success("🎉 Линия успешно отправлена на сервер!")
                st.rerun()
            else:
                st.warning("👉 Сначала нарисуй новую линию на холсте перед отправкой!")

    # Кнопка обновления состояния для других игроков
    st.write("---")
    st.metric(label="📊 Всего линий нарисовано:", value=len(shared_game.all_strokes))
    if st.button("🔄 Обновить доску (Показать ходы других игроков)", use_container_width=True):
        st.rerun()