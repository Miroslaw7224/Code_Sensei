# app.py
import streamlit as st
from openai import OpenAI
from dotenv import dotenv_values
import sqlite3
from datetime import datetime
import pandas as pd
import io
import os

def set_custom_style():
    st.markdown("""
        <style>
        .big-font {
            font-size:22px !important;
        }
        .small-font {
            font-size:14px !important;
            color: #888;
        }
        .highlight {
            background-color: #f0f2f6;
            padding: 0.3em 0.6em;
            border-radius: 0.4em;
        }
        </style>
    """, unsafe_allow_html=True)

set_custom_style()
# Tworzymy/otwieramy bazę
conn = sqlite3.connect("history.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    code TEXT,
    description TEXT,
    description_type TEXT,
    voice TEXT,
    audio_path TEXT,
    text_cost_pln REAL,
    audio_cost_pln REAL
)
""")
conn.commit()
# Archiwum kosztów
c.execute("""
CREATE TABLE IF NOT EXISTS history_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deleted_at TEXT,
    description_type TEXT,
    text_cost_pln REAL,
    audio_cost_pln REAL
)
""")
conn.commit()
# Tworzymy tabelę qa_history, jeśli nie istnieje
c.execute("""
CREATE TABLE IF NOT EXISTS qa_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    code TEXT,
    question TEXT,
    answer TEXT,
    cost_pln REAL
)
""")

# Tworzymy tabelę refactor_history, jeśli nie istnieje
c.execute("""
CREATE TABLE IF NOT EXISTS refactor_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    code TEXT,
    refactored_code TEXT,
    comment TEXT,
    cost_pln REAL
)
""")

conn.commit()

# Wczytanie zmiennych środowiskowych

USD_TO_PLN = 4.0


# Konfiguracja strony
st.set_page_config(
    page_title="Code Sensei",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ✨ Wywołaj funkcję stylów
def set_custom_style():
    st.markdown("""
        <style>
        .big-font {
            font-size:22px !important;
        }
        .small-font {
            font-size:14px !important;
            color: #888;
        }
        .highlight {
            background-color: #f0f2f6;
            padding: 0.3em 0.6em;
            border-radius: 0.4em;
        }
        </style>
    """, unsafe_allow_html=True)

# Tworzymy/otwieramy bazę
conn = sqlite3.connect("history.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    code TEXT,
    description TEXT,
    description_type TEXT,
    voice TEXT,
    audio_path TEXT,
    text_cost_pln REAL,
    audio_cost_pln REAL
)
""")
conn.commit()
# Archiwum kosztów
c.execute("""
CREATE TABLE IF NOT EXISTS history_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deleted_at TEXT,
    description_type TEXT,
    text_cost_pln REAL,
    audio_cost_pln REAL
)
""")
conn.commit()
# Tworzymy tabelę qa_history, jeśli nie istnieje
c.execute("""
CREATE TABLE IF NOT EXISTS qa_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    code TEXT,
    question TEXT,
    answer TEXT,
    cost_pln REAL
)
""")

# Tworzymy tabelę refactor_history, jeśli nie istnieje
c.execute("""
CREATE TABLE IF NOT EXISTS refactor_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    code TEXT,
    refactored_code TEXT,
    comment TEXT,
    cost_pln REAL
)
""")

conn.commit()




