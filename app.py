# app.py
import streamlit as st
from openai import OpenAI
from dotenv import dotenv_values
import sqlite3
from datetime import datetime
import pandas as pd
import io
import os
from pathlib import Path

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


def render_landing_page():
    """Pierwszy ekran — ten sam klimat co statyczny landing (ciemny / akcent Streamlit)."""
    st.markdown(
        """
        <style>
            .stApp, [data-testid="stAppViewContainer"] {
                background-color: #0e1117 !important;
            }
            section.main, section.main > div {
                color: #e8eaed !important;
            }
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="stSidebarCollapsedControl"] { display: none !important; }
            div[data-testid="stToolbar"] { display: none !important; }
            .block-container {
                padding-top: 2rem !important;
                max-width: 920px !important;
            }
            .lp-bg {
                position: fixed; inset: 0; z-index: -1;
                background: #0e1117;
                background-image:
                  linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
                background-size: 48px 48px;
            }
            .lp-glow {
                position: fixed; width: 70vmax; height: 70vmax; border-radius: 50%;
                background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, transparent 55%);
                top: -20%; right: -15%; z-index: -1; pointer-events: none;
            }
            .lp-hero h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem 0; color: #fafafa; }
            .lp-hero p { color: #a3a8b8; font-size: 1.05rem; line-height: 1.55; max-width: 52ch; }
            .lp-card {
                background: #161b22; border: 1px solid #3d404a; border-radius: 12px;
                padding: 1.5rem; margin: 1.25rem 0;
                box-shadow: 0 12px 40px rgba(0,0,0,0.35);
                color: #e8eaed;
            }
            .lp-card p { color: #a3a8b8; margin: 0 0 0.75rem 0; }
            .lp-section-title {
                color: #fafafa; font-size: 1.35rem; font-weight: 600;
                margin: 1.75rem 0 0.75rem 0; letter-spacing: -0.02em;
            }
            .lp-feats {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 1rem;
                margin: 0.5rem 0 1rem 0;
            }
            .lp-feat {
                background: #262730; border: 1px solid #3d404a;
                border-radius: 10px; padding: 1rem 1.15rem; font-size: 0.9rem;
            }
            .lp-feat strong { color: #fafafa; display: block; margin-bottom: 0.4rem; font-size: 0.95rem; }
            .lp-feat span { color: #a3a8b8; font-size: 0.86rem; line-height: 1.5; display: block; }
            div[data-testid="stImage"] {
                overflow: hidden !important;
                border-radius: 12px !important;
                border: 1px solid #3d404a !important;
                margin-bottom: 0.35rem !important;
            }
            div[data-testid="stImage"] > img,
            div[data-testid="stImage"] picture img {
                border-radius: 0 !important;
                border: none !important;
                display: block !important;
                transform: scale(1.32) !important;
                transform-origin: center 20% !important;
            }
        </style>
        <div class="lp-bg"></div><div class="lp-glow"></div>
        <div class="lp-hero">
            <p style="font-size:1.5rem;margin-bottom:0.25rem;">🧠</p>
            <h1>Code Sensei</h1>
            <p><strong style="color:#e8eaed;">Wklejasz kod — dostajesz zrozumiałe wyjaśnienia, audio i odpowiedzi na pytania,</strong>
            dzięki modelom OpenAI (GPT-4o / GPT-4o-mini). Dla osób uczących się programowania, po przejściu przez cudzy
            fragment lub własny „klocek”, którego sens chcesz szybko ogarnąć.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _root = Path(__file__).resolve().parent
    _demo1 = _root / "demo-1.png"
    _demo2 = _root / "demo-2.png"
    _hero_png = _root / "assets" / "hero.png"
    _has1, _has2 = _demo1.is_file(), _demo2.is_file()

    if _has1 and _has2:
        c_a, c_b = st.columns(2, gap="medium")
        with c_a:
            st.image(
                str(_demo2),
                use_container_width=True,
                caption="Demo — przykładowy opis szczegółowy (`demo-2.png`).",
            )
        with c_b:
            st.image(
                str(_demo1),
                use_container_width=True,
                caption="Demo — widok z kodem w aplikacji (`demo-1.png`).",
            )
    elif _has1:
        st.image(
            str(_demo1),
            use_container_width=True,
            caption="Demo — `demo-1.png` (dodaj `demo-2.png` obok, aby pokazać dwa zrzuty w jednym rzędzie).",
        )
    elif _has2:
        st.image(
            str(_demo2),
            use_container_width=True,
            caption="Demo — `demo-2.png`.",
        )
    elif _hero_png.is_file():
        st.image(
            str(_hero_png),
            use_container_width=True,
            caption="Podgląd interfejsu — placeholder `assets/hero.png` (opcjonalnie użyj `demo-1.png` / `demo-2.png` w katalogu projektu).",
        )
    else:
        st.markdown(
            """
            <div style="min-height:200px;border:2px dashed #3d404a;border-radius:12px;
            display:flex;align-items:center;justify-content:center;color:#a3a8b8;background:#161b22;
            margin:1rem 0;text-align:center;padding:1rem;">
            Brak obrazów: umieść w katalogu projektu <code style="color:#fafafa;">demo-1.png</code> i/lub
            <code style="color:#fafafa;">demo-2.png</code>, albo <code style="color:#fafafa;">assets/hero.png</code>.
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <div class="lp-card">
            <p>Poniżej masz <strong>skrót możliwości</strong>. Po kliknięciu „Otwórz aplikację” przejdziesz do pełnego
            Streamlita: wybór widoku (analiza, historia, statystyki), wklejanie kodu, generowanie treści przez API
            oraz <strong>tryb demonstracyjny</strong> — możesz przejrzeć cały interfejs bez klucza; działania AI włączą się
            dopiero po wpisaniu klucza w panelu bocznym.</p>
            <p style="border-left:3px solid #ffc107;padding-left:0.75rem;margin:0;color:#e8d4a8;">
            🔐 Klucz OpenAI nigdy nie trafia do repozytorium — podajesz go tylko w aplikacji i trzyma się w sesji do
            odświeżenia karty.</p>
        </div>
        <h2 class="lp-section-title">Kluczowe funkcje</h2>
        <div class="lp-feats">
            <div class="lp-feat"><strong>🔍 Analiza kodu (GPT)</strong><span>Model czyta Twój kod i tworzy
            <strong>opis ogólny</strong> (jedno zdanie) albo <strong>opis szczegółowy</strong> — blok po bloku albo
            linia po linii, po polsku lub po angielsku. Możesz też podejrzeć kod sformatowany w podglądzie.</span></div>
            <div class="lp-feat"><strong>🎧 Audio z opisów (TTS)</strong><span>Z wygenerowanego tekstu powstaje
            nagranie głosowe (OpenAI TTS) — wybór głosu (alloy, nova, shimmer), odtwarzanie w przeglądarce; przy
            analizach zapisuje się też ścieżka do pliku w historii.</span></div>
            <div class="lp-feat"><strong>💬 Pytania i odpowiedzi</strong><span>Zadajesz pytanie w kontekście wklejonego
            kodu (np. „co robi ta pętla?”) — model odpowiada jak mentor. Wpis trafia do osobnej historii z szacunkiem
            kosztu.</span></div>
            <div class="lp-feat"><strong>🛠️ Refaktoryzacja</strong><span>Propozycja czytelniejszej wersji kodu plus
            krótki komentarz, co się zmieniło — przydatne przy porządkowaniu szkiców i uczeniu się dobrych praktyk.</span></div>
            <div class="lp-feat"><strong>📜 Historia i eksport</strong><span>Wszystkie opisy, pytania i refaktoryzacje
            lądują w <strong>SQLite</strong>: przegląd, filtry (typ, głos, koszt), usuwanie z archiwizacją kosztów,
            pobieranie audio oraz <strong>eksport do CSV</strong>.</span></div>
            <div class="lp-feat"><strong>📊 Koszty i statystyki</strong><span>Po operacjach widać szacunek w PLN
            (tokeny / długość wg uproszczonego przelicznika w aplikacji). Zbiorcze podsumowania i pełny eksport danych
            z bazy w jednym miejscu.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Bez tego ekranu: dodaj do adresu parametr `?app=1` (np. zakładka z bezpośrednim linkiem do narzędzia)."
    )


