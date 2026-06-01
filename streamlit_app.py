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
        self.canvas_lines = []  # Список линий (массивы точек)

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
    # --- ЗОНА СТАТУСА (Обновление каждые 3 секунды) ---
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
    st.caption("Нарисуй одну линию (зажми мышку/палец) и нажми «Отправить мой ход».")

    # Жесткая очистка и валидация данных перед отправкой в JS
    cleaned_lines = []
    for line in shared_game.canvas_lines:
        if isinstance(line, list) and len(line) >= 2:
            cleaned_lines.append(line)
            
    existing_lines_json = json.dumps(cleaned_lines)

    # Стабильный HTML5 холст. Передает данные через стандартный Input
    custom_canvas_html = f"""
    <div style="text-align: center; font-family: sans-serif;">
        <canvas id="paintCanvas" width="500" height="350" style="border:2px solid #333; background-color:#fff; cursor:crosshair; border-radius:5px; touch-action: none;"></canvas>
        <br><br>
        <button id="sendBtn" style="background-color: #ff4b4b; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold;">📤 Отправить мой ход</button>
    </div>

    <script>
        const canvas = document.getElementById('paintCanvas');
        const ctx = canvas.getContext('2d');
        const sendBtn = document.getElementById('sendBtn');
        
        let isDrawing = false;
        let currentLine = [];
        const existingLines = {existing_lines_json};

        // Настройки кисти
        ctx.strokeStyle = "#111111";
        ctx.lineWidth = 4;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";

        // Отрисовка линий из базы данных
        function drawSavedLines() {{
            existingLines.forEach(line => {{
                if (!line || line.length < 2) return;
                ctx.beginPath();
                ctx.moveTo(line[0].x, line[0].y);
                for (let i = 1; i < line.length; i++) {{
                    ctx.lineTo(line[i].x, line[i].y);
                }}
                ctx.stroke();
            }});
        }}
        drawSavedLines();

        // Координаты
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

        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        window.addEventListener('mouseup', stopDrawing);

        canvas.addEventListener('touchstart', startDrawing, {{passive: false}});
        canvas.addEventListener('touchmove', draw, {{passive: false}});
        canvas.addEventListener('touchend', stopDrawing);

        // Отправка через postMessage в родительское окно без перезагрузок
        sendBtn.addEventListener('click', () => {{
            if (currentLine.length < 2) {{
                alert("Сначала нарисуй линию!");
                return;
            }}
            window.parent.postMessage({{
                type: 'streamlit:reportReady',
                value: JSON.stringify(currentLine)
            }}, '*');
            
            // Визуальный фидбек
            sendBtn.innerText = "⏳ Передаем ход...";
            sendBtn.style.backgroundColor = "#ffaa00";
        }});
    </script>
    """

    # Создаем скрытый или явный приемник данных в интерфейсе Streamlit
    # text_input поймает строку из JS, когда сработает событие отправки
    raw_transport = st.text_input("Системный буфер обмена (не трогать)", key="line_transport_buffer", label_visibility="collapsed")

    # Скрипт-мост, который берет сообщение из iframe холста и аккуратно вставляет в text_input Streamlit
    st.components.v1.html(custom_canvas_html, height=420)
    
    components_js_bridge = """
    <script>
    window.addEventListener('message', function(e) {
        if (e.data && e.data.type === 'streamlit:reportReady') {
            // Находим текстовое поле ввода Streamlit внутри родительского DOM и пишем туда данные
            const inputs = window.parent.document.querySelectorAll('input[type="text"]');
            // Перебираем, ищем наш скрытый буфер
            for (let input of inputs) {
                if (input.id && input.id.includes('line_transport_buffer')) {
                    input.value = e.data.value;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    break;
                }
            }
        }
    });
    </script>
    """
    st.components.v1.html(components_js_bridge, height=0)

    # Если в буфер прилетела строка с точками новой линии
    if raw_transport:
        try:
            new_line_data = json.loads(raw_transport)
            if new_line_data and (not shared_game.canvas_lines or shared_game.canvas_lines[-1] != new_line_data):
                shared_game.canvas_lines.append(new_line_data)
                # Очищаем сессионный буфер, чтобы скрипт не зациклился
                st.session_state["line_transport_buffer"] = ""
                st.success("Линия сохранена!")
                st.rerun()
        except Exception:
            pass

    # Кнопка ручной синхронизации для клиентов
    if st.button("🔄 Синхронизировать доску (Показать чужие ходы)", use_container_width=True):
        st.rerun()