# Konfiguracja strony
st.set_page_config(
    page_title="Code Sensei",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ✨ Wywołaj funkcję stylów
set_custom_style()
# Sidebar
st.sidebar.title("🧭 Code Sensei")
menu = st.sidebar.radio(
    "Wybierz widok:",
    (
        "🔍 Analizuj kod",
        "📜 Historia analiz",
        "📊 Statystyki i eksport",
        "🧩 Funkcje"
    )
)
api_key_input = st.sidebar.text_input(
    "🔑 Wprowadź swój klucz OpenAI:",
    type="password",
    placeholder="sk-..."
)

# Zapisz w sesji
if api_key_input:
    st.session_state["user_api_key"] = api_key_input
st.sidebar.markdown("---")
st.sidebar.warning(
    "🔐 Twój klucz jest przechowywany tylko w tej sesji."
)
# Nowa sekcja linku do GitHuba
st.sidebar.markdown("---")
st.sidebar.markdown("🔗 **[Kod źródłowy na GitHubie](https://github.com/Miroslaw7224/Code_Sensei)**")
st.sidebar.info("""
**ℹ️ Code Sensei**

🔹 Autor: Miro7224  
🔹 Wersja: 1.0  
🔹 Kontakt: miro7224.job@gmail.com

Dziękujemy za korzystanie z aplikacji!
""")
# 🔍 Widok: Analizuj kod
def view_analyze():
    # Sprawdzenie, czy klucz jest w sesji
    if "user_api_key" not in st.session_state:
        st.error("❌ Nie podano klucza OpenAI. Wprowadź go w panelu bocznym.")
        st.stop()
    # ✨ Inicjalizacja klienta
    client = OpenAI(api_key=st.session_state["user_api_key"])
    # Inicjalizacja klienta z kluczem użytkownika
    st.markdown("## 🧠 Code Sensei – Analizuj kod krok po kroku")

    # Wybór modelu
    model_name = st.selectbox(
        "🧠 Wybierz model AI:",
        ["gpt-4o", "gpt-4o-mini"],
        index=0
    )
    lang = st.selectbox(
    "🌐 Wybierz język opisu:",
    ["Polski", "English"],
    index=0
)
    st.info("ℹ️ *Używanie GPT-4o-mini jest tańsze i szybsze, ale może być mniej precyzyjne.*")

    # Inicjalizacja stanu
    if "code_input" not in st.session_state:
        st.session_state["code_input"] = ""
    if "show_code" not in st.session_state:
        st.session_state["show_code"] = False
    if "last_explanation_general" not in st.session_state:
        st.session_state["last_explanation_general"] = ""
    if "last_explanation_detail" not in st.session_state:
        st.session_state["last_explanation_detail"] = ""
    if "last_audio_general" not in st.session_state:
        st.session_state["last_audio_general"] = ""
    if "last_audio_detail" not in st.session_state:
        st.session_state["last_audio_detail"] = ""

    # Pole tekstowe na kod
    st.markdown("#### ✍️ Wklej kod źródłowy")
    code_input = st.text_area(
        "",
        height=200,
        placeholder="Np. kod w Pythonie...",
        value=st.session_state["code_input"]
    )
    st.session_state["code_input"] = code_input

    st.divider()

    col_show, _ = st.columns([1, 3])
    with col_show:
        if st.button("👁️ Wyświetl kod"):
            if code_input.strip() == "":
                st.warning("⚠️ Najpierw wklej kod.")
                st.session_state["show_code"] = False
            else:
                st.session_state["show_code"] = True

    if st.session_state["show_code"]:
        st.code(code_input, language="python")

    st.divider()
    st.markdown("### 📝 Generowanie opisów i audio")

    col1, col2 = st.columns(2)

    # Kolumna 1: Opis ogólny
    with col1:
        st.markdown("#### 🟢 Opis ogólny")
        if st.button("✅ Generuj opis ogólny"):
            if code_input.strip() == "":
                st.warning("⚠️ Najpierw wklej kod.")
            else:
                with st.spinner("Generuję opis ogólny..."):
                    if lang == "Polski":
                        prompt = (
                            "Przeczytaj poniższy kod i opisz jego ogólne działanie w jednym prostym zdaniu.\n\n"
                            f"{code_input}"
                        )
                        system_content = "Jesteś doświadczonym programistą, który w prosty sposób tłumaczy działanie kodu po polsku."
                    else:
                        prompt = (
                            "Read the following code and describe its overall purpose in one simple sentence.\n\n"
                            f"{code_input}"
                        )
                        system_content = "You are an experienced programmer who explains code clearly and simply in English."

                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_content},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2
                    )
                    explanation = response.choices[0].message.content.strip()
                    st.session_state["last_explanation_general"] = explanation

                    prompt_tokens = response.usage.prompt_tokens
                    completion_tokens = response.usage.completion_tokens
                    cost_usd = prompt_tokens * 0.005/1000 + completion_tokens * 0.015/1000
                    cost_pln = cost_usd * USD_TO_PLN

                    now = datetime.now().isoformat()
                    c.execute("""
                        INSERT INTO history (timestamp, code, description, description_type, text_cost_pln)
                        VALUES (?, ?, ?, ?, ?)
                    """, (now, code_input, explanation, "ogólny", cost_pln))
                    conn.commit()

                st.success("✅ Opis ogólny został wygenerowany.")
                st.info(f"💰 Koszt generacji: {cost_pln:.4f} zł")

        if st.session_state["last_explanation_general"]:
            with st.expander("🔍 Podgląd opisu ogólnego", expanded=True):
                st.write(st.session_state["last_explanation_general"])

        voice1 = st.selectbox(
            "🎤 Wybierz głos do nagrania:",
            ["alloy", "nova", "shimmer"],
            key="voice_general"
        )
        if st.button("🎧 Generuj audio opisu ogólnego"):
            if not st.session_state["last_explanation_general"]:
                st.warning("⚠️ Najpierw wygeneruj opis.")
            else:
                with st.spinner("Generuję audio..."):
                    text = st.session_state["last_explanation_general"]
                    audio = client.audio.speech.create(
                        model="tts-1",
                        voice=voice1,
                        input=text
                    )
                    audio_path = "audio_general.mp3"
                    audio.stream_to_file(audio_path)

                    st.session_state["last_audio_general"] = audio_path

                    cost_audio_pln = len(text) * 0.015 / 1000 * USD_TO_PLN

                    c.execute("""
                        UPDATE history
                        SET voice=?, audio_path=?, audio_cost_pln=?
                        WHERE id=(SELECT MAX(id) FROM history)
                    """, (voice1, audio_path, cost_audio_pln))
                    conn.commit()

                st.success("✅ Nagranie audio zostało wygenerowane.")
                st.info(f"💰 Koszt audio: {cost_audio_pln:.4f} zł")

        if st.session_state["last_audio_general"]:
            st.audio(st.session_state["last_audio_general"])

    # Kolumna 2: Opis szczegółowy
    with col2:
        st.markdown("#### 🟡 Opis szczegółowy")
        mode = st.selectbox(
            "📝 Styl opisu:",
            ["Opis blokowy", "Opis liniowy"],
            help="Wybierz, czy opis ma być blokowy czy linia po linii."
        )
        if st.button("✅ Generuj opis szczegółowy"):
            if code_input.strip() == "":
                st.warning("⚠️ Najpierw wklej kod.")
            else:
                with st.spinner("Generuję opis szczegółowy..."):
 # Dynamiczny prompt i system prompt zależny od języka i trybu
                    if mode == "Opis blokowy":
                        if lang == "Polski":
                            prompt = (
                                "Przeczytaj poniższy kod i opisz blok po bloku, co robi każda część.\n\n"
                                f"{code_input}"
                            )
                            system_content = (
                                "Jesteś doświadczonym programistą, który w prosty sposób tłumaczy działanie kodu po polsku."
                            )
                        else:
                            prompt = (
                                "Read the following code and describe it block by block, explaining what each part does.\n\n"
                                f"{code_input}"
                            )
                            system_content = (
                                "You are an experienced programmer who explains code clearly and simply in English."
                            )
                    else:  # Opis liniowy
                        if lang == "Polski":
                            prompt = (
                                "Przeczytaj poniższy kod i opisz linia po linii, co robi każda linia.\n\n"
                                f"{code_input}"
                            )
                            system_content = (
                                "Jesteś doświadczonym programistą, który w prosty sposób tłumaczy działanie kodu po polsku."
                            )
                        else:
                            prompt = (
                                "Read the following code and describe it line by line, explaining what each line does.\n\n"
                                f"{code_input}"
                            )
                            system_content = (
                                "You are an experienced programmer who explains code clearly and simply in English."
                            )

                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_content},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2
                    )

                    explanation = response.choices[0].message.content.strip()
                    st.session_state["last_explanation_detail"] = explanation

                    prompt_tokens = response.usage.prompt_tokens
                    completion_tokens = response.usage.completion_tokens
                    cost_usd = prompt_tokens * 0.005/1000 + completion_tokens * 0.015/1000
                    cost_pln = cost_usd * USD_TO_PLN

                    now = datetime.now().isoformat()
                    c.execute("""
                        INSERT INTO history (timestamp, code, description, description_type, text_cost_pln)
                        VALUES (?, ?, ?, ?, ?)
                    """, (now, code_input, explanation, "szczegółowy", cost_pln))
                    conn.commit()

                st.success("✅ Opis szczegółowy został wygenerowany.")
                st.info(f"💰 Koszt generacji: {cost_pln:.4f} zł")

        if st.session_state["last_explanation_detail"]:
            with st.expander("🔍 Podgląd opisu szczegółowego", expanded=True):
                st.write(st.session_state["last_explanation_detail"])

        voice2 = st.selectbox(
            "🎤 Wybierz głos do nagrania:",
            ["alloy", "nova", "shimmer"],
            key="voice_detail"
        )
        if st.button("🎧 Generuj audio opisu szczegółowego"):
            if not st.session_state["last_explanation_detail"]:
                st.warning("⚠️ Najpierw wygeneruj opis.")
            else:
                with st.spinner("Generuję audio..."):
                    text = st.session_state["last_explanation_detail"]
                    audio = client.audio.speech.create(
                        model="tts-1",
                        voice=voice2,
                        input=text
                    )
                    audio_path = "audio_detail.mp3"
                    audio.stream_to_file(audio_path)

                    st.session_state["last_audio_detail"] = audio_path

                    cost_audio_pln = len(text) * 0.015 / 1000 * USD_TO_PLN

                    c.execute("""
                        UPDATE history
                        SET voice=?, audio_path=?, audio_cost_pln=?
                        WHERE id=(SELECT MAX(id) FROM history)
                    """, (voice2, audio_path, cost_audio_pln))
                    conn.commit()

                st.success("✅ Nagranie audio zostało wygenerowane.")
                st.info(f"💰 Koszt audio: {cost_audio_pln:.4f} zł")

        if st.session_state["last_audio_detail"]:
            st.audio(st.session_state["last_audio_detail"])

    st.divider()
    st.markdown("### ❓ Zadaj pytanie o kod")

    # Inicjalizacja Q&A
    if "qa_question" not in st.session_state:
        st.session_state["qa_question"] = ""
    if "qa_answer" not in st.session_state:
        st.session_state["qa_answer"] = ""

    question = st.text_input(
        "📝 Twoje pytanie:",
        value=st.session_state["qa_question"],
        placeholder="Np. Co robi ta pętla? Jak działa ta funkcja?"
    )
    st.session_state["qa_question"] = question

    if st.button("💬 Odpowiedz na pytanie"):
        if code_input.strip() == "":
            st.warning("⚠️ Najpierw wklej kod.")
        elif question.strip() == "":
            st.warning("⚠️ Najpierw wpisz pytanie.")
        else:
            with st.spinner("Generuję odpowiedź..."):
                prompt = (
                    "Masz poniższy kod oraz pytanie użytkownika.\n"
                    "Odpowiedz na to pytanie w sposób jasny i zrozumiały.\n\n"
                    f"KOD:\n{code_input}\n\n"
                    f"PYTANIE:\n{question}"
                )
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "Jesteś doświadczonym programistą i mentorem, który pomaga zrozumieć kod."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                answer = response.choices[0].message.content.strip()
                st.session_state["qa_answer"] = answer

                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                cost_usd = prompt_tokens * 0.005/1000 + completion_tokens * 0.015/1000
                cost_pln = cost_usd * USD_TO_PLN

                now = datetime.now().isoformat()
                c.execute("""
                    INSERT INTO qa_history (timestamp, code, question, answer, cost_pln)
                    VALUES (?, ?, ?, ?, ?)
                """, (now, code_input, question, answer, cost_pln))
                conn.commit()

            st.success("✅ Odpowiedź została wygenerowana.")
            st.info(f"💰 Koszt generacji odpowiedzi: {cost_pln:.4f} zł")

    if st.session_state["qa_answer"]:
        with st.expander("📖 Odpowiedź", expanded=True):
            st.write(st.session_state["qa_answer"])
    st.divider()
    st.markdown("### 🛠️ Refaktoryzacja kodu")

    # Inicjalizacja refaktoryzacji
    if "refactored_code" not in st.session_state:
        st.session_state["refactored_code"] = ""
    if "refactor_comment" not in st.session_state:
        st.session_state["refactor_comment"] = ""

    if st.button("🔄 Refaktoryzuj kod"):
        if code_input.strip() == "":
            st.warning("⚠️ Najpierw wklej kod.")
        else:
            with st.spinner("Generuję refaktoryzację..."):
                # Prompt zależny od języka
                if lang == "Polski":
                    prompt = (
                        "Masz poniższy kod. Zrefaktoryzuj go tak, aby był bardziej czytelny i zgodny z dobrymi praktykami. "
                        "Następnie podaj krótki komentarz, co zostało zmienione.\n\n"
                        f"{code_input}"
                    )
                    system_content = (
                        "Jesteś doświadczonym programistą i mentorem, który refaktoryzuje kod i tłumaczy zmiany po polsku."
                    )
                else:
                    prompt = (
                        "Here is some code. Refactor it to be more readable and follow best practices. "
                        "Then provide a short comment explaining what was changed.\n\n"
                        f"{code_input}"
                    )
                    system_content = (
                        "You are an experienced programmer and mentor who refactors code and explains the changes in English."
                    )
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )

                content = response.choices[0].message.content.strip()

                if "```" in content:
                    parts = content.split("```")
                    code_block = parts[1].strip()
                    comment = "\n".join(parts[2:]).strip() if len(parts) > 2 else "Brak komentarza."
                else:
                    code_block = content
                    comment = "Brak komentarza."

                st.session_state["refactored_code"] = code_block
                st.session_state["refactor_comment"] = comment

                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                cost_usd = prompt_tokens * 0.005/1000 + completion_tokens * 0.015/1000
                cost_pln = cost_usd * USD_TO_PLN

                now = datetime.now().isoformat()
                c.execute("""
                    INSERT INTO refactor_history (timestamp, code, refactored_code, comment, cost_pln)
                    VALUES (?, ?, ?, ?, ?)
                """, (now, code_input, code_block, comment, cost_pln))
                conn.commit()

            st.success("✅ Refaktoryzacja została wygenerowana.")
            st.info(f"💰 Koszt generacji refaktoryzacji: {cost_pln:.4f} zł")

    # Wyświetlanie refaktoryzacji
    if st.session_state["refactored_code"]:
        with st.expander("📖 Podgląd refaktoryzacji", expanded=True):
            st.markdown("**🔄 Kod po refaktoryzacji:**")
            st.code(st.session_state["refactored_code"], language="python")
            st.markdown(f"💡 **Komentarz:** {st.session_state['refactor_comment']}")

