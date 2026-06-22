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
    if "firebase" in st.secrets:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    else:
        st.error("Ошибка: ключ Firebase не найден. Добавьте serviceAccountKey.json или настройте Secrets.")
        st.stop()

db = firestore.client()

# Настройки страницы
st.set_page_config(page_title="Питание и успеваемость", page_icon="🥗", layout="wide")
st.title("🥗 Питание и успеваемость студентов")
st.markdown("Анонимный опрос для учебного проекта. Все ответы используются исключительно в образовательных целях.")
st.divider()

#Форма опроса 50 вопросов
with st.form("survey_form"):

    # БЛОК 1 — Общая информация (q1–q5)
    st.subheader("Блок 1 — Общая информация")
    col1, col2 = st.columns(2)
    with col1:
        q1 = st.number_input("1. Ваш возраст", min_value=14, max_value=60, step=1, value=20)
        q2 = st.selectbox("2. Курс обучения", ["1 курс", "2 курс", "3 курс", "4 курс", "5 курс / магистратура"])
        q3 = st.text_input("3. Ваш город")
    with col2:
        q4 = st.radio("4. Пол", ["Мужской", "Женский", "Предпочитаю не указывать"])
        q5 = st.select_slider("5. Средняя успеваемость", options=["Неудовлетворительно", "Удовлетворительно", "Хорошо", "Отлично"])

    st.divider()

    # БЛОК 2 — Режим питания (q6–q15)
    st.subheader("Блок 2 — Режим питания")
    col1, col2 = st.columns(2)
    with col1:
        q6  = st.radio("6. Сколько раз в день вы едите?", ["1 раз", "2 раза", "3 раза", "4 раза и более"])
        q7  = st.radio("7. Как часто вы пропускаете завтрак?", ["Никогда", "Редко (1–2 раза в неделю)", "Часто (3–4 раза в неделю)", "Почти всегда"])
        q8  = st.radio("8. Как часто вы пропускаете обед?", ["Никогда", "Редко", "Часто", "Почти всегда"])
        q9  = st.radio("9. Придерживаетесь ли вы режима питания?", ["Да, всегда", "Стараюсь, но не всегда", "Нет, ем когда придётся"])
        q10 = st.radio("10. В какое время вы обычно завтракаете?", ["До 8:00", "8:00–10:00", "После 10:00", "Не завтракаю"])
    with col2:
        q11 = st.radio("11. В какое время вы обычно ужинаете?", ["До 18:00", "18:00–20:00", "После 20:00", "Не ужинаю"])
        q12 = st.slider("12. Сколько часов проходит между первым и последним приёмом пищи?", 1, 16, 8)
        q13 = st.radio("13. Готовите ли вы еду самостоятельно?", ["Да, регулярно", "Иногда", "Почти никогда", "Никогда"])
        q14 = st.multiselect("14. Где чаще всего едите в течение учебного дня?", ["Дома", "Столовая вуза", "Кафе / ресторан", "Фастфуд", "Не ем в течение дня"])
        q15 = st.radio("15. Соблюдаете ли вы какую-либо диету или систему питания?", ["Нет", "Вегетарианство / веганство", "Правильное питание (ПП)", "Другая диета"])

    st.divider()

    # БЛОК 3 — Качество и состав питания (q16–q25)
    st.subheader("Блок 3 — Качество и состав питания")
    col1, col2 = st.columns(2)
    with col1:
        q16 = st.radio("16. Как часто вы едите овощи и фрукты?", ["Каждый день", "Несколько раз в неделю", "Редко", "Почти никогда"])
        q17 = st.radio("17. Как часто вы едите домашнюю еду?", ["Каждый день", "Несколько раз в неделю", "Редко", "Почти никогда"])
        q18 = st.radio("18. Как часто вы едите полуфабрикаты?", ["Каждый день", "Несколько раз в неделю", "Редко", "Никогда"])
        q19 = st.multiselect("19. Какие продукты составляют основу вашего рациона?", ["Крупы / макароны", "Мясо / рыба", "Овощи / фрукты", "Молочные продукты", "Выпечка / хлеб", "Фастфуд", "Сладкое"])
        q20 = st.radio("20. Считаете ли вы своё питание сбалансированным?", ["Да", "Скорее да", "Скорее нет", "Нет"])
    with col2:
        q21 = st.radio("21. Принимаете ли вы витамины или добавки?", ["Да, регулярно", "Иногда", "Нет"])
        q22 = st.slider("22. Оцените качество своего питания (1–10)", 1, 10, 5)
        q23 = st.radio("23. Следите ли вы за калорийностью пищи?", ["Да, считаю калории", "Иногда слежу примерно", "Нет, не слежу"])
        q24 = st.radio("24. Как часто вы едите сладкое и кондитерские изделия?", ["Каждый день", "Несколько раз в неделю", "Редко", "Никогда"])
        q25 = st.radio("25. Как часто вы едите жареную пищу?", ["Каждый день", "Несколько раз в неделю", "Редко", "Никогда"])

    st.divider()

    # БЛОК 4 — Фастфуд (q26–q33)
    st.subheader("Блок 4 — Фастфуд и перекусы")
    col1, col2 = st.columns(2)
    with col1:
        q26 = st.radio("26. Как часто вы едите фастфуд?", ["Не ем совсем", "Реже 1 раза в неделю", "1–2 раза в неделю", "3 и более раз в неделю"])
        q27 = st.multiselect("27. Почему едите фастфуд? (можно несколько)", ["Быстро и удобно", "Нет времени готовить", "Дешевле", "Вкусно", "Нет альтернативы рядом", "Не ем фастфуд"])
        q28 = st.radio("28. Как часто вы перекусываете между основными приёмами пищи?", ["Несколько раз в день", "1 раз в день", "Редко", "Никогда"])
        q29 = st.multiselect("29. Что чаще всего едите в качестве перекуса?", ["Фрукты", "Орехи", "Шоколад / конфеты", "Чипсы / сухарики", "Бутерброд", "Йогурт", "Ничего не перекусываю"])
    with col2:
        q30 = st.radio("30. Едите ли вы во время учёбы / лекций?", ["Да, часто", "Иногда", "Нет"])
        q31 = st.multiselect("31. Какие напитки пьёте в течение дня?", ["Вода", "Чай", "Кофе", "Энергетики", "Сладкая газировка", "Соки", "Другое"])
        q32 = st.radio("32. Сколько стаканов воды вы выпиваете в день?", ["Менее 2", "2–4", "5–7", "8 и более"])
        q33 = st.radio("33. Как часто вы пьёте энергетические напитки?", ["Каждый день", "Несколько раз в неделю", "Редко", "Никогда"])

    st.divider()

    # БЛОК 5 — Влияние на концентрацию и учёбу (q34–q43)
    st.subheader("Блок 5 — Влияние питания на концентрацию и учёбу")
    col1, col2 = st.columns(2)
    with col1:
        q34 = st.slider("34. Оцените свою концентрацию на занятиях (1–10)", 1, 10, 5)
        q35 = st.radio("35. Замечаете ли вы связь между питанием и продуктивностью?", ["Да, явно замечаю", "Иногда замечаю", "Нет, не замечаю", "Никогда не задумывался(ась)"])
        q36 = st.radio("36. В какое время суток вам труднее всего сосредоточиться?", ["Утром (до обеда)", "После обеда (сонливость)", "Вечером", "Не зависит от времени"])
        q37 = st.radio("37. Чувствуете ли вы сонливость после обеда?", ["Да, часто", "Иногда", "Редко", "Нет"])
        q38 = st.radio("38. Влияет ли пропуск завтрака на вашу успеваемость?", ["Да, значительно", "Незначительно", "Нет", "Не замечал(а)"])
    with col2:
        q39 = st.radio("39. Как вы себя чувствуете после еды в столовой / кафе?", ["Хорошо, бодро", "Нейтрально", "Тяжело, хочется спать", "Не хожу в столовую"])
        q40 = st.radio("40. Как часто вы испытываете усталость в течение учебного дня?", ["Постоянно", "Часто", "Иногда", "Редко"])
        q41 = st.radio("41. Связываете ли вы усталость с питанием?", ["Да", "Иногда", "Нет"])
        q42 = st.slider("42. Насколько вы удовлетворены своей успеваемостью? (1–10)", 1, 10, 5)
        q43 = st.radio("43. Улучшилась бы ваша успеваемость при правильном питании?", ["Да, значительно", "Немного улучшилась бы", "Вряд ли", "Нет"])

    st.divider()

    # БЛОК 6 — Барьеры и осведомлённость (q44–q50)
    st.subheader("Блок 6 — Барьеры и осведомлённость")
    col1, col2 = st.columns(2)
    with col1:
        q44 = st.multiselect("44. Что мешает питаться правильно в период учёбы?", ["Нехватка времени", "Финансовые ограничения", "Нет возможности готовить", "Лень", "Нет знаний о правильном питании", "Плохой выбор в столовой"])
        q45 = st.radio("45. Знаете ли вы основы правильного питания?", ["Да, хорошо знаю", "Знаю в общих чертах", "Знаю мало", "Не знаю"])
        q46 = st.radio("46. Где вы получаете информацию о питании?", ["Интернет / соцсети", "От врача / диетолога", "От родителей", "Из книг", "Нигде не получаю"])
        q47 = st.radio("47. Хотели бы вы улучшить своё питание?", ["Да, это важная цель", "Да, но не знаю как", "Возможно", "Нет, меня всё устраивает"])
    with col2:
        q48 = st.radio("48. Есть ли в вашем вузе удобные места для питания?", ["Да, и они хорошие", "Есть, но качество низкое", "Почти нет", "Нет совсем"])
        q49 = st.radio("49. Обсуждают ли в вашем вузе тему здорового питания?", ["Да, регулярно", "Иногда", "Очень редко", "Никогда"])
        q50 = st.text_area("50. Дополнительные комментарии или пожелания (необязательно)", height=80)

    st.markdown("")
    submitted = st.form_submit_button("📨 Отправить ответы", use_container_width=True)

