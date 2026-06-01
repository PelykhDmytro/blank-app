import streamlit as st
import random
import os
import json
import streamlit.components.v1 as components

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

# Стабильное состояние игры без хранения сложных объектов
class GameState:
    def __init__(self):
        self.theme = None
        self.word = None
        self.round_id = 0
        self.roles_pool = []
        self.claimed_count = 0
        self.themes_pool = []
        self.canvas_lines = []  # Храним линии как обычный список строк/массивов

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
    
    # --- ИГРОВОЙ ХОЛСТ (HTML5 Canvas) ---
    st.subheader("🖼️ Общая онлайн-доска")
    st.caption("Нарисуй одну линию (зажми мышку/палец) и нажми «Отправить ход».")

    # Сериализуем линии в простой JSON-текст для передачи внутрь HTML
    existing_lines_json = json.dumps(shared_game.canvas_lines)

    custom_canvas_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; display: flex; flex-direction: column; align-items: center; font-family: sans-serif; }}
            canvas {{ border: 2px solid #333; border-radius: 8px; background: #ffffff; cursor: crosshair; touch-action: none; }}
            #btn-container {{ width: 500px; margin-top: 10px; display: flex; justify-content: space-between; }}
            button {{ padding: 10px 16px; font-size: 14px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; width: 100%; }}
            .btn-success {{ background-color: #28a745; color: white; }}
            .btn-disabled {{ background-color: #cccccc; color: #666666; cursor: not-allowed; }}
        </style>
    </head>
    <body>
        <canvas id="paintCanvas" width="500" height="380"></canvas>
        <div id="btn-container">
            <button id="sendBtn" class="btn-disabled" disabled>Код сгенерирован ниже!</button>
        </div>

        <script>
            const canvas = document.getElementById('paintCanvas');
            const ctx = canvas.getContext('2d');
            const sendBtn = document.getElementById('sendBtn');
            
            ctx.lineWidth = 4;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.strokeStyle = '#111111';

            // Отрисовка уже существующих линий с сервера
            const serverLines = {existing_lines_json};
            serverLines.forEach(line => {{
                if (line.length < 2) return;
                ctx.beginPath();
                ctx.moveTo(line[0].x, line[0].y);
                for (let i = 1; i < line.length; i++) {{
                    ctx.lineTo(line[i].x, line[i].y);
                }}
                ctx.stroke();
            }});

            let isPainting = false;
            let currentLine = [];
            let hasDrawnNewLine = false;

            function getPos(e) {{
                const rect = canvas.getBoundingClientRect();
                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                return {{
                    x: clientX - rect.left,
                    y: clientY - rect.top
                }};
            }}

            function startDraw(e) {{
                if (hasDrawnNewLine) return; // Только одна линия за ход
                isPainting = true;
                const pos = getPos(e);
                currentLine = [pos];
                ctx.beginPath();
                ctx.moveTo(pos.x, pos.y);
            }}

            function draw(e) {{
                if (!isPainting) return;
                const pos = getPos(e);
                currentLine.push(pos);
                ctx.lineTo(pos.x, pos.y);
                ctx.stroke();
            }}

            function stopDraw() {{
                if (!isPainting) return;
                isPainting = false;
                if (currentLine.length >= 2) {{
                    hasDrawnNewLine = true;
                    sendBtn.disabled = false;
                    sendBtn.className = "btn-success";
                    sendBtn.innerText = "Нажмите сюда, когда закончите линию";
                    
                    // Передаем данные обратно в Streamlit через хэш URL родительского окна
                    sendBtn.onclick = function() {{
                        const encodedData = btoa(encodeURIComponent(JSON.stringify(currentLine)));
                        window.parent.postMessage({{type: 'streamlit:setComponentValue', value: encodedData}}, '*');
                    }};
                }}
            }}

            canvas.addEventListener('mousedown', startDraw);
            canvas.addEventListener('mousemove', draw);
            window.addEventListener('mouseup', stopDraw);

            canvas.addEventListener('touchstart', startDraw);
            canvas.addEventListener('touchmove', draw);
            canvas.addEventListener('touchend', stopDraw);
        </script>
    </body>
    </html>
    """

    # Отображаем кастомный безопасный холст
    # Присваиваем уникальный ключ на основе количества линий, чтобы он обновлялся при новых ходах
    canvas_key = f"custom_html_canvas_v1_{len(shared_game.canvas_lines)}"
    
    # Компонент возвращает данные из postMessage
    response_data = components.html(custom_canvas_html, height=430, key=canvas_key)

    st.write("### 📥 Шаг 2: Отправка хода в игру")
    
    if response_data:
        try:
            import base64
            import urllib.parse
            # Декодируем безопасную строку от JS холста
            raw_json = urllib.parse.unquote(base64.b64decode(response_data).decode('utf-8'))
            new_line_object = json.loads(raw_json)
            
            if st.button("🚀 Подтвердить и отправить ход на доску", type="primary", use_container_width=True):
                shared_game.canvas_lines.append(new_line_object)
                st.success("🎉 Твоя линия успешно добавлена!")
                st.rerun()
        except Exception:
            st.caption("Ожидание рисования линии...")
    else:
        st.info("Сначала нарисуйте одну линию на холсте выше, чтобы появилась кнопка подтверждения.")

    if st.button("🔄 Синхронизировать доску (Посмотреть чужие ходы)", use_container_width=True):
        st.rerun()

    st.write("---")
    st.metric(label="📊 Всего линий на доске:", value=len(shared_game.canvas_lines))