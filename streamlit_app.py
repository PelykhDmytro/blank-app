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

# Глобальное состояние игры, устойчивое к JSON-сериализации
class GameState:
    def __init__(self):
        self.theme = None
        self.word = None
        self.round_id = 0
        self.roles_pool = []
        self.claimed_count = 0
        self.themes_pool = []
        # Храним холст как чистый валидный JSON-словарь конфигурации Fabric.js
        self.canvas_data = {"objects": [], "background": "#ffffff"}

    def start_new_round(self):
        if not self.themes_pool:
            self.themes_pool = list(WORDS_BANK.keys())
            random.shuffle(self.themes_pool)
        
        self.theme = self.themes_pool.pop()
        self.word = random.choice(WORDS_BANK[self.theme])
        self.round_id += 1
        self.claimed_count = 0
        self.canvas_data = {"objects": [], "background": "#ffffff"}
        
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
        self.canvas_data = {"objects": [], "background": "#ffffff"}

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
    @st.fragment(run_every=4)
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
                st.error("🛑 Все роли разобраны!")
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
    
    # --- ИГРОВОЙ ХОЛСТ ---
    st.subheader("🖼️ Общая онлайн-доска")
    st.caption("Нарисуй ОДНУ линию и нажми кнопку «Отправить ход» под холстом.")

    # Динамический ключ для принудительного обновления холста при изменении данных на сервере
    lines_count = len(shared_game.canvas_data["objects"])
    canvas_key = f"global_canvas_r{shared_game.round_id}_l{lines_count}"

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0)",
        stroke_width=4,
        stroke_color="#111111",
        background_color="#ffffff",
        height=400,
        width=500,
        drawing_mode="freedraw",
        initial_drawing=shared_game.canvas_data,
        update_streamlit=True,
        key=canvas_key
    )

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Отправить мой ход", type="primary", use_container_width=True):
            if canvas_result is not None and canvas_result.json_data is not None:
                client_objects = canvas_result.json_data.get("objects", [])
                server_objects = shared_game.canvas_data.get("objects", [])
                
                if len(client_objects) > len(server_objects):
                    # Берем строго новые нарисованные линии
                    new_strokes = client_objects[len(server_objects):]
                    for stroke in new_strokes:
                        # Глубокое копирование через принудительный дамп строк, защищающее от искажения типов
                        clean_stroke = json.loads(json.dumps(stroke))
                        shared_game.canvas_data["objects"].append(clean_stroke)
                    
                    st.success("🎉 Ход засчитан!")
                    st.rerun()
                else:
                    st.warning("👉 Сначала нарисуй новую линию на холсте!")
                    
    with col2:
        if st.button("🔄 Синхронизировать доску", type="secondary", use_container_width=True):
            st.rerun()

    st.write("---")
    st.metric(label="📊 Всего линий на доске:", value=lines_count)