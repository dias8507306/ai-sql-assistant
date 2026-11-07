# DataInsight: natural-language SQL assistant

A Streamlit app that turns questions in plain language (Kazakh / English keywords) into SQL over an uploaded dataset, runs them on an in-memory SQLite database and charts the results with Plotly. It also includes a reusable NL-to-SQL module that can use OpenAI or a rule-based fallback.

## Features

- **Data sources:** upload CSV / Excel, generate a table by hand, or use the bundled **demo dataset** (random sales data)
- Data preview, row / column statistics, one-click "auto analysis"
- **Question to SQL** (`generate_sql_dynamic`): average / sum / max / min per column, group-by, "show all", descriptive stats; runs on SQLite in memory
- Auto-visualisation of the result: line, bar or pie chart (Plotly)
- Extra tools: CSV export, drop empty rows, column type info
- `ai_helper.py`: `AIQueryTranslator` sends the schema and sample rows to OpenAI (`gpt-3.5-turbo`) to produce SQLite SQL. `LocalAIQueryTranslator` is a regex-based fallback used when no key is set
- `database.py`: a small SQLite manager (schema bootstrap, query execution, schema introspection)

## Tech stack

Python · Streamlit · pandas · SQLite · Plotly · OpenAI API (optional) · python-dotenv

## Project structure

```
app.py               Streamlit UI (DataInsight)
ai_helper.py         NL -> SQL translators (OpenAI + local rules)
database.py          SQLite helper
schema.sql           tables: sales, customers, products
scripts/seed_db.py   random demo data generator -> data/sample_data.db + data/sample_sales.csv
scripts/ask.py       CLI demo: question -> SQL -> result
data/sample_sales.csv  generated demo dataset (committed)
.env.example
```

## How to run (demo mode)

```bash
python -m venv .venv && .venv/Scripts/activate      # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python scripts/seed_db.py          # creates data/sample_data.db and data/sample_sales.csv
streamlit run app.py               # choose "🧪 Демо деректер"

# CLI: NL -> SQL over the SQLite demo DB (rule-based without a key)
python scripts/ask.py "категория бойынша сатылым"
python scripts/ask.py "орташа сатылым"
```

Optional: copy `.env.example` to `.env` and set `OPENAI_API_KEY` to switch `scripts/ask.py` to the OpenAI translator.

> All data in this repository is randomly generated; brand names are anonymized.

Author: Dias Ayazbay.

## Кратко (RU)

DataInsight — приложение на Streamlit, которое превращает вопрос на естественном языке в SQL-запрос.
Можно загрузить CSV/Excel, ввести данные вручную или взять готовые демо-данные. Результат — таблица и график Plotly.
`ai_helper.py` генерирует SQL через OpenAI или без ключа — на основе правил. Все данные сгенерированы случайно.
