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

if shared_game.round_id == 0 or shared_game.theme is None:
    st.warning("Организатор еще не запустил раунд. Ждем...")
else:
    # --- ФРАГМЕНТ 1: Живой статус игроков и ролей (тикает сам) ---
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
        
        # Индикатор для пацанов, сколько людей уже зашли в игру
        st.caption(f"👥 Игроков взяли роли: {shared_game.claimed_count} из 4")

    live_status_zone()

    st.write("---")
    st.subheader("🖼️ Общая онлайн доска")
    st.caption("Сделай свой ход (нарисуй линию). Нажми кнопку отправки, чтобы её увидели остальные, либо кнопку обновления, чтобы подтянуть чужие линии.")

    # --- ЗОНА ХОЛСТА: Вынесена из фрагмента для стабильного рендеринга ---
    canvas_kwargs = {
        "fill_color": "rgba(255, 165, 0, 0.3)",
        "stroke_width": 4,
        "stroke_color": "#000000",
        "background_color": "#FFFFFF",
        "update_vis_cycle": False, # Выключаем внутренний триггер обновлений
        "height": 400,
        "width": 500,
        "drawing_mode": "freedraw",
        "key": f"canvas_v2_r{shared_game.round_id}" # Сбрасывается только при смене раунда
    }

    if shared_game.canvas_data is not None:
        if isinstance(shared_game.canvas_data, str):
            canvas_kwargs["initial_drawing"] = shared_game.canvas_data
        else:
            canvas_kwargs["initial_drawing"] = json.dumps(shared_game.canvas_data)

    # Стабильная отрисовка
    canvas_result = st_canvas(**canvas_kwargs)

    # Кнопки управления холстом
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Обновить доску", use_container_width=True):
            st.rerun()

    with col2:
        if canvas_result is not None and canvas_result.json_data is not None:
            # Если игрок нарисовал новые линии, которых нет в базе
            if canvas_result.json_data != shared_game.canvas_data:
                if canvas_result.json_data.get("objects"):
                    if st.button("📤 Отправить мой ход", type="primary", use_container_width=True):
                        shared_game.canvas_data = canvas_result.json_data
                        st.success("Ход отправлен!")
                        st.rerun()