# Pierwszy ekran: landing w Streamlit (jedno `streamlit run app.py`)
_app_qp = st.query_params.get("app")
if _app_qp is not None and (str(_app_qp[0]) if isinstance(_app_qp, (list, tuple)) else str(_app_qp)) == "1":
    st.session_state["entered_main_app"] = True
if not st.session_state.get("entered_main_app", False):
    render_landing_page()
    if st.button("Otwórz aplikację →", type="primary", use_container_width=True):
        st.session_state["entered_main_app"] = True
        st.rerun()
    st.stop()

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


def has_openai_key():
    k = st.session_state.get("user_api_key")
    return bool(k and str(k).strip())


# 🔍 Widok: Analizuj kod
def view_analyze():
    demo = not has_openai_key()
    if demo:
        st.info(
            "🔍 **Tryb demonstracyjny** — możesz przeglądać interfejs (listy, pola tekstowe, rozwijane sekcje). "
            "Przyciski korzystające z OpenAI są nieaktywne. Wprowadź klucz API w panelu bocznym, aby włączyć pełną funkcjonalność."
        )
    else:
        client = OpenAI(api_key=st.session_state["user_api_key"])

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
        if st.button("✅ Generuj opis ogólny", disabled=demo):
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
        elif demo:
            with st.expander("🔍 Podgląd opisu ogólnego", expanded=False):
                st.caption("Po wygenerowaniu opisu (z kluczem API) treść pojawi się w tej sekcji.")

        voice1 = st.selectbox(
            "🎤 Wybierz głos do nagrania:",
            ["alloy", "nova", "shimmer"],
            key="voice_general"
        )
        if st.button("🎧 Generuj audio opisu ogólnego", disabled=demo):
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
        if st.button("✅ Generuj opis szczegółowy", disabled=demo):
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
        elif demo:
            with st.expander("🔍 Podgląd opisu szczegółowego", expanded=False):
                st.caption("Po wygenerowaniu opisu szczegółowego (z kluczem API) treść pojawi się tutaj.")

        voice2 = st.selectbox(
            "🎤 Wybierz głos do nagrania:",
            ["alloy", "nova", "shimmer"],
            key="voice_detail"
        )
        if st.button("🎧 Generuj audio opisu szczegółowego", disabled=demo):
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

    if st.button("💬 Odpowiedz na pytanie", disabled=demo):
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
    elif demo:
        with st.expander("📖 Odpowiedź", expanded=False):
            st.caption("Tutaj pojawi się odpowiedź modelu na Twoje pytanie o kod.")
    st.divider()
    st.markdown("### 🛠️ Refaktoryzacja kodu")

    # Inicjalizacja refaktoryzacji
    if "refactored_code" not in st.session_state:
        st.session_state["refactored_code"] = ""
    if "refactor_comment" not in st.session_state:
        st.session_state["refactor_comment"] = ""

    if st.button("🔄 Refaktoryzuj kod", disabled=demo):
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
    elif demo:
        with st.expander("📖 Podgląd refaktoryzacji", expanded=False):
            st.caption("Po refaktoryzacji zobaczysz tu zaproponowany kod i krótki komentarz zmian.")

# 📜 Widok: Historia

def view_history():
    if not has_openai_key():
        st.info(
            "🔍 **Tryb demonstracyjny** — historia i eksport działają na lokalnej bazie; "
            "klucz OpenAI jest potrzebny tylko do generowania treści w widoku „Analizuj kod”."
        )
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
    if not has_openai_key():
        st.info(
            "🔍 **Tryb demonstracyjny** — statystyki i eksport opierają się na zapisanych lokalnie danych."
        )
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
    if not has_openai_key():
        st.info("🔍 **Tryb demonstracyjny** — poniżej opis możliwości aplikacji po włączeniu klucza API.")
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

