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

# Создаем глобальный класс для игры, общий для всех устройств
class GameState:
    def __init__(self):
        self.theme = None
        self.word = None
        self.spy = None
        self.round_id = 0

    def start_new_round(self):
        self.theme = random.choice(list(WORDS_BANK.keys()))
        self.word = random.choice(WORDS_BANK[self.theme])
        self.spy = random.randint(1, 4)
        self.round_id += 1

# Кэшируем объект игры, чтобы он был один на весь сервер Streamlit
@st.cache_resource
def get_global_game():
    return GameState()

shared_game = get_global_game()

st.title("🎨 Fake Artist: Онлайн Раздача Ролей")
st.write("Один человек создает раунд — все заходят со своих телефонов и видят свои роли!")

# Блок перезапуска раунда
if st.button("🔄 Сгенерировать новый раунд (ДЛЯ ВСЕХ)", type="primary"):
    shared_game.start_new_round()
    st.success(f"🎉 Раунд №{shared_game.round_id} успешно создан! Роли перемешаны.")

st.divider()

# Блок игрока
if shared_game.theme is not None:
    st.subheader(f"Раунд №{shared_game.round_id}")
    
    player_num = st.selectbox(
        "Выбери свой номер игрока:", 
        [1, 2, 3, 4], 
        index=None, 
        placeholder="Кто ты из 4-х игроков?",
        key=f"player_select_{shared_game.round_id}"
    )
    
    if player_num:
        show_role = st.checkbox("👁️ Показать мою карточку (убедись, что никто не палит экран!)", key=f"show_{shared_game.round_id}")
        
        if show_role:
            st.info(f"📋 Категория раунда: **{shared_game.theme}**")
            
            if player_num == shared_game.spy:
                st.error("🕵️ ТЫ ШПИОН! Ты не знаешь слова. Рисуй аккуратно, маскируйся под художников!")
            else:
                st.success(f"✏️ ТЫ ХУДОЖНИК! Загаданное слово: **{shared_game.word}**")
else:
    st.warning("Игра еще не началась. Кто-нибудь один, нажмите кнопку «Сгенерировать новый раунд» выше.")