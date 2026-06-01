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

class GameState:
    def __init__(self):
        self.theme = None
        self.word = None
        self.round_id = 0
        self.roles_pool = []  # Очередь ролей (перемешанная)
        self.claimed_count = 0  # Сколько игроков уже забрали роль

    def start_new_round(self):
        self.theme = random.choice(list(WORDS_BANK.keys()))
        self.word = random.choice(WORDS_BANK[self.theme])
        self.round_id += 1
        self.claimed_count = 0
        
        # Создаем пул ролей для 4-х игроков и намертво его перемешиваем
        self.roles_pool = ["ХУДОЖНИК", "ХУДОЖНИК", "ХУДОЖНИК", "ХУДОЖНИК"]
        spy_index = random.randint(0, 3)
        self.roles_pool[spy_index] = "ШПИОН"

@st.cache_resource
def get_global_game():
    return GameState()

shared_game = get_global_game()

st.title("🎨 Fake Artist: Авто-Раздача по очереди")
st.write("Просто заходите по ссылке и по очереди берите карточки!")

# Кнопка перезапуска раунда
if st.button("🔄 Сгенерировать новый раунд (ДЛЯ ВСЕХ)", type="primary"):
    shared_game.start_new_round()
    # Очищаем локальную память браузера для нового раунда
    if "my_assigned_role" in st.session_state:
        del st.session_state["my_assigned_role"]
    if "my_player_number" in st.session_state:
        del st.session_state["my_player_number"]
    st.success(f"🎉 Раунд №{shared_game.round_id} успешно создан! Кнопки ниже обновились.")

st.divider()

if shared_game.theme is not None:
    st.subheader(f"Раунд №{shared_game.round_id}")
    
    # Ключ сессии привязываем к ID раунда, чтобы при перезапуске всё сбрасывалось автоматически
    role_key = f"assigned_role_r{shared_game.round_id}"
    num_key = f"player_num_r{shared_game.round_id}"
    
    # Если этот конкретный телефон/браузер еще не брал роль в этом раунде
    if role_key not in st.session_state:
        if shared_game.claimed_count < 4:
            if st.button("👁️ Узнать мою роль (Я зашел по очереди)"):
                # Присваиваем игроку следующую роль из перемешанного пула
                st.session_state[role_key] = shared_game.roles_pool[shared_game.claimed_count]
                shared_game.claimed_count += 1
                st.session_state[num_key] = shared_game.claimed_count
                st.rerun()
        else:
            st.error("🛑 Все 4 роли уже разобраны! Если хотите сыграть еще раз, нажмите кнопку сверху.")
            
    # Если роль уже успешно получена этим телефоном
    else:
        my_num = st.session_state[num_key]
        my_role = st.session_state[role_key]
        
        st.info(f"👤 Автоматически присвоен: **Игрок №{my_num}**")
        
        # Чекбокс, чтобы скрыть/показать код, если передаешь телефон или кто-то смотрит
        show_card = st.checkbox("Показать мою карточку", key=f"show_card_{shared_game.round_id}")
        
        if show_card:
            st.info(f"📋 Категория раунда: **{shared_game.theme}**")
            if my_role == "ШПИОН":
                st.error("🕵️ ТЫ ШПИОН! Ты не знаешь слова. Рисуй аккуратно и коси под художника!")
            else:
                st.success(f"✏️ ТЫ ХУДОЖНИК! Загаданное слово: **{shared_game.word}**")
else:
    st.warning("Игра еще не началась. Кто-нибудь один, нажмите кнопку «Сгенерировать новый раунд» выше.")