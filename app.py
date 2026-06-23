import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import json

#Инициализация Firebase
if not firebase_admin._apps:
    # Способ 1: Streamlit Cloud — ключ хранится в Secrets
    if "firebase" in st.secrets:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    # Способ 2: локальный запуск — ключ лежит рядом с app.py
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    else:
        st.error("Ошибка: ключ Firebase не найден. Добавьте serviceAccountKey.json или настройте Secrets.")
        st.stop()

db = firestore.client()

# Настройки страницы
st.set_page_config(page_title="Питание и успеваемость", page_icon="🥗", layout="centered")

st.title("🥗 Питание и успеваемость студентов")
st.markdown(
    "Анонимный опрос для учебного проекта. "
    "Все ответы используются исключительно в образовательных целях."
)
st.divider()

# Форма опроса
with st.form("survey_form"):
    st.subheader("Раздел 1 — Общая информация")

    age = st.number_input("Ваш возраст", min_value=14, max_value=60, step=1, value=20)
    course = st.selectbox(
        "Курс обучения",
        ["1 курс", "2 курс", "3 курс", "4 курс", "5 курс / магистратура"]
    )
    avg_grade = st.select_slider(
        "Ваша средняя успеваемость",
        options=["Неудовлетворительно", "Удовлетворительно", "Хорошо", "Отлично"]
    )

    st.divider()
    st.subheader("Раздел 2 — Режим питания")

    meals_per_day = st.radio(
        "Сколько раз в день вы обычно едите?",
        ["1 раз", "2 раза", "3 раза", "4 раза и более"]
    )
    skip_breakfast = st.radio(
        "Как часто вы пропускаете завтрак?",
        ["Никогда", "Редко (1–2 раза в неделю)", "Часто (3–4 раза в неделю)", "Почти всегда"]
    )
    eat_schedule = st.radio(
        "Придерживаетесь ли вы режима питания (едите примерно в одно и то же время)?",
        ["Да, всегда", "Стараюсь, но не всегда получается", "Нет, ем когда придётся"]
    )

    st.divider()
    st.subheader("Раздел 3 — Фастфуд и нездоровое питание")

    fastfood_freq = st.radio(
        "Как часто вы едите фастфуд (бургеры, пицца, шаурма и т.п.)?",
        ["Не ем совсем", "Реже 1 раза в неделю", "1–2 раза в неделю", "3 и более раз в неделю"]
    )
    fastfood_reason = st.multiselect(
        "Если едите фастфуд — почему? (можно несколько вариантов)",
        ["Быстро и удобно", "Нет времени готовить", "Дешевле", "Вкусно", "Нет альтернативы рядом", "Не ем фастфуд"]
    )
    drinks = st.multiselect(
        "Какие напитки вы чаще всего употребляете в течение дня?",
        ["Вода", "Чай / кофе", "Энергетики", "Сладкая газировка", "Соки", "Другое"]
    )

    st.divider()
    st.subheader("Раздел 4 — Влияние питания на концентрацию и учёбу")

    concentration = st.slider(
        "Как вы оцениваете свою концентрацию на занятиях в течение дня? (1 — очень плохо, 10 — отлично)",
        min_value=1, max_value=10, value=5
    )
    food_effect = st.radio(
        "Замечаете ли вы связь между тем, что вы съели, и вашей продуктивностью?",
        ["Да, явно замечаю", "Иногда замечаю", "Нет, не замечаю", "Никогда не задумывался(ась)"]
    )
    worst_time = st.radio(
        "В какое время суток вам труднее всего сосредоточиться?",
        ["Утром (до обеда)", "После обеда (сонливость)", "Вечером", "Не зависит от времени"]
    )
    improvement = st.multiselect(
        "Что, по-вашему, больше всего мешает правильно питаться в период учёбы?",
        ["Нехватка времени", "Финансовые ограничения", "Нет возможности готовить", "Лень", "Отсутствие знаний о правильном питании", "Столовая / кафе с плохим выбором"]
    )

    comment = st.text_area("Дополнительные комментарии (необязательно)", height=80)

    st.markdown("")
    submitted = st.form_submit_button("📨 Отправить ответ", use_container_width=True)

