import streamlit as st
import random
import os
import json

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
        self.canvas_lines = []  # Храним массивы точек для отрисовки линий

    def start_new_round(self):
        if not self.themes_pool:
            self.themes_pool = list(WORDS_BANK.keys())
            random.shuffle(self.themes_pool)
        
        self.theme = self.themes_pool.pop()
        self.word = random.choice(WORDS_BANK[self.theme])
        self.round_id += 1
        self.claimed_count = 0
        self.canvas_lines = []  
        
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
        self.canvas_lines = []

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
    # --- ЗОНА СТАТУСА (Обновляется автоматически каждые 3 секунды) ---
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
    st.caption("Нарисуй одну линию (зажми мышку/палец) и нажми «Отправить ход».")

    # Обработка входящих данных от HTML5 Canvas через query параметры
    query_params = st.query_params
    if "new_line" in query_params:
        try:
            raw_line = query_params["new_line"]
            line_data = json.loads(raw_line)
            if line_data and line_data not in shared_game.canvas_lines:
                shared_game.canvas_lines.append(line_data)
            # Очищаем параметры из URL, чтобы не дублировать линии при обновлении страницы
            st.query_params.clear()
            st.rerun()
        except Exception:
            pass

    # Сериализуем уже существующие линии, чтобы HTML-холст их отобразил
    existing_lines_json = json.dumps(shared_game.canvas_lines)

    # Встроенный HTML5 Canvas на чистом JS
    custom_canvas_html = f"""
    <div style="text-align: center; font-family: sans-serif;">
        <canvas id="paintCanvas" width="500" height="350" style="border:2px solid #333; background-color:#fff; cursor:crosshair; border-radius:5px;"></canvas>
        <br><br>
        <button id="sendBtn" style="background-color: #ff4b4b; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; width: 100%;">📤 Отправить мой ход</button>
    </div>

    <script>
        const canvas = document.getElementById('paintCanvas');
        const ctx = canvas.getContext('2d');
        const sendBtn = document.getElementById('sendBtn');
        
        let isDrawing = false;
        let currentLine = [];
        const existingLines = {existing_lines_json};

        // Настройки кисти (один цвет для всех)
        ctx.strokeStyle = "#222222";
        ctx.lineWidth = 4;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";

        // Рисуем уже сохраненные ранее линии пацанов
        function drawSavedLines() {{
            existingLines.forEach(line => {{
                if (line.length < 2) return;
                ctx.beginPath();
                ctx.moveTo(line[0].x, line[0].y);
                for (let i = 1; i < line.length; i++) {{
                    ctx.lineTo(line[i].x, line[i].y);
                }}
                ctx.stroke();
            }});
        }}
        drawSavedLines();

        // Логика рисования новой линии
        function getCoords(e) {{
            const rect = canvas.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            return {{ x: clientX - rect.left, y: clientY - rect.top }};
        }}

        function startDrawing(e) {{
            isDrawing = true;
            currentLine = [];
            const coords = getCoords(e);
            currentLine.push(coords);
            ctx.beginPath();
            ctx.moveTo(coords.x, coords.y);
        }}

        function draw(e) {{
            if (!isDrawing) return;
            e.preventDefault();
            const coords = getCoords(e);
            currentLine.push(coords);
            ctx.lineTo(coords.x, coords.y);
            ctx.stroke();
        }}

        function stopDrawing() {{
            isDrawing = false;
        }}

        // Мышь
        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        window.addEventListener('mouseup', stopDrawing);

        // Тачпад / Смартфоны
        canvas.addEventListener('touchstart', startDrawing, {{passive: false}});
        canvas.addEventListener('touchmove', draw, {{passive: false}});
        canvas.addEventListener('touchend', stopDrawing);

        // Отправка хода в Streamlit через перезапись query параметров окна
        sendBtn.addEventListener('click', () => {{
            if (currentLine.length < 2) {{
                alert("Сначала нарисуй линию!");
                return;
            }}
            const dataStr = JSON.stringify(currentLine);
            // Передаем данные наверх родителю (в Streamlit)
            const url = new URL(window.parent.location.href);
            url.searchParams.set("new_line", dataStr);
            window.parent.location.href = url.href;
        }});
    </script>
    """

    # Рендерим безопасный HTML-компонент холста
    st.components.v1.html(custom_canvas_html, height=430)

    # Кнопка ручного обновления, чтобы стянуть ходы других игроков
    if st.button("🔄 Синхронизировать доску (Подтянуть чужие ходы)", use_container_width=True):
        st.rerun()