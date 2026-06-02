import streamlit as st
import random
import os

# Настройка страницы
st.set_page_config(page_title="Fake Artist Мультиплеер", page_icon="🎨", layout="centered")

ADMIN_PASSWORD = "123"

# Функция автоматической загрузки слов из файла
def load_words_from_file():
    base_words = {
        "Еда 🍔": ["Бургер", "Пицца", "Суши", "Шаурма", "Хот-дог"],
        "Музыка 🎸": ["Гитара", "Барабаны", "Пианино", "Скрипка", "Микрофон"]
    }
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

# Загружаем базу слов
WORDS_BANK = load_words_from_file()

class GameState:
    def __init__(self):
        self.theme = None
        self.word = None
        self.round_id = 0
        self.roles_pool = []
        self.claimed_count = 0
        self.themes_pool = []
        self.total_players = 4  # Базовое значение

    # Сделали players_count=4 по умолчанию, чтобы старый кэш не вызывал TypeError
    def start_new_round(self, players_count=4):
        self.total_players = players_count
        
        if not self.themes_pool:
            self.themes_pool = list(WORDS_BANK.keys())
            random.shuffle(self.themes_pool)
        
        self.theme = self.themes_pool.pop()
        self.word = random.choice(WORDS_BANK[self.theme])
        
        self.round_id += 1
        self.claimed_count = 0
        
        # Генерируем пул ролей под выбранное количество игроков
        self.roles_pool = ["ХУДОЖНИК"] * int(self.total_players)
        spy_index = random.randint(0, int(self.total_players) - 1)
        self.roles_pool[spy_index] = "ШПИОН"

    def reset_game_completely(self):
        self.theme = None
        self.word = None
        self.round_id = 0
        self.roles_pool = []
        self.claimed_count = 0
        self.themes_pool = []

# Переименовали функцию кэша, чтобы Streamlit принудительно сбросил старую память сервера
@st.cache_resource
def get_fresh_global_game():
    return GameState()

shared_game = get_fresh_global_game()

# Проверяем, что у объекта точно есть нужное свойство (защита от багов кэша)
if not hasattr(shared_game, 'total_players'):
    shared_game.total_players = 4

st.title("🎨 Fake Artist: Живое Обновление")
st.caption(f"Загружено тем из файла words.txt: {len(WORDS_BANK)}")

# Панель ведущего
with st.sidebar:
    st.header("⚙️ Панель ведущего")
    pass_input = st.text_input("Введите пароль:", type="password")
    
    if pass_input == ADMIN_PASSWORD:
        st.success("Доступ разрешен!")
        
        # Настройка количества игроков перед стартом раунда
        players_count = st.number_input(
            "Количество игроков:", 
            min_value=3, 
            max_value=10, 
            value=int(shared_game.total_players), 
            step=1
        )
        
        if st.button("🔄 Сгенерировать новый раунд", type="primary", use_container_width=True):
            shared_game.start_new_round(players_count)
            st.success(f"🎉 Раунд №{shared_game.round_id} запущен для {players_count} игроков!")
            st.rerun()
            
        st.write("---")
        if st.button("❌ Сбросить всю игру с нуля", type="secondary", use_container_width=True):
            shared_game.reset_game_completely()
            st.warning("⚠️ Игра полностью сброшена!")
            st.rerun()
    else:
        st.caption("Панель только для создателя игры.")

st.divider()

# Спец-фрагмент для живого обновления раз в 2 секунды
@st.fragment(run_every=2)
def live_game_zone():
    if shared_game.round_id == 0 or shared_game.theme is None:
        st.warning("Организатор еще не запустил раунд или сбросил игру. Ждем...")
        for key in list(st.session_state.keys()):
            if key.startswith("role_r"):
                del st.session_state[key]
        return

    st.subheader(f"Текущий раунд №{shared_game.round_id}")
    role_key = f"role_r{shared_game.round_id}"
    
    # Защитное получение лимита игроков
    total_slots = int(getattr(shared_game, 'total_players', 4))
    
    if role_key not in st.session_state:
        if shared_game.claimed_count < total_slots:
            if st.button("👁️ Узнать мою роль", use_container_width=True):
                st.session_state[role_key] = shared_game.roles_pool[shared_game.claimed_count]
                shared_game.claimed_count += 1
                st.rerun()
        else:
            st.error(f"🛑 Все {total_slots} ролей уже разобраны! Ждем новый раунд от админа.")
    else:
        my_role = st.session_state[role_key]
        show_card = st.checkbox("Показать мою карточку", key=f"show_v_{shared_game.round_id}")
        
        if show_card:
            st.info(f"📋 Категория: **{shared_game.theme}**")
            if my_role == "ШПИОН":
                st.error("🕵️ ТЫ ШПИОН! Ты не знаешь слова. Рисуй аккуратно!")
            else:
                st.success(f"✏️ ТЫ ХУДОЖНИК! Загаданное слово: **{shared_game.word}**")

    # Динамический счетчик игроков
    st.caption(f"👥 Карточки разобрали: {shared_game.claimed_count} из {total_slots}")

live_game_zone()