# 📜 Widok: Historia

def view_history():
        # Sprawdzenie, czy klucz jest w sesji
    if "user_api_key" not in st.session_state:
        st.error("❌ Nie podano klucza OpenAI. Wprowadź go w panelu bocznym.")
        st.stop()
    # ✨ Inicjalizacja klienta
    client = OpenAI(api_key=st.session_state["user_api_key"])
    # Inicjalizacja klienta z kluczem użytkownika
    st.markdown("## 📜 Historia działań")

    tabs = st.tabs([
        "📝 Opisy",
        "❓ Pytania i odpowiedzi",
        "🛠️ Refaktoryzacje"
    ])

    # 📝 Zakładka - Historia opisów
    with tabs[0]:
        st.markdown("### 📝 Historia opisów kodu")

        sort = st.selectbox(
            "📂 Sortuj według:",
            ["Najnowsze", "Najstarsze", "Najtańszy tekst", "Najdroższy tekst"]
        )
        ftype = st.selectbox("🎯 Filtruj wg typu opisu:", ["Wszystkie", "ogólny", "szczegółowy"])
        fvoice = st.selectbox("🎤 Filtruj wg głosu:", ["Wszystkie", "alloy", "nova", "shimmer", "brak"])

        query = "SELECT * FROM history"
        conditions = []
        params = []

        if ftype != "Wszystkie":
            conditions.append("description_type=?")
            params.append(ftype)
        if fvoice != "Wszystkie":
            if fvoice == "brak":
                conditions.append("voice IS NULL")
            else:
                conditions.append("voice=?")
                params.append(fvoice)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if sort == "Najnowsze":
            query += " ORDER BY timestamp DESC"
        elif sort == "Najstarsze":
            query += " ORDER BY timestamp ASC"
        elif sort == "Najtańszy tekst":
            query += " ORDER BY text_cost_pln ASC"
        else:
            query += " ORDER BY text_cost_pln DESC"

        c.execute(query, params)
        rows = c.fetchall()

        if not rows:
            st.warning("⚠️ Brak wyników.")
        else:
            st.success(f"✅ Znaleziono {len(rows)} wpisów.")

            total_text_cost = sum(r[7] for r in rows if r[7] is not None)
            total_audio_cost = sum(r[8] for r in rows if r[8] is not None)
            st.info(f"💰 Suma kosztów tekstu: {total_text_cost:.4f} zł | 🎧 Suma kosztów audio: {total_audio_cost:.4f} zł")

            for row in rows:
                id, ts, code, desc, dtype, voice, audio_path, text_cost, audio_cost = row
                with st.expander(f"📝 ID {id} | {ts} | {dtype} | Głos: {voice if voice else '-'}"):
                    st.code(code[:300] + ("..." if len(code) > 300 else ""), language="python")
                    st.write(desc[:500] + ("..." if len(desc) > 500 else ""))
                    st.write(f"💰 Koszt tekstu: {text_cost:.4f} zł")
                    st.write(f"🎧 Koszt audio: {audio_cost:.4f} zł" if audio_cost else "🎧 Brak audio")

                    if audio_path and os.path.exists(audio_path):
                        st.audio(audio_path)
                        with open(audio_path, "rb") as f:
                            st.download_button(
                                "📥 Pobierz audio",
                                f,
                                file_name=os.path.basename(audio_path),
                                mime="audio/mp3",
                                key=f"dl_{id}"
                            )
                    if st.button("🗑️ Usuń wpis", key=f"del_{id}"):
                        deleted_at = datetime.now().isoformat()
                        c.execute("""
                            INSERT INTO history_archive (deleted_at, description_type, text_cost_pln, audio_cost_pln)
                            VALUES (?, ?, ?, ?)
                        """, (deleted_at, dtype, text_cost, audio_cost))
                        c.execute("DELETE FROM history WHERE id=?", (id,))
                        conn.commit()
                        st.success("✅ Rekord został usunięty i zarchiwizowany.")
                        st.rerun()

            # Eksport
            df_desc = pd.DataFrame(rows, columns=[
                "ID", "Data", "Kod", "Opis", "Typ", "Głos", "Ścieżka audio", "Koszt tekstu (PLN)", "Koszt audio (PLN)"
            ])
            csv_desc = io.StringIO()
            df_desc.to_csv(csv_desc, index=False, encoding="utf-8-sig")
            st.download_button(
                label="⬇️ Eksportuj opisy do CSV",
                data=csv_desc.getvalue(),
                file_name="historia_opisow.csv",
                mime="text/csv"
            )

    # ❓ Zakładka - Pytania
    with tabs[1]:
        st.markdown("### ❓ Historia pytań i odpowiedzi")

        c.execute("SELECT * FROM qa_history ORDER BY timestamp DESC")
        qa_rows = c.fetchall()

        if not qa_rows:
            st.info("⚠️ Brak pytań.")
        else:
            st.success(f"✅ Znaleziono {len(qa_rows)} wpisów.")
            total_cost = sum(r[5] for r in qa_rows if r[5] is not None)
            st.info(f"💰 Suma kosztów odpowiedzi: {total_cost:.4f} zł")

            for row in qa_rows:
                id_, timestamp, code, question, answer, cost = row
                with st.expander(f"❓ ID {id_} | {timestamp}"):
                    st.code(code[:300] + ("..." if len(code) > 300 else ""), language="python")
                    st.markdown(f"**Pytanie:** {question}")
                    st.markdown(f"**Odpowiedź:** {answer}")
                    if cost is not None:
                        st.write(f"💰 Koszt: {cost:.4f} zł")
                    else:
                        st.write("💰 Koszt: brak danych")

            df_qa = pd.DataFrame(qa_rows, columns=[
                "ID", "Data", "Kod", "Pytanie", "Odpowiedź", "Koszt (PLN)"
            ])
            csv_qa = io.StringIO()
            df_qa.to_csv(csv_qa, index=False, encoding="utf-8-sig")
            st.download_button(
                label="⬇️ Eksportuj pytania i odpowiedzi do CSV",
                data=csv_qa.getvalue(),
                file_name="historia_pytan_odpowiedzi.csv",
                mime="text/csv"
            )

    # 🛠️ Zakładka - Refaktoryzacje
    with tabs[2]:
        st.markdown("### 🛠️ Historia refaktoryzacji")

        c.execute("SELECT * FROM refactor_history ORDER BY timestamp DESC")
        ref_rows = c.fetchall()

        if not ref_rows:
            st.info("⚠️ Brak refaktoryzacji.")
        else:
            st.success(f"✅ Znaleziono {len(ref_rows)} wpisów.")
            total_cost = sum(r[5] for r in ref_rows if r[5] is not None)
            st.info(f"💰 Suma kosztów refaktoryzacji: {total_cost:.4f} zł")

            for row in ref_rows:
                id_, timestamp, code, refactored_code, comment, cost = row
                with st.expander(f"🛠️ ID {id_} | {timestamp}"):
                    st.markdown("**Kod oryginalny:**")
                    st.code(code[:300] + ("..." if len(code) > 300 else ""), language="python")
                    st.markdown("**Kod zrefaktoryzowany:**")
                    st.code(refactored_code, language="python")
                    st.markdown(f"**Komentarz:** {comment}")
                    if cost is not None:
                        st.write(f"💰 Koszt: {cost:.4f} zł")
                    else:
                        st.write("💰 Koszt: brak danych")

            df_ref = pd.DataFrame(ref_rows, columns=[
                "ID", "Data", "Kod oryginalny", "Kod zrefaktoryzowany", "Komentarz", "Koszt (PLN)"
            ])
            csv_ref = io.StringIO()
            df_ref.to_csv(csv_ref, index=False, encoding="utf-8-sig")
            st.download_button(
                label="⬇️ Eksportuj refaktoryzacje do CSV",
                data=csv_ref.getvalue(),
                file_name="historia_refaktoryzacji.csv",
                mime="text/csv"
            )

