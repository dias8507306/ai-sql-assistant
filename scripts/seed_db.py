"""Generate random demo data for the SQL assistant.

Creates:
  data/sample_data.db   - SQLite DB (schema.sql + random rows) used by database.py / scripts/ask.py
  data/sample_sales.csv - the same sales table as CSV, for the Streamlit app ("Demo data" option)

All values are randomly generated (fixed seed for reproducibility).
Usage:  python scripts/seed_db.py [--rows 400] [--seed 42]
"""
import argparse
import csv
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

PRODUCTS = [
    # name, category, base price
    ("Кітап", "Білім", 30), ("Журнал", "Білім", 10), ("Онлайн курс", "Білім", 120),
    ("Компьютер", "Техника", 1400), ("Телефон", "Техника", 750), ("Құлаққап", "Техника", 60),
    ("Планшет", "Техника", 420), ("Куртка", "Киім", 90), ("Кроссовка", "Киім", 110),
    ("Футболка", "Киім", 25), ("Шай", "Азық-түлік", 8), ("Кофе", "Азық-түлік", 15),
]
REGIONS = ["Алматы", "Астана", "Шымкент", "Қарағанды", "Ақтөбе", "Павлодар"]
REGION_WEIGHTS = [30, 25, 15, 12, 10, 8]
MALE = ["Ерлан", "Нұрлан", "Асхат", "Бекзат", "Тимур", "Дәурен"]
FEMALE = ["Айгерім", "Динара", "Сәуле", "Мадина", "Аружан", "Әсел"]
LAST = ["Сапаров", "Нұрланов", "Ахметов", "Жұмабаев", "Қасымов", "Омаров", "Серікбаев", "Тоқтаров"]
TRANSLIT = {
    "а": "a", "ә": "a", "б": "b", "в": "v", "г": "g", "ғ": "g", "д": "d", "е": "e", "ж": "zh", "з": "z",
    "и": "i", "й": "i", "к": "k", "қ": "q", "л": "l", "м": "m", "н": "n", "ң": "n", "о": "o", "ө": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ұ": "u", "ү": "u", "ф": "f", "х": "h", "ш": "sh",
    "ы": "y", "і": "i",
}


def translit(s: str) -> str:
    return "".join(TRANSLIT.get(ch, ch) for ch in s.lower())


def random_sales(rng: random.Random, n: int, start: date, days: int):
    rows = []
    for _ in range(n):
        # weekend + end-of-year seasonality (rejection sampling)
        while True:
            d = start + timedelta(days=rng.randrange(days))
            weight = (1.3 if d.weekday() >= 5 else 1.0) * (1.4 if d.month in (11, 12) else 1.0)
            if rng.random() < weight / 1.82:
                break
        name, cat, base = rng.choice(PRODUCTS)
        amount = round(base * rng.uniform(0.8, 1.25), 2)
        region = rng.choices(REGIONS, REGION_WEIGHTS)[0]
        rows.append((name, amount, d.isoformat(), cat, region))
    rows.sort(key=lambda r: r[2])
    return rows


def random_customers(rng: random.Random, n: int):
    customers, used = [], set()
    while len(customers) < n:
        female = rng.random() < 0.5
        first = rng.choice(FEMALE if female else MALE)
        last = rng.choice(LAST) + ("а" if female else "")
        if (first, last) in used:
            continue
        used.add((first, last))
        email = f"{translit(first)}.{translit(last)}@example.com"
        reg = date(2023, 6, 1) + timedelta(days=rng.randrange(400))
        customers.append((f"{first} {last}", email, reg.isoformat(), round(rng.uniform(20, 3000), 2)))
    return customers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=400)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    DATA.mkdir(exist_ok=True)

    sales = random_sales(rng, args.rows, date(2024, 1, 1), 366)
    customers = random_customers(rng, 25)
    products = [(name, float(base), rng.randint(0, 120), cat) for name, cat, base in PRODUCTS]

    db_path = DATA / "sample_data.db"
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
    conn.executemany("INSERT INTO sales (product, amount, date, category, region) VALUES (?,?,?,?,?)", sales)
    conn.executemany("INSERT INTO customers (name, email, registration_date, total_purchases) VALUES (?,?,?,?)", customers)
    conn.executemany("INSERT INTO products (name, price, stock, category) VALUES (?,?,?,?)", products)
    conn.commit()
    conn.close()

    with open(DATA / "sample_sales.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["product", "amount", "date", "category", "region"])
        w.writerows(sales)

    print(f"OK: data/sample_data.db ({len(sales)} sales, {len(customers)} customers, {len(products)} products)")
    print("OK: data/sample_sales.csv")


if __name__ == "__main__":
    main()