# Сохранение в Firebase
if submitted:
    if not drinks and not fastfood_reason:
        st.warning("Пожалуйста, выберите хотя бы один вариант в вопросах с множественным выбором.")
    else:
        record = {
            "age": int(age),
            "course": course,
            "avg_grade": avg_grade,
            "meals_per_day": meals_per_day,
            "skip_breakfast": skip_breakfast,
            "eat_schedule": eat_schedule,
            "fastfood_freq": fastfood_freq,
            "fastfood_reason": fastfood_reason,
            "drinks": drinks,
            "concentration": int(concentration),
            "food_effect": food_effect,
            "worst_time": worst_time,
            "improvement": improvement,
            "comment": comment,
            "timestamp": datetime.utcnow()
        }
        try:
            db.collection("nutrition_survey").add(record)
            st.success("✅ Спасибо! Ваш ответ успешно сохранён.")
            st.balloons()
        except Exception as e:
            st.error(f"Ошибка при сохранении: {e}")

#Аналитика
st.divider()
if st.checkbox("📊 Показать аналитику (для преподавателя)"):
    docs = db.collection("nutrition_survey").stream()
    data = [doc.to_dict() for doc in docs]

    if not data:
        st.info("Ответов пока нет.")
    else:
        df = pd.DataFrame(data)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        st.subheader("Сводная таблица ответов")
        st.dataframe(df.drop(columns=["timestamp", "comment"], errors="ignore"), use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Всего ответов", len(df))
        if "concentration" in df.columns:
            col2.metric("Средняя концентрация", f"{df['concentration'].mean():.1f} / 10")
        if "age" in df.columns:
            col3.metric("Средний возраст", f"{df['age'].mean():.1f} лет")

        st.divider()

        if "concentration" in df.columns:
            st.subheader("Распределение концентрации (1–10)")
            fig1 = px.histogram(df, x="concentration", nbins=10,
                                title="Самооценка концентрации студентов",
                                labels={"concentration": "Концентрация", "count": "Кол-во"},
                                color_discrete_sequence=["#5DCAA5"])
            st.plotly_chart(fig1, use_container_width=True)

        if "fastfood_freq" in df.columns:
            st.subheader("Частота употребления фастфуда")
            freq_counts = df["fastfood_freq"].value_counts().reset_index()
            freq_counts.columns = ["Частота", "Кол-во"]
            fig2 = px.bar(freq_counts, x="Частота", y="Кол-во",
                          title="Как часто студенты едят фастфуд",
                          color_discrete_sequence=["#7F77DD"])
            st.plotly_chart(fig2, use_container_width=True)

        if "avg_grade" in df.columns and "concentration" in df.columns:
            st.subheader("Концентрация по уровню успеваемости")
            grade_order = ["Неудовлетворительно", "Удовлетворительно", "Хорошо", "Отлично"]
            fig3 = px.box(df, x="avg_grade", y="concentration",
                          category_orders={"avg_grade": grade_order},
                          title="Концентрация vs успеваемость",
                          labels={"avg_grade": "Успеваемость", "concentration": "Концентрация"},
                          color_discrete_sequence=["#D85A30"])
            st.plotly_chart(fig3, use_container_width=True)

        if "skip_breakfast" in df.columns:
            st.subheader("Пропуск завтрака")
            breakfast_counts = df["skip_breakfast"].value_counts().reset_index()
            breakfast_counts.columns = ["Частота пропуска", "Кол-во"]
            fig4 = px.pie(breakfast_counts, names="Частота пропуска", values="Кол-во",
                          title="Как часто студенты пропускают завтрак",
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig4, use_container_width=True)

        if "food_effect" in df.columns:
            st.subheader("Замечают ли студенты влияние питания на продуктивность?")
            effect_counts = df["food_effect"].value_counts().reset_index()
            effect_counts.columns = ["Ответ", "Кол-во"]
            fig5 = px.bar(effect_counts, x="Ответ", y="Кол-во",
                          title="Связь питания и продуктивности",
                          color_discrete_sequence=["#378ADD"])
            st.plotly_chart(fig5, use_container_width=True)

        st.divider()
        csv = df.drop(columns=["timestamp"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Скачать данные (CSV)", data=csv,
                           file_name="nutrition_survey_results.csv", mime="text/csv")