# 📊 Widok: Statystyki i eksport
def view_statistics():
    # Sprawdzenie, czy klucz jest w sesji
    if "user_api_key" not in st.session_state:
        st.error("❌ Nie podano klucza OpenAI. Wprowadź go w panelu bocznym.")
        st.stop()
    # ✨ Inicjalizacja klienta
    client = OpenAI(api_key=st.session_state["user_api_key"])
    # Inicjalizacja klienta z kluczem użytkownika
    st.header("📊 Statystyki i eksport wszystkich działań")

    # Statystyki analiz (opisy)
    c.execute("SELECT COUNT(*), COALESCE(SUM(text_cost_pln),0), COALESCE(SUM(audio_cost_pln),0) FROM history")
    stats_current = c.fetchone()
    c.execute("SELECT COUNT(*), COALESCE(SUM(text_cost_pln),0), COALESCE(SUM(audio_cost_pln),0) FROM history_archive")
    stats_archived = c.fetchone()

    total_analyses = stats_current[0] + stats_archived[0]
    total_text_cost_analyses = stats_current[1] + stats_archived[1]
    total_audio_cost_analyses = stats_current[2] + stats_archived[2]

    # Statystyki pytań
    c.execute("SELECT COUNT(*), COALESCE(SUM(cost_pln),0) FROM qa_history")
    stats_qa = c.fetchone()
    total_qas = stats_qa[0]
    total_cost_qas = stats_qa[1]

    # Statystyki refaktoryzacji
    c.execute("SELECT COUNT(*), COALESCE(SUM(cost_pln),0) FROM refactor_history")
    stats_ref = c.fetchone()
    total_refs = stats_ref[0]
    total_cost_refs = stats_ref[1]

    # Łączne podsumowanie
    grand_total_text_cost = total_text_cost_analyses + total_cost_qas + total_cost_refs
    grand_total_audio_cost = total_audio_cost_analyses

    # Wyświetlanie w kolumnach
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🟢 Analizy")
        st.write(f"✅ Liczba: {stats_current[0]} bieżących + {stats_archived[0]} archiwalnych = {total_analyses}")
        st.write(f"📝 Koszt tekstu: {total_text_cost_analyses:.4f} zł")
        st.write(f"🎧 Koszt audio: {total_audio_cost_analyses:.4f} zł")

    with col2:
        st.subheader("❓ Pytania")
        st.write(f"✅ Liczba: {total_qas}")
        st.write(f"📝 Koszt odpowiedzi: {total_cost_qas:.4f} zł")

    with col3:
        st.subheader("🛠️ Refaktoryzacje")
        st.write(f"✅ Liczba: {total_refs}")
        st.write(f"📝 Koszt refaktoryzacji: {total_cost_refs:.4f} zł")

    st.markdown("---")
    st.subheader("🔵 Suma wszystkich kosztów")

    st.write(f"💰 **Łączny koszt tekstu i odpowiedzi:** {grand_total_text_cost:.4f} zł")
    st.write(f"🎧 **Łączny koszt audio (tylko analizy):** {grand_total_audio_cost:.4f} zł")

    st.markdown("---")
    st.subheader("📤 Eksport danych")

    # Pobieranie danych do eksportu
    c.execute("SELECT * FROM history")
    history_rows = c.fetchall()
    c.execute("SELECT * FROM history_archive")
    archive_rows = c.fetchall()
    c.execute("SELECT * FROM qa_history ORDER BY timestamp DESC")
    qa_rows = c.fetchall()
    c.execute("SELECT * FROM refactor_history ORDER BY timestamp DESC")
    ref_rows = c.fetchall()

    # Tworzenie DataFrame
    df_history = pd.DataFrame(history_rows, columns=[
        "ID","Data","Kod","Opis","Typ","Głos","Ścieżka audio","Koszt tekstu (PLN)","Koszt audio (PLN)"
    ])
    df_archive = pd.DataFrame(archive_rows, columns=[
        "ID archiwum","Data usunięcia","Typ","Koszt tekstu (PLN)","Koszt audio (PLN)"
    ])
    df_qa = pd.DataFrame(qa_rows, columns=[
        "ID","Data","Kod","Pytanie","Odpowiedź","Koszt (PLN)"
    ])
    df_ref = pd.DataFrame(ref_rows, columns=[
        "ID","Data","Kod oryginalny","Kod zrefaktoryzowany","Komentarz","Koszt (PLN)"
    ])

    # Przyciski eksportu
    csv_hist = io.StringIO()
    df_history.to_csv(csv_hist, index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Eksportuj bieżące analizy",
        data=csv_hist.getvalue(),
        file_name="analizy_biezace.csv",
        mime="text/csv"
    )

    csv_arch = io.StringIO()
    df_archive.to_csv(csv_arch, index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Eksportuj archiwum usuniętych analiz",
        data=csv_arch.getvalue(),
        file_name="analizy_archiwum.csv",
        mime="text/csv"
    )

    csv_qa = io.StringIO()
    df_qa.to_csv(csv_qa, index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Eksportuj pytania i odpowiedzi",
        data=csv_qa.getvalue(),
        file_name="pytania_odpowiedzi.csv",
        mime="text/csv"
    )

    csv_ref = io.StringIO()
    df_ref.to_csv(csv_ref, index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Eksportuj refaktoryzacje",
        data=csv_ref.getvalue(),
        file_name="refaktoryzacje.csv",
        mime="text/csv"
    )
