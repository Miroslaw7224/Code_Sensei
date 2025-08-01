# Code Sensei

**Code Sensei** to aplikacja webowa zbudowana w Streamlit, która wspiera analizę kodu źródłowego i naukę programowania. Korzysta z modeli OpenAI (GPT-4o i GPT-4o-mini) do generowania opisów, wyjaśnień i refaktoryzacji kodu, a także umożliwia tworzenie nagrań audio.

---

## Funkcje

### 🔍 Analizuj kod
- Wklej kod źródłowy i wyświetl go w edytorze.
- Generuj **opis ogólny** – streszczenie działania kodu w jednym zdaniu.
- Generuj **opis szczegółowy** – opis blokowy lub linia po linii.
- Twórz nagrania audio wygenerowanych opisów (głosy: alloy, nova, shimmer).
- Zadawaj pytania o kod i otrzymuj odpowiedzi w formie tekstowej.
- Refaktoryzuj kod – otrzymuj ulepszony kod i komentarze zmian.

### 📜 Historia
- Przeglądaj historię analiz, pytań i refaktoryzacji.
- Filtruj dane według typu opisu, głosu lub kosztu.
- Odtwarzaj i pobieraj wygenerowane nagrania audio.
- Eksportuj historię do plików CSV.
- Usuwaj wpisy i archiwizuj koszty.

### 📊 Statystyki i eksport
- Podsumowanie liczby analiz, pytań i refaktoryzacji.
- Łączne koszty generacji tekstów i nagrań audio.
- Eksport wszystkich danych (analizy, pytania, refaktoryzacje) do plików CSV.

### 🧩 Funkcje aplikacji
- Przejrzysty podgląd funkcjonalności dostępny w aplikacji.
- Informacje o autorze i wersji.

---

## Technologie

- **Framework:** [Streamlit](https://streamlit.io/)
- **AI API:** [OpenAI API](https://platform.openai.com/)
- **Baza danych:** SQLite (lokalna baza `history.db`)
- **Języki:** Python
- **Hosting docelowy:** DigitalOcean

---

## Wymagania

- Python 3.10+
- Konto OpenAI i klucz API
- Biblioteki: `streamlit`, `openai`, `sqlite3`, `pandas`, `python-dotenv`

---

## Uruchomienie lokalne

```bash
# Klonowanie repozytorium
git clone <URL_REPO>
cd code-sensei

# Instalacja zależności
pip install -r requirements.txt

# Uruchomienie aplikacji
streamlit run app.py
