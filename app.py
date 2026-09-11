import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, date

# --- 1. НАЛАШТУВАННЯ БАЗИ ДАНИХ (SQLite) ---
DB_NAME = "radiation_control.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personnel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                position TEXT NOT NULL,
                start_year INTEGER NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                measurement_date DATE NOT NULL,
                dose_msv REAL NOT NULL,
                FOREIGN KEY (person_id) REFERENCES personnel (id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annual_archives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER UNIQUE NOT NULL,
                archived_at DATETIME NOT NULL,
                total_people INTEGER NOT NULL,
                collective_dose REAL NOT NULL
            )
        ''')
        conn.commit()

init_db()

# --- 2. ФУНКЦІЇ РОБОТИ З ДАНИМИ (CRUD) ---
def get_personnel():
    with get_connection() as conn:
        return pd.read_sql("SELECT id, full_name, position, start_year FROM personnel ORDER BY full_name", conn)

def add_person(full_name, position, start_year=2026):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO personnel (full_name, position, start_year) VALUES (?, ?, ?)",
            (full_name, position, start_year)
        )
        conn.commit()

def update_person(person_id, full_name, position, start_year=2026):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE personnel SET full_name=?, position=?, start_year=? WHERE id=?",
            (full_name, position, start_year, person_id)
        )
        conn.commit()

def delete_person(person_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM personnel WHERE id=?", (person_id,))
        conn.commit()

def add_measurement(person_id, measurement_date, dose_msv):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO measurements (person_id, measurement_date, dose_msv) VALUES (?, ?, ?)",
            (person_id, measurement_date, dose_msv)
        )
        conn.commit()

def update_measurement(measurement_id, person_id, measurement_date, dose_msv):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE measurements SET person_id=?, measurement_date=?, dose_msv=? WHERE id=?",
            (person_id, measurement_date, dose_msv, measurement_id)
        )
        conn.commit()

def delete_measurement(measurement_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM measurements WHERE id=?", (measurement_id,))
        conn.commit()

def get_all_measurements():
    with get_connection() as conn:
        query = '''
            SELECT 
                m.id AS measurement_id,
                p.id AS person_id,
                p.full_name,
                p.position,
                m.measurement_date,
                m.dose_msv,
                strftime('%Y', m.measurement_date) AS year
            FROM measurements m
            JOIN personnel p ON m.person_id = p.id
            ORDER BY m.measurement_date DESC
        '''
        return pd.read_sql(query, conn)

# --- 3. НАЛАШТУВАННЯ СТОРІНКИ ТА CSS ---
st.set_page_config(
    page_title="Система ІДК", 
    layout="wide",
    initial_sidebar_state="expanded"
)

cbrn_style = """
<style>
    /* 1. ПРИХОВУЄМО СТАНДАРТНЕ МЕНЮ STREAMLIT */
    #MainMenu, 
    footer, 
    [data-testid="stDecoration"], 
    [data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* ФІКС ШАПКИ ДЛЯ МОБІЛЬНИХ: Темний фон замість білого */
    header[data-testid="stHeader"] {
        background-color: #0B101D !important;
        z-index: 99999 !important;
    }

    /* 2. КНОПКА ТА СТРІЛКА РОЗГОРТАННЯ/ЗГОРТАННЯ ПАНЕЛІ (У ЧЕРВОНОМУ КВАДРАТІ) */
    [data-testid="stSidebarToggle"], 
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    header[data-testid="stHeader"] button,
    button[aria-label*="sidebar"],
    button[aria-label*="Sidebar"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        background-color: #121826 !important;
        border: 2px solid #FF0000 !important; /* Червона рамка (квадрат) */
        border-radius: 6px !important;
        padding: 5px !important;
        margin: 5px !important;
        cursor: pointer !important;
    }

    /* Червона стрілочка всередині кнопки */
    [data-testid="stSidebarToggle"] svg, 
    [data-testid="collapsedControl"] svg,
    [data-testid="stSidebarCollapseButton"] svg,
    header[data-testid="stHeader"] button svg,
    button[aria-label*="sidebar"] svg,
    button[aria-label*="Sidebar"] svg {
        fill: #FF0000 !important;
        color: #FF0000 !important;
        stroke: #FF0000 !important;
        width: 24px !important;
        height: 24px !important;
    }

    /* 3. ПРИМУСОВИЙ ТЕМНИЙ РЕЖИМ ДЛЯ ДАТИ НА СМАРТФОНАХ (ЧОРНИЙ ФОН / БІЛИЙ ТЕКСТ) */
    :root, html, body {
        color-scheme: dark !important; /* Головний фікс для iOS/Android нативних контролів */
    }

    /* Віконце дати та інші текстові поля */
    div[data-baseweb="datepicker"],
    div[data-baseweb="datepicker"] *,
    div[data-baseweb="input"],
    div[data-baseweb="input"] *,
    div[data-baseweb="base-input"],
    div[data-baseweb="base-input"] *,
    input[type="date"],
    input[type="text"],
    input {
        background-color: #000000 !important; /* Чорний фон */
        color: #FFFFFF !important;            /* Білий текст */
        -webkit-text-fill-color: #FFFFFF !important; /* Фікс для iOS Safari / Chrome */
        -webkit-appearance: none !important;
        border-color: #FFE600 !important;
        color-scheme: dark !important;
    }

    /* Іконка календаря у полі дати — біла */
    input::-webkit-calendar-picker-indicator {
        filter: invert(1) !important;
        cursor: pointer !important;
    }

    /* Стилізація випадаючого вікна календаря */
    div[data-baseweb="popover"], 
    div[data-baseweb="calendar"],
    div[data-baseweb="calendar"] * {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }

    div[data-baseweb="calendar"] button {
        color: #FFE600 !important;
    }

    /* 4. БОКОВА ПАНЕЛЬ */
    section[data-testid="stSidebar"] {
        background-color: #0E1422 !important;
        border-right: 3px solid #FFE600 !important;
        min-width: 280px !important;
    }

    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    
    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem !important;
    }

    /* 5. ЗАГАЛЬНА ТЕМНА ТЕМА НДІ/ХБРЯ */
    .stApp {
        background-color: #0B101D;
        color: #FFE600 !important;
        font-family: system-ui, -apple-system, sans-serif !important;
    }

    h1, h2, h3, label, .stMarkdown, p, span {
        color: #FFE600 !important;
        font-weight: bold !important;
    }

    /* 6. БЛОКИ ТА ТАБЛИЦІ */
    div[data-testid="stForm"], 
    div[data-testid="stMetric"],
    div[data-testid="stExpander"],
    div.stDataFrame {
        border: 2px solid #FFE600 !important;
        border-radius: 4px !important;
        background-color: #0E1422 !important;
    }

    div.stDataFrame [data-testid="stTable"] td, 
    div.stDataFrame [role="gridcell"] {
        color: #FFFFFF !important;
        font-weight: normal !important;
    }
    div.stDataFrame [role="columnheader"] {
        color: #FFE600 !important;
        font-weight: bold !important;
    }

    /* 7. КНОПКИ ФОРМИ */
    .stButton > button, 
    div[data-testid="stFormSubmitButton"] > button {
        border: 2px solid #FFE600 !important;
        color: #000000 !important;
        background-color: #FFE600 !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border-radius: 3px !important;
        width: 100% !important;
    }

    .stButton > button:hover, 
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #000000 !important;
        color: #FFE600 !important;
    }

    div[role="radiogroup"] label {
        border: 1px solid #FFE600 !important;
        padding: 8px 12px !important;
        margin-bottom: 6px !important;
        border-radius: 3px !important;
        background-color: #121826 !important;
        color: #FFE600 !important;
    }
</style>
"""
st.markdown(cbrn_style, unsafe_allow_html=True)

# --- 4. ГОЛОВНИЙ ЗАГОЛОВОК ---
st.title("Система обліку індивідуальних доз опромінення (ІДК)")
st.markdown("---")

# --- 5. БОКОВА ПАНЕЛЬ ТА НАВІГАЦІЯ ---
st.sidebar.subheader("ПАНЕЛЬ УПРАВЛІННЯ")

menu = st.sidebar.radio(
    label="Навігація",
    options=[
        "Особовий склад",
        "Внесення доз",
        "Журнал обліку доз за рік",
        "Багаторічний облік доз",
        "Пошук та аналітика"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.subheader("АДМІНІСТРУВАННЯ")

def logout_admin():
    st.session_state["admin_pass"] = ""

if "admin_pass" not in st.session_state:
    st.session_state["admin_pass"] = ""

st.sidebar.markdown("Для редагування або видалення даних введіть пароль:")
admin_password_input = st.sidebar.text_input("Пароль адміністратора", type="password", key="admin_pass")

IS_ADMIN = (st.session_state["admin_pass"] == "admin123")

if IS_ADMIN:
    st.sidebar.success("РЕЖИМ АДМІНІСТРАТОРА АКТИВОВАНО")
    st.sidebar.button("ВИЙТИ З РЕЖИМУ АДМІНІСТРАТОРА", on_click=logout_admin)
else:
    if st.session_state["admin_pass"] != "":
        st.sidebar.error("НЕВІРНИЙ ПАРОЛЬ")

# --- 6. РОЗДІЛ 1: ОСОБОВИЙ СКЛАД ---
if menu == "Особовий склад":
    st.subheader("РЕЄСТР ОСОБОВОГО СКЛАДУ")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Додати співробітника")
        with st.form("add_person_form"):
            name = st.text_input("Прізвище, ім'я та по батькові")
            pos = st.text_input("Посада")
            start_yr = st.number_input("Рік початку обліку", min_value=1970, max_value=2050, value=datetime.now().year)
            
            submit = st.form_submit_button("ЗБЕРЕГТИ ОСОБУ")
            if submit:
                if name and pos:
                    add_person(name, pos, start_year=start_yr)
                    st.success(f"Запис {name} успішно створено!")
                    st.rerun()
                else:
                    st.warning("Заповніть усі обов'язкові поля!")
                    
    with col2:
        if IS_ADMIN:
            st.markdown("### Коригування / Видалення (АДМІН)")
            df_persons = get_personnel()
            if not df_persons.empty:
                person_options = {f"ID: {r['id']} | {r['full_name']}": r['id'] for _, r in df_persons.iterrows()}
                selected_p_str = st.selectbox("Оберіть особу для редагування", list(person_options.keys()))
                selected_p_id = person_options[selected_p_str]
                
                person_data = df_persons[df_persons['id'] == selected_p_id].iloc[0]
                
                with st.form("edit_person_form"):
                    edit_name = st.text_input("ПІБ", value=person_data['full_name'])
                    edit_pos = st.text_input("Посада", value=person_data['position'])
                    edit_start_yr = st.number_input("Рік початку", min_value=1970, max_value=2050, value=int(person_data['start_year']))
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        btn_update = st.form_submit_button("ОНОВИТИ ДАНІ")
                    with col_btn2:
                        btn_delete = st.form_submit_button("ВИДАЛИТИ ОСОБУ")
                        
                    if btn_update:
                        update_person(selected_p_id, edit_name, edit_pos, start_year=edit_start_yr)
                        st.success("Дані особи оновлено!")
                        st.rerun()
                    if btn_delete:
                        delete_person(selected_p_id)
                        st.warning("Особу та всі її вимірювання видалено!")
                        st.rerun()

    st.markdown("---")
    st.markdown("### Повний список зареєстрованого персоналу")
    df_persons = get_personnel()
    if not df_persons.empty:
        st.dataframe(
            df_persons[['id', 'full_name', 'position', 'start_year']].rename(columns={
                'id': 'ID', 'full_name': 'ПІБ', 'position': 'Посада', 'start_year': 'Рік початку'
            }), 
            height=320, 
            use_container_width=True
        )

# --- 7. РОЗДІЛ 2: ВНЕСЕННЯ ДОЗ ---
elif menu == "Внесення доз":
    st.subheader("ВНЕСЕННЯ ТА КОРИГУВАННЯ ВИМІРЮВАНЬ ДОЗ")
    
    df_persons = get_personnel()
    if df_persons.empty:
        st.warning("База даних особового складу порожня! Спочатку додайте осіб у розділі 'Особовий склад'.")
    else:
        col_in1, col_in2 = st.columns([1, 1])
        
        with col_in1:
            st.markdown("### Внести нове вимірювання")
            person_dict = {f"{row['full_name']} ({row['position']})": row['id'] for _, row in df_persons.iterrows()}
            
            with st.form("add_dose_form"):
                selected_person_str = st.selectbox("Співробітник", list(person_dict.keys()))
                person_id = person_dict[selected_person_str]
                
                m_date = st.date_input("Дата вимірювання", value=date.today())
                dose = st.number_input("Отримана доза (мЗв)", min_value=0.0, max_value=500.0, value=0.0, step=0.001, format="%.3f")
                
                submit_dose = st.form_submit_button("ЗАПИСАТИ ДОЗУ")
                if submit_dose:
                    add_measurement(person_id, m_date.strftime("%Y-%m-%d"), dose)
                    st.success("Запис успішно додано!")
                    st.rerun()

        with col_in2:
            if IS_ADMIN:
                st.markdown("### Коригувати/Видалити вимірювання (АДМІН)")
                df_m = get_all_measurements()
                if not df_m.empty:
                    meas_dict = {f"ID:{r['measurement_id']} | {r['measurement_date']} | {r['full_name']} ({r['dose_msv']} мЗв)": r['measurement_id'] for _, r in df_m.iterrows()}
                    selected_m_str = st.selectbox("Обрати запис вимірювання", list(meas_dict.keys()))
                    selected_m_id = meas_dict[selected_m_str]
                    
                    meas_data = df_m[df_m['measurement_id'] == selected_m_id].iloc[0]
                    
                    with st.form("edit_meas_form"):
                        e_date = st.date_input("Дата", value=datetime.strptime(meas_data['measurement_date'], "%Y-%m-%d").date())
                        e_dose = st.number_input("Доза (мЗв)", min_value=0.0, max_value=500.0, value=float(meas_data['dose_msv']), step=0.001, format="%.3f")
                        
                        m_btn1, m_btn2 = st.columns(2)
                        with m_btn1:
                            btn_m_update = st.form_submit_button("ОНОВИТИ ЗАПИС")
                        with m_btn2:
                            btn_m_delete = st.form_submit_button("ВИДАЛИТИ ЗАПИС")
                            
                        if btn_m_update:
                            update_measurement(selected_m_id, int(meas_data['person_id']), e_date.strftime("%Y-%m-%d"), e_dose)
                            st.success("Вимірювання оновлено!")
                            st.rerun()
                        if btn_m_delete:
                            delete_measurement(selected_m_id)
                            st.warning("Запис вимірювання видалено!")
                            st.rerun()

    st.markdown("---")
    st.markdown("### Останні внесені вимірювання")
    df_m = get_all_measurements()
    if not df_m.empty:
        st.dataframe(df_m[['measurement_id', 'measurement_date', 'full_name', 'position', 'dose_msv']].rename(columns={
            'measurement_id': 'ID запису', 'measurement_date': 'Дата', 
            'full_name': 'ПІБ', 'position': 'Посада', 'dose_msv': 'Доза (мЗв)'
        }), height=300, use_container_width=True)

# --- 8. РОЗДІЛ 3: ЖУРНАЛ ОБЛІКУ ДОЗ ЗА РІК ---
elif menu == "Журнал обліку доз за рік":
    st.subheader("ЖУРНАЛ ОБЛІКУ ІНДИВІДУАЛЬНИХ ДОЗ ЗА РІК")
    
    with get_connection() as conn:
        archived_years_df = pd.read_sql("SELECT year, archived_at FROM annual_archives", conn)
    archived_years = set(archived_years_df['year'].tolist()) if not archived_years_df.empty else set()

    col_hdr1, col_hdr2 = st.columns([1, 2])
    with col_hdr1:
        selected_year = st.selectbox("Оберіть рік звітності", range(datetime.now().year, 1970, -1))
    
    is_archived = selected_year in archived_years
    
    with col_hdr2:
        if is_archived:
            arch_date = archived_years_df[archived_years_df['year'] == selected_year]['archived_at'].iloc[0]
            st.success(f"СТАТУС: ЖУРНАЛ ЗА {selected_year} РІК ЗАРЕЄСТРОВАНО ТА ЗААРХІВОВАНО ({arch_date})")
        else:
            st.info("СТАТУС: АКТИВНИЙ РІК (автоматичний підрахунок)")

    df_m = get_all_measurements()
    if not df_m.empty:
        df_year = df_m[df_m['year'] == str(selected_year)]
        
        if not df_year.empty:
            summary_records = []
            grouped = df_year.groupby('person_id')
            
            idx = 1
            for person_id, group in grouped:
                person_name = group['full_name'].iloc[0]
                position = group['position'].iloc[0]
                
                sorted_group = group.sort_values('measurement_date')
                dates_doses = "\n".join([f"{r['measurement_date']}: {r['dose_msv']} мЗв" for _, r in sorted_group.iterrows()])
                
                total_year_dose = group['dose_msv'].sum()
                
                summary_records.append({
                    "№ з/п": idx,
                    "Прізвище, ім’я та по батькові": person_name,
                    "Посада": position,
                    "Дози, отримані протягом року": dates_doses,
                    "Записів": len(group),
                    "Сумарна доза за рік (мЗв)": f"{total_year_dose:.3f}",
                    "_raw_sum": total_year_dose
                })
                idx += 1
            
            df_report = pd.DataFrame(summary_records)
            
            coll_dose = df_report['_raw_sum'].sum()
            st.markdown(f"**Всього осіб:** {len(df_report)} | **Колективна доза підрозділу за {selected_year} рік:** `{coll_dose:.3f} люд.-мЗв`")
            
            df_display = df_report.drop(columns=['_raw_sum'])
            st.dataframe(
                df_display, 
                height=450, 
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                csv_data = df_display.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label=f"ЗАВАНТАЖИТИ ОФІЦІЙНИЙ ЗВІТ ЗА {selected_year} РІК (CSV)",
                    data=csv_data,
                    file_name=f"Journal_IDK_{selected_year}_Archived.csv",
                    mime="text/csv"
                )
            
            with col_b2:
                if not is_archived:
                    if st.button(f"ЗАФІКСУВАТИ ТА ЗААРХІВУВАТИ ЖУРНАЛ ЗА {selected_year} РІК"):
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                        with get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT OR REPLACE INTO annual_archives (year, archived_at, total_people, collective_dose) VALUES (?, ?, ?, ?)",
                                (selected_year, now_str, len(df_report), coll_dose)
                            )
                            conn.commit()
                        st.success(f"Журнал за {selected_year} рік зафіксовано в архіві!")
                        st.rerun()
                else:
                    st.caption("Цей рік уже збережено в постійному архіві.")
        else:
            st.info(f"За {selected_year} рік дані вимірювань відсутні.")

# --- 9. РОЗДІЛ 4: БАГАТОРІЧНИЙ ОБЛІК ДОЗ ---
elif menu == "Багаторічний облік доз":
    st.subheader("НАКОПИЧЕНІ ДОЗИ ЗА БАГАТОРІЧНИЙ ПЕРІОД (2–50 РОКІВ)")
    
    df_m = get_all_measurements()
    if not df_m.empty:
        df_m['year_int'] = df_m['measurement_date'].apply(lambda x: int(x.split('-')[0]))
        min_yr = int(df_m['year_int'].min())
        max_yr = int(df_m['year_int'].max())
        
        col_y1, col_y2 = st.columns(2)
        with col_y1:
            start_period = st.number_input("Початковий рік", min_value=1970, max_value=max_yr, value=min_yr)
        with col_y2:
            end_period = st.number_input("Кінцевий рік", min_value=start_period, max_value=2070, value=max_yr)
            
        period_len = end_period - start_period + 1
        st.warning(f"ОБРАНО ІНТЕРВАЛ СПОСТЕРЕЖЕННЯ: {period_len} РОКІВ ({start_period} – {end_period})")
        
        df_filtered = df_m[(df_m['year_int'] >= start_period) & (df_m['year_int'] <= end_period)]
        
        if not df_filtered.empty:
            multiyear_summary = df_filtered.groupby(['person_id', 'full_name', 'position']).agg(
                total_accumulated_dose=('dose_msv', 'sum'),
                avg_annual_dose=('dose_msv', lambda x: x.sum() / period_len),
                max_single_dose=('dose_msv', 'max')
            ).reset_index()
            
            multiyear_summary['total_accumulated_dose'] = multiyear_summary['total_accumulated_dose'].round(3)
            multiyear_summary['avg_annual_dose'] = multiyear_summary['avg_annual_dose'].round(3)
            
            st.dataframe(multiyear_summary.rename(columns={
                'full_name': 'ПІБ', 'position': 'Посада',
                'total_accumulated_dose': f'Накопичено за {period_len} р. (мЗв)',
                'avg_annual_dose': 'Середньорічна (мЗв)',
                'max_single_dose': 'Макс. разова (мЗв)'
            }), height=300, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### ДИНАМІКА ОПРОМІНЕННЯ ОСОБИ")
            selected_person = st.selectbox("Обрати особу для побудови графіку", multiyear_summary['full_name'].unique())
            
            person_history = df_filtered[df_filtered['full_name'] == selected_person]
            annual_trend = person_history.groupby('year_int')['dose_msv'].sum().reset_index()
            
            st.line_chart(annual_trend.set_index('year_int')['dose_msv'])

# --- 10. РОЗДІЛ 5: ПОШУК ТА АНАЛІТИКА ---
elif menu == "Пошук та аналітика":
    st.subheader("ПОШУК ТА ФІЛЬТРАЦІЯ (ПІБ, ТЕРМІН, ДОЗА)")
    
    df_m = get_all_measurements()
    if not df_m.empty:
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            search_name = st.text_input("Пошук за ПІБ")
        with col_f2:
            date_from = st.date_input("З дати", value=date(2000, 1, 1))
            date_to = st.date_input("По дату", value=date.today())
        with col_f3:
            min_dose_threshold = st.number_input("Поріг дози перевищення (мЗв)", min_value=0.0, value=0.0, step=0.1)
            
        filtered_df = df_m.copy()
        filtered_df['measurement_date_dt'] = pd.to_datetime(filtered_df['measurement_date'])
        
        if search_name:
            filtered_df = filtered_df[filtered_df['full_name'].str.contains(search_name, case=False, na=False)]
            
        filtered_df = filtered_df[
            (filtered_df['measurement_date_dt'].dt.date >= date_from) & 
            (filtered_df['measurement_date_dt'].dt.date <= date_to)
        ]
        
        if min_dose_threshold > 0:
            filtered_df = filtered_df[filtered_df['dose_msv'] >= min_dose_threshold]
            
        st.markdown(f"**Знайдено збігів:** {len(filtered_df)}")
        st.dataframe(filtered_df[['measurement_date', 'full_name', 'position', 'dose_msv']].rename(columns={
            'measurement_date': 'Дата', 'full_name': 'ПІБ', 
            'position': 'Посада', 'dose_msv': 'Доза (мЗв)'
        }), height=350, use_container_width=True)
