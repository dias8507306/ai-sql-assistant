"""Command-line demo of the natural-language -> SQL assistant (database.py + ai_helper.py).

Uses OpenAI if OPENAI_API_KEY is set, otherwise the rule-based LocalAIQueryTranslator.
Usage:
  python scripts/seed_db.py
  python scripts/ask.py "категория бойынша сатылым"
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)  # database.py reads schema.sql / data/ relative to the project root

from database import DatabaseManager  # noqa: E402
from ai_helper import AIQueryTranslator, LocalAIQueryTranslator  # noqa: E402


def main():
    question = " ".join(sys.argv[1:]) or "барлық сатылым"
    if not Path("data/sample_data.db").exists():
        sys.exit("data/sample_data.db not found - run: python scripts/seed_db.py")
    db = DatabaseManager("data/sample_data.db")
    schema = db.get_schema_info()
    samples = {t: db.get_sample_data(t) for t in schema if t != "sqlite_sequence"}

    translator = AIQueryTranslator() if os.getenv("OPENAI_API_KEY") else LocalAIQueryTranslator()
    sql = translator.generate_sql_from_natural_language(question, schema, samples)
    print(f"Question: {question}\nSQL:      {sql}\n")
    print(db.execute_query(sql))


if __name__ == "__main__":
    main()
