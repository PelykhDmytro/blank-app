import streamlit as st
import random

# Настройка страницы
st.set_page_config(page_title="Fake Artist Мультиплеер", page_icon="🎨", layout="centered")

# База категорий и слов
WORDS_BANK = {
    "Еда 🍔": ["Бургер", "Пицца", "Суши", "Шаурма", "Хот-дог", "Пельмени", "Круассан", "Пончик"],
    "Музыка 🎸": ["Гитара", "Барабаны", "Пианино", "Скрипка", "Микрофон", "Нота", "Саксофон"],
    "Животные 🦁": ["Пингвин", "Слон", "Жираф", "Кенгуру", "Акула", "Кот", "Медведь", "Лев"],
    "Транспорт 🚗": ["Трактор", "Самолет", "Велосипед", "Поезд", "Субмарина", "Вертолет", "Автобус"],
    "Одежда и Обувь 👟": ["Кроссовки", "Шляпа", "Куртка", "Носки", "Галстук", "Джинсы", "Футболка"]
}

ADMIN_PASSWORD = "123"

class GameState:
    def __init__(self):
        self.theme = None
        self.word = None
        self.round_id = 0
        self.roles_pool = []
        self.claimed_count = 0

@st.cache_resource
def get_global_game():
    return GameState()

shared_game = get_global_game()

st.title("🎨 Fake Artist: Живое Обновление")

# Панель ведущего в боковой панели
with st.sidebar:
    st.header("⚙️ Панель ведущего")
    pass_input = st.text_input("Введите пароль:", type="password")
    
    if pass_input == ADMIN_PASSWORD:
        st.success("Доступ разрешен!")
        
        # Кнопка генерации раунда
        if st.button("🔄 Сгенерировать новый раунд", type="primary", use_container_width=True):
            shared_game.theme = random.choice(list(WORDS_BANK.keys()))
            shared_game.word = random.choice(WORDS_BANK[shared_game.theme])
            shared_game.round_id += 1
            shared_game.claimed_count = 0
            
            shared_game.roles_pool = ["ХУДОЖНИК", "ХУДОЖНИК", "ХУДОЖНИК", "ХУДОЖНИК"]
            spy_index = random.randint(0, 3)
            shared_game.roles_pool[spy_index] = "ШПИОН"
            st.success(f"🎉 Раунд №{shared_game.round_id} запущен!")
            
        st.write("---")
        # Безопасный сброс параметров без вызова внутренних методов класса
        if st.button("❌ Сбросить всю игру с нуля", type="secondary", use_container_width=True):
            shared_game.theme = None
            shared_game.word = None
            shared_game.round_id = 0
            shared_game.roles_pool = []
            shared_game.claimed_count = 0
            st.warning("⚠️ Игра полностью сброшена!")
    else:
        st.caption("Панель только для создателя игры.")

st.divider()

# Спец-фрагмент для живого обновления раз в 2 секунды
@st.fragment(run_every=2)
def live_game_zone():
    if shared_game.round_id == 0 or shared_game.theme is None:
        st.warning("Организатор еще не запустил раунд или сбросил игру. Ждем...")
        # Чистим локальные сессии игроков при сбросе
        for key in list(st.session_state.keys()):
            if key.startswith("role_r"):
                del st.session_state[key]
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
            st.error("🛑 Все 4 роли уже разобраны! Ждем новый раунд от админа.")
    else:
        my_role = st.session_state[role_key]
        show_card = st.checkbox("Показать мою карточку", key=f"show_v_{shared_game.round_id}")
        
        if show_card:
            st.info(f"📋 Категория: **{shared_game.theme}**")
            if my_role == "ШПИОН":
                st.error("🕵️ ТЫ ШПИОН! Ты не знаешь слова. Рисуй аккуратно!")
            else:
                st.success(f"✏️ ТЫ ХУДОЖНИК! Загаданное слово: **{shared_game.word}**")

live_game_zone()