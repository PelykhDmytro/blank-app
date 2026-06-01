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
    # --- ЗОНА СТАТУСА (Авто-обновление у пацанов раз в 3 секунды) ---
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

    # Переводим существующие линии в JSON
    cleaned_lines = []
    for line in shared_game.canvas_lines:
        if isinstance(line, list) and len(line) >= 2:
            cleaned_lines.append(line)
    existing_lines_json = json.dumps(cleaned_lines)

    # HTML5 Холст с исправленным вызовом btoa()
    custom_canvas_html = f"""
    <div style="text-align: center; font-family: sans-serif; background-color: #f9f9f9; padding: 10px; border-radius: 10px;">
        <canvas id="paintCanvas" width="500" height="350" style="border:2px solid #333; background-color:#fff; cursor:crosshair; border-radius:5px; touch-action: none;"></canvas>
        <br><br>
        <button id="generateBtn" style="background-color: #ff4b4b; color: white; border: none; padding: 12px 20px; font-size: 15px; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold;"> Нажмите сюда, когда закончите линию</button>
        <br><br>
        <div id="outputZone" style="display: none; background: #e3f2fd; padding: 10px; border-radius: 5px; border: 1px dashed #1e88e5;">
            <span style="font-size: 13px; color: #0d47a1;"> Скопируйте этот код линии:</span>
            <input id="codeResult" type="text" readonly style="width: 100%; text-align: center; margin: 5px 0; padding: 8px; font-weight: bold; background-color: #fff; border: 1px solid #ccc;" onclick="this.select();">
            <span style="font-size: 11px; color: #555;">(Кликните на текст выше, чтобы выделить его, скопируйте и вставьте в поле ввода под холстом)</span>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('paintCanvas');
        const ctx = canvas.getContext('2d');
        const generateBtn = document.getElementById('generateBtn');
        const outputZone = document.getElementById('outputZone');
        const codeResult = document.getElementById('codeResult');
        
        let isDrawing = false;
        let currentLine = [];
        const existingLines = {existing_lines_json};

        ctx.strokeStyle = "#111111";
        ctx.lineWidth = 4;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";

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

        function getCoords(e) {{
            const rect = canvas.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            return {{ x: Math.round(clientX - rect.left), y: Math.round(clientY - rect.top) }};
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

        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        window.addEventListener('mouseup', () => isDrawing = false);

        canvas.addEventListener('touchstart', startDrawing, {{passive: false}});
        canvas.addEventListener('touchmove', draw, {{passive: false}});
        canvas.addEventListener('touchend', () => isDrawing = false);

        generateBtn.addEventListener('click', () => {{
            if (currentLine.length < 2) {{
                alert("Сначала нарисуйте линию на холсте!");
                return;
            }}
            // Фикс: Переводим массив в СТРОКУ перед тем, как кодировать через btoa
            const jsonStr = JSON.stringify(currentLine);
            const compressedStr = btoa(unescape(encodeURIComponent(jsonStr)));
            
            codeResult.value = compressedStr;
            outputZone.style.display = "block";
            generateBtn.innerText = " Код успешно сгенерирован ниже!";
            generateBtn.style.backgroundColor = "#2ebd59";
        }});
    </script>
    """

    # Выводим холст
    st.components.v1.html(custom_canvas_html, height=510)

    # Поле ввода Streamlit, куда игрок вставляет сгенерированный код хода
    st.write("### 📥 Шаг 2: Отправка хода в игру")
    input_code = st.text_input("Вставьте скопированный код линии сюда и нажмите Enter:", key=f"input_code_r{shared_game.round_id}")

    if input_code:
        try:
            import base64
            # Декодируем строку обратно в массив точек
            decoded_json = base64.b64decode(input_code).decode('utf-8')
            parsed_line = json.loads(decoded_json)
            
            if parsed_line and isinstance(parsed_line, list):
                if not shared_game.canvas_lines or shared_game.canvas_lines[-1] != parsed_line:
                    shared_game.canvas_lines.append(parsed_line)
                    st.success("🎉 Твой ход успешно добавлен на общую доску!")
                    st.rerun()
        except Exception:
            st.error("❌ Неверный код линии. Убедитесь, что скопировали его полностью.")

    # Кнопка ручной синхронизации
    st.write("---")
    if st.button("🔄 Обновить доску (Показать ходы других игроков)", use_container_width=True):
        st.rerun()