import streamlit as st
import random
import os

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

# Глобальный класс игры с защитой от пустых атрибутов
class GameState:
    def __init__(self):
        self.theme = None
        self.word = None
        self.round_id = 0
        self.roles_pool = []
        self.claimed_count = 0
        self.themes_pool = []
        self.current_painter = 1  # Заменили сложный индекс на простую переменную

    def start_new_round(self):
        if not self.themes_pool:
            self.themes_pool = list(WORDS_BANK.keys())
            random.shuffle(self.themes_pool)
        
        self.theme = self.themes_pool.pop()
        self.word = random.choice(WORDS_BANK[self.theme])
        self.round_id += 1
        self.claimed_count = 0
        self.current_painter = 1
        
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
        self.current_painter = 1

@st.cache_resource
def get_global_game():
    return GameState()

shared_game = get_global_game()

# Безопасный перехват на случай, если кэш сервера вернул старый объект без нового свойства
if not hasattr(shared_game, 'current_painter'):
    shared_game.current_painter = 1

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

st.divider()

if shared_game.round_id == 0 or shared_game.theme is None:
    st.warning("Организатор еще не запустил раунд. Ждем...")
else:
    # --- ЗОНА РОЛЕЙ ---
    st.subheader(f"🔷 Раунд №{shared_game.round_id}")
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
                st.error("🕵️ ТЫ ШПИОН! Ты не знаешь слова. Рисуй так, чтобы никто не догадался!")
            else:
                st.success(f"✏️ ТЫ ХУДОЖНИК! Загаданное слово: **{shared_game.word}**")
    
    st.caption(f"👥 Взяли роли: {shared_game.claimed_count} из 4")
    st.write("---")
    
    # --- ИГРОВОЙ ПРОЦЕСС ---
    st.subheader("🖼️ Инструкция к игре")
    st.info(
        "1. Откройте общую онлайн-доску в новой вкладке (например, [witeboard.com](https://witeboard.com) или [excalidraw.com](https://excalidraw.com)) и отправьте ссылку на неё всем игрокам.\n"
        "2. Каждый игрок в свой ход рисует на этой доске **ровно одну непрерывную линию**, не отрывая мышку или палец от экрана."
    )
    
    st.write("### ⏱️ Очередь рисования")
    st.metric(label="Сейчас должен рисовать Игрок №:", value=int(shared_game.current_painter))
    
    if st.button("✅ Я нарисовал линию, передать ход дальше", type="primary", use_container_width=True):
        if shared_game.current_painter < 4:
            shared_game.current_painter += 1
        else:
            shared_game.current_painter = 1
        st.rerun()