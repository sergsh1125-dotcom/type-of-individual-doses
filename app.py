import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, date

# --- 1. НАЛАШТУВАННЯ БАЗИ ДАНИХ (SQLite) ---
DB_NAME = "radiation_control.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        # Таблиця особового складу
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personnel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                position TEXT NOT NULL,
                category TEXT DEFAULT 'Категорія А',
                start_year INTEGER NOT NULL
            )
        ''')
        # Таблиця вимірювань доз
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

# --- 2. ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ РОБОТИ З ДАНИМИ ---
def get_personnel():
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM personnel ORDER BY full_name", conn)

def add_person(full_name, position, category, start_year):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO personnel (full_name, position, category, start_year) VALUES (?, ?, ?, ?)",
            (full_name, position, category, start_year)
        )
        conn.commit()

def add_measurement(person_id, measurement_date, dose_msv):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO measurements (person_id, measurement_date, dose_msv) VALUES (?, ?, ?)",
            (person_id, measurement_date, dose_msv)
        )
        conn.commit()

def get_all_measurements():
    with get_connection() as conn:
        query = '''
            SELECT 
                m.id AS measurement_id,
                p.id AS person_id,
                p.full_name,
                p.position,
                p.category,
                m.measurement_date,
                m.dose_msv,
                strftime('%Y', m.measurement_date) AS year
            FROM measurements m
            JOIN personnel p ON m.person_id = p.id
            ORDER BY m.measurement_date DESC
        '''
        return pd.read_sql(query, conn)

# --- 3. НАЛАШТУВАННЯ ІНТЕРФЕЙСУ STREAMLIT ---
st.set_page_config(page_title="Система ІДК та Багаторічного Обліку", layout="wide")

st.title("🛡️ Система обліку індивідуальних доз опромінення (ІДК)")
st.caption("Автоматизація Журналу ІДК та аналіз накопичених доз за 2–50 років")

menu = st.sidebar.radio(
    "Навігація по системі:",
    [
        "👥 Особовий склад",
        "📝 Введення вимірювань",
        "📅 Річний журнал (Додаток 3)",
        "📊 Багаторічний облік (2-50 років)",
        "🔍 Гнучкий пошук та аналітика"
    ]
)

# --- 4. РАЗДІЛ 1: ОСОБОВИЙ СКЛАД ---
if menu == "👥 Особовий склад":
    st.subheader("Реєстр особового складу")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Додати співробітника")
        with st.form("add_person_form"):
            name = st.text_input("Прізвище, ім'я та по батькові")
            pos = st.text_input("Посада")
            cat = st.selectbox("Категорія опромінюваних", ["Категорія А", "Категорія Б"])
            start_yr = st.number_input("Рік початку обліку", min_value=1970, max_value=2050, value=datetime.now().year)
            
            submit = st.form_submit_button("Зберегти особа")
            if submit:
                if name and pos:
                    add_person(name, pos, cat, start_yr)
                    st.success(f"Співробітника {name} додано успішно!")
                    st.rerun()
                else:
                    st.warning("Заповніть усі поля!")
                    
    with col2:
        st.markdown("### Список зареєстрованих осіб")
        df_persons = get_personnel()
        if not df_persons.empty:
            st.dataframe(df_persons.rename(columns={
                'id': 'ID', 'full_name': 'ПІБ', 'position': 'Посада', 
                'category': 'Категорія', 'start_year': 'Рік початку'
            }), use_container_width=True)
        else:
            st.info("База даних особового складу порожня.")

# --- 5. РАЗДІЛ 2: ВВЕДЕННЯ ВИМІРЮВАНЬ ---
elif menu == "📝 Введення вимірювань":
    st.subheader("Внесення нових даних вимірювання дози")
    
    df_persons = get_personnel()
    if df_persons.empty:
        st.warning("Спочатку додайте співробітників у розділі 'Особовий склад'!")
    else:
        person_dict = {f"{row['full_name']} ({row['position']})": row['id'] for _, row in df_persons.iterrows()}
        
        with st.form("add_dose_form"):
            selected_person_str = st.selectbox("Оберіть співробітника", list(person_dict.keys()))
            person_id = person_dict[selected_person_str]
            
            m_date = st.date_input("Дата вимірювання", value=date.today())
            dose = st.number_input("Отримана доза (в мЗв)", min_value=0.0, max_value=500.0, value=0.0, step=0.01, format="%.3f")
            
            submit_dose = st.form_submit_button("Записати дозу")
            if submit_dose:
                add_measurement(person_id, m_date.strftime("%Y-%m-%d"), dose)
                st.success("Вимірювання успішно збережено в Журналі!")
                st.rerun()

        st.subheader("Останні внесені вимірювання")
        df_m = get_all_measurements()
        if not df_m.empty:
            st.dataframe(df_m[['measurement_date', 'full_name', 'position', 'dose_msv']].head(10).rename(columns={
                'measurement_date': 'Дата', 'full_name': 'ПІБ', 
                'position': 'Посада', 'dose_msv': 'Доза (мЗв)'
            }), use_container_width=True)

# --- 6. РАЗДІЛ 3: РІЧНИЙ ЖУРНАЛ (ДОДАТОК 3) ---
elif menu == "📅 Річний журнал (Додаток 3)":
    st.subheader("Журнал обліку індивідуальних доз зовнішнього опромінення за рік")
    
    selected_year = st.selectbox("Оберіть рік для формування звіту", range(datetime.now().year, 1970, -1))
    
    df_m = get_all_measurements()
    if not df_m.empty:
        df_year = df_m[df_m['year'] == str(selected_year)]
        
        if not df_year.empty:
            # Консолідація даних у формат Додатка 3
            summary_records = []
            grouped = df_year.groupby('person_id')
            
            idx = 1
            for person_id, group in grouped:
                person_name = group['full_name'].iloc[0]
                position = group['position'].iloc[0]
                
                # Формуємо список дат і вимірювань
                dates_doses = ", ".join([f"{row['measurement_date']}: {row['dose_msv']} мЗв" for _, row in group.iterrows()])
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
            st.dataframe(df_report, use_container_width=True)
            
            # Завантаження звіту
            csv = df_report.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="💾 Завантажити Журнал за рік (CSV)",
                data=csv,
                file_name=f"Journal_IDK_{selected_year}.csv",
                mime="text/csv"
            )
        else:
            st.info(f"За {selected_year} рік записи про вимірювання відсутні.")
    else:
        st.info("База вимірювань порожня.")

# --- 7. РАЗДІЛ 4: БАГАТО РІЧНИЙ ОБЛІК (2-50 РОКІВ) ---
elif menu == "📊 Багаторічний облік (2-50 років)":
    st.subheader("Аналіз накопиченого опромінення за багаторічні періоди")
    
    df_m = get_all_measurements()
    if df_m.empty:
        st.info("Дані про вимірювання відсутні.")
    else:
        df_m['year_int'] = df_m['measurement_date'].apply(lambda x: int(x.split('-')[0]))
        min_yr = int(df_m['year_int'].min())
        max_yr = int(df_m['year_int'].max())
        
        st.markdown("#### Налаштування часового інтервалу розрахунку")
        col_y1, col_y2 = st.columns(2)
        with col_y1:
            start_period = st.number_input("Початковий рік", min_value=1970, max_value=max_yr, value=min_yr)
        with col_y2:
            end_period = st.number_input("Кінцевий рік", min_value=start_period, max_value=2070, value=max_yr)
            
        period_len = end_period - start_period + 1
        st.info(f"🗓️ Обрано період: **{period_len} років/рік** (з {start_period} по {end_period} рік)")
        
        # Фільтрація за інтервалом
        df_filtered = df_m[(df_m['year_int'] >= start_period) & (df_m['year_int'] <= end_period)]
        
        if not df_filtered.empty:
            # Обчислення накопиченої дози за період
            multiyear_summary = df_filtered.groupby(['person_id', 'full_name', 'position', 'category']).agg(
                total_accumulated_dose=('dose_msv', 'sum'),
                avg_annual_dose=('dose_msv', lambda x: x.sum() / period_len),
                max_single_dose=('dose_msv', 'max')
            ).reset_index()
            
            multiyear_summary['total_accumulated_dose'] = multiyear_summary['total_accumulated_dose'].round(3)
            multiyear_summary['avg_annual_dose'] = multiyear_summary['avg_annual_dose'].round(3)
            
            st.markdown("### Зведена таблиці накопичених доз")
            st.dataframe(multiyear_summary.rename(columns={
                'full_name': 'ПІБ', 'position': 'Посада', 'category': 'Категорія',
                'total_accumulated_dose': f'Сумарна доза за {period_len} р. (мЗв)',
                'avg_annual_dose': 'Середньорічна доза (мЗв)',
                'max_single_dose': 'Макс. разова доза (мЗв)'
            }), use_container_width=True)
            
            # Візуалізація для окремого співробітника
            st.markdown("---")
            st.markdown("### 📈 Динаміка накопичення дози конкретної особи")
            
            selected_person = st.selectbox("Оберіть особу для детального графіка", multiyear_summary['full_name'].unique())
            
            person_history = df_filtered[df_filtered['full_name'] == selected_person]
            annual_trend = person_history.groupby('year_int')['dose_msv'].sum().reset_index()
            
            # Побудова графіка
            st.line_chart(annual_trend.set_index('year_int')['dose_msv'])
            st.caption("Шкала X — Роки, Шкала Y — Річна доза у мЗв")

# --- 8. РАЗДІЛ 5: ГНУЧКИЙ ПОШУК ТА АНАЛІТИКА ---
elif menu == "🔍 Гнучкий пошук та аналітика":
    st.subheader("Пошук інформації за критеріями (ПІБ, термін, порогові дози)")
    
    df_m = get_all_measurements()
    if not df_m.empty:
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            search_name = st.text_input("🔍 Пошук за ПІБ (частковий збіг)")
        with col_f2:
            date_from = st.date_input("Дата З", value=date(2000, 1, 1))
            date_to = st.date_input("Дата ПО", value=date.today())
        with col_f3:
            min_dose_threshold = st.number_input("⚠️ Фільтр: доза вища ніж (мЗв)", min_value=0.0, value=0.0, step=0.1)
            
        # Застосування фільтрів
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
            
        st.markdown(f"**Знайдено записів:** {len(filtered_df)}")
        st.dataframe(filtered_df[['measurement_date', 'full_name', 'position', 'dose_msv']].rename(columns={
            'measurement_date': 'Дата', 'full_name': 'ПІБ', 
            'position': 'Посада', 'dose_msv': 'Доза (мЗв)'
        }), use_container_width=True)
