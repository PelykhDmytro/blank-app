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

# Стабильное хранилище данных без сложных объектов
class GameState:
    def __init__(self):
        self.theme = None
        self.word = None
        self.round_id = 0
        self.roles_pool = []
        self.claimed_count = 0
        self.themes_pool = []
        self.canvas_lines = []  # Храним линии как чистые списки точек

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
    
    # --- ИГРОВОЙ ХОЛСТ ---
    st.subheader("🖼️ Общая онлайн-доска")
    st.caption("Нарисуй одну непрерывную линию. После этого внизу появится кнопка отправки.")

    # Кодируем текущие линии в строку, чтобы передать без конфликтов синтаксиса
    existing_lines_str = json.dumps(shared_game.canvas_lines)

    # Чистый HTML код БЕЗ f-строки (символы { } больше не вызовут SyntaxError!)
    custom_canvas_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; padding: 0; display: flex; flex-direction: column; align-items: center; }
            canvas { border: 2px solid #333; border-radius: 8px; background: #ffffff; cursor: crosshair; touch-action: none; }
        </style>
    </head>
    <body>
        <div id="serverData" style="display:none;"></div>
        
        <canvas id="paintCanvas" width="500" height="380"></canvas>

        <script>
            const canvas = document.getElementById('paintCanvas');
            const ctx = canvas.getContext('2d');
            
            ctx.lineWidth = 4;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.strokeStyle = '#111111';

            // Безопасно парсим старые линии
            try {
                const dataDiv = document.getElementById('serverData');
                const serverLines = JSON.parse(dataDiv.innerText || "[]");
                serverLines.forEach(line => {
                    if (line.length < 2) return;
                    ctx.beginPath();
                    ctx.moveTo(line[0].x, line[0].y);
                    for (let i = 1; i < line.length; i++) {
                        ctx.lineTo(line[i].x, line[i].y);
                    }
                    ctx.stroke();
                });
            } catch(e) { console.error(e); }

            let isPainting = false;
            let currentLine = [];
            let drawn = false;

            function getPos(e) {
                const rect = canvas.getBoundingClientRect();
                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                return { x: clientX - rect.left, y: clientY - rect.top };
            }

            function startDraw(e) {
                if (drawn) return;
                isPainting = true;
                const pos = getPos(e);
                currentLine = [pos];
                ctx.beginPath();
                ctx.moveTo(pos.x, pos.y);
            }

            function draw(e) {
                if (!isPainting) return;
                const pos = getPos(e);
                currentLine.push(pos);
                ctx.lineTo(pos.x, pos.y);
                ctx.stroke();
            }

            function stopDraw() {
                if (!isPainting) return;
                isPainting = false;
                if (currentLine.length >= 2) {
                    drawn = true;
                    // Передаем массив точек обратно в родительский Streamlit
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: JSON.stringify(currentLine)
                    }, '*');
                }
            }

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

    # Динамически внедряем наши линии в скрытый блок текста перед рендерингом компонента
    html_with_data = custom_canvas_html.replace(
        '<div id="serverData" style="display:none;"></div>',
        f'<div id="serverData" style="display:none;">{existing_lines_str}</div>'
    )

    # Генерируем уникальный ключ, чтобы при изменении количества линий холст перерисовывался у всех
    canvas_key = f"html5_canvas_r{shared_game.round_id}_v{len(shared_game.canvas_lines)}"
    
    # Запускаем компонент, он вернет строку-JSON новой линии, когда юзер закончит рисовать
    drawn_line_json = components.html(html_with_data, height=395, key=canvas_key)

    # --- КНОПКА ОТПРАВКИ ХОДА ---
    st.write("### 📥 Шаг 2: Фиксация хода")
    
    if drawn_line_json:
        if st.button("🚀 Отправить мою линию на доску", type="primary", use_container_width=True):
            try:
                new_line_points = json.loads(drawn_line_json)
                shared_game.canvas_lines.append(new_line_points)
                st.success("🎉 Линия успешно отправлена!")
                st.rerun()
            except Exception as err:
                st.error(f"Ошибка сохранения: {err}")
    else:
        st.info("Проведи линию на холсте выше, чтобы появилась кнопка подтверждения хода.")

    if st.button("🔄 Синхронизировать доску (Обновить рисунки других)", use_container_width=True):
        st.rerun()

    st.write("---")
    st.metric(label="📊 Всего линий нарисовано на доске:", value=len(shared_game.canvas_lines))