#Сохранение в Firebase
if submitted:
    if not q3:
        st.warning("Пожалуйста, укажите ваш город (вопрос 3).")
    else:
        record = {
            "age": int(q1), "course": q2, "city": q3, "gender": q4, "avg_grade": q5,
            "meals_per_day": q6, "skip_breakfast": q7, "skip_lunch": q8,
            "eating_schedule": q9, "breakfast_time": q10, "dinner_time": q11,
            "hours_between_meals": int(q12), "cooks_self": q13, "eating_place": q14,
            "diet_type": q15, "eats_vegetables": q16, "eats_homefood": q17,
            "eats_processed": q18, "diet_base": q19, "diet_balanced": q20,
            "takes_vitamins": q21, "diet_quality": int(q22), "counts_calories": q23,
            "eats_sweets": q24, "eats_fried": q25, "fastfood_freq": q26,
            "fastfood_reason": q27, "snack_freq": q28, "snack_type": q29,
            "eats_during_class": q30, "drinks": q31, "water_glasses": q32,
            "energy_drinks": q33, "concentration": int(q34), "food_effect": q35,
            "hard_focus_time": q36, "after_lunch_sleepy": q37,
            "breakfast_skip_effect": q38, "feel_after_canteen": q39,
            "fatigue_freq": q40, "fatigue_linked_to_food": q41,
            "grade_satisfaction": int(q42), "grade_improve_with_food": q43,
            "barriers": q44, "nutrition_knowledge": q45, "info_source": q46,
            "wants_improve": q47, "canteen_quality": q48,
            "uni_discusses_nutrition": q49, "comment": q50,
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
        if "diet_quality" in df.columns:
            col3.metric("Средняя оценка питания", f"{df['diet_quality'].mean():.1f} / 10")

        st.divider()

        if "concentration" in df.columns:
            st.subheader("Распределение самооценки концентрации (1–10)")
            fig1 = px.histogram(df, x="concentration", nbins=10,
                                title="Концентрация студентов на занятиях",
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
            st.subheader("Частота пропуска завтрака")
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
                          title="Осознанность связи питания и продуктивности",
                          color_discrete_sequence=["#378ADD"])
            st.plotly_chart(fig5, use_container_width=True)

        if "diet_quality" in df.columns:
            st.subheader("Самооценка качества питания (1–10)")
            fig6 = px.histogram(df, x="diet_quality", nbins=10,
                                title="Как студенты оценивают своё питание",
                                labels={"diet_quality": "Качество питания", "count": "Кол-во"},
                                color_discrete_sequence=["#E8A838"])
            st.plotly_chart(fig6, use_container_width=True)

        if "eats_vegetables" in df.columns:
            st.subheader("Частота употребления овощей и фруктов")
            veg_counts = df["eats_vegetables"].value_counts().reset_index()
            veg_counts.columns = ["Частота", "Кол-во"]
            fig7 = px.pie(veg_counts, names="Частота", values="Кол-во",
                          title="Как часто студенты едят овощи и фрукты",
                          color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig7, use_container_width=True)

        st.divider()
        csv = df.drop(columns=["timestamp"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Скачать данные (CSV)", data=csv,
                           file_name="nutrition_survey_results.csv", mime="text/csv")
