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

# --- 3. НАЛАШТУВАННЯ СТИЛЮ ---
st.set_page_config(page_title="Система ІДК", layout="wide")

cbrn_style = """
<style>
    header[data-testid="stHeader"] {
        display: none !important;
    }
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}

    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 0.5rem !important;
    }

    .stApp {
        background-color: #0B101D;
        color: #FFE600 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    h1, h2, h3, label, .stMarkdown, p, span {
        color: #FFE600 !important;
        font-weight: bold !important;
    }

    input, select, textarea, div[data-baseweb="select"] {
        border: 1px solid #FFE600 !important;
        color: #FFFFFF !important;
        background-color: #121826 !important;
        font-size: 16px !important;
        border-radius: 3px !important;
    }
    input::placeholder {
        color: #888888 !important;
    }

    div[data-baseweb="select"] span, div[data-baseweb="select"] input {
        color: #FFFFFF !important;
    }

    div[data-testid="stForm"], 
    div[data-testid="stMetric"],
    div[data-testid="stExpander"] {
        border: 2px solid #FFE600 !important;
        border-radius: 4px !important;
        padding: 12px !important;
        background-color: #0E1422 !important;
    }

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

    section[data-testid="stSidebar"] {
        border-right: 5px double #FFE600 !important;
        background-color: #0E1422 !important;
    }

    .stButton>button {
        border: 2px solid #FFE600 !important;
        color: #000000 !important;
        background-color: #FFE600 !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border-radius: 3px !important;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #000000 !important;
        color: #FFE600 !important;
        border: 2px solid #FFE600 !important;
    }

    div[role="radiogroup"] label {
        border: 1px solid #FFE600 !important;
        padding: 6px 10px !important;
        margin-bottom: 4px !important;
        border-radius: 3px !important;
        color: #FFE600 !important;
    }
</style>
"""
st.markdown(cbrn_style, unsafe_allow_html=True)

# --- 4. ГОЛОВНИЙ ЗАГОЛОВОК СИСТЕМИ ---
st.title("Система обліку індивідуальних доз опромінення (ІДК)")
st.markdown("---")

# --- 5. БОКОВА ПАНЕЛЬ ТА АВТОРИЗАЦІЯ ---
st.sidebar.subheader("ПАНЕЛЬ УПРАВЛІННЯ")

menu = st.sidebar.radio(
    label="",
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

# Функція виходу через callback для уникнення помилки StreamlitWidgetAlreadyInstantiatedError
def logout_admin():
    st.session_state["admin_pass"] = ""

if "admin_pass" not in st.session_state:
    st.session_state["admin_pass"] = ""

st.sidebar.markdown("Для редагування або видалення даних введіть пароль адміністратора у панелі нижче:")
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
        st.warning("База даних особового складу порожня!")
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
    
    selected_year = st.selectbox("Оберіть рік звітності", range(datetime.now().year, 1970, -1))
    
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
                
                dates_doses = "; ".join([f"{row['measurement_date']}: {row['dose_msv']}мЗв" for _, row in group.iterrows()])
                total_year_dose = group['dose_msv'].sum()
                
                summary_records.append({
                    "№ з/п": idx,
                    "Прізвище, ім’я та по батькові": person_name,
                    "Посада": position,
                    "Дози за датами вимірювання (в мЗв)": dates_doses,
                    "Сумарна доза за рік (в мЗв)": round(total_year_dose, 3)
                })
                idx += 1
            
            df_report = pd.DataFrame(summary_records)
            st.dataframe(df_report, height=350, use_container_width=True)
            
            csv = df_report.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="ЕКСПОРТУВАТИ ЖУРНАЛ ЗА РІК (CSV)",
                data=csv,
                file_name=f"Journal_IDK_{selected_year}.csv",
                mime="text/csv"
            )
        else:
            st.info(f"За {selected_year} рік дані відсутні.")

# --- 9. РОЗДІЛ 4: БАГАТО РІЧНИЙ ОБЛІК ДОЗ ---
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