def view_functions():
    # Sprawdzenie, czy klucz jest w sesji
    if "user_api_key" not in st.session_state:
        st.error("❌ Nie podano klucza OpenAI. Wprowadź go w panelu bocznym.")
        st.stop()
    # ✨ Inicjalizacja klienta
    client = OpenAI(api_key=st.session_state["user_api_key"])
    # Inicjalizacja klienta z kluczem użytkownika
    st.markdown('<div class="big-title">🧩 Funkcje aplikacji</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="section-subtitle">✨ Co potrafi Code Sensei?</div>
    """, unsafe_allow_html=True)

    st.info("""
    **🔍 Analizuj kod**
    - Wklej kod źródłowy
    - Generuj opis ogólny (jedno zdanie)
    - Generuj opis szczegółowy (blokowy lub linia po linii)
    - Odtwórz i pobierz nagranie audio wyjaśnienia
    - Zadaj pytanie o kod i otrzymaj odpowiedź
    - Zrefaktoryzuj kod i zobacz komentarz zmian

    **📜 Historia**
    - Przeglądaj historię wszystkich analiz
    - Filtruj wg typu, głosu, kosztu
    - Odtwarzaj nagrania
    - Eksportuj dane do CSV
    - Usuwaj wpisy i archiwizuj koszty

    **📊 Statystyki i eksport**
    - Zobacz sumy i średnie kosztów
    - Eksportuj wszystkie dane jednym kliknięciem,
""")
        
# 🔚 Końcowy warunek wyboru widoku
if menu == "🔍 Analizuj kod":
    view_analyze()
elif menu == "📜 Historia analiz":
    view_history()
elif menu == "📊 Statystyki i eksport":
    view_statistics()
elif menu == "🧩 Funkcje":
    view_functions()

