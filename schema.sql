-- Деректер қазынасын бастапқы инициализациялау (тек кестелер құрылымы).
-- Үлгі деректерді генерациялау: python scripts/seed_db.py
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT NOT NULL,
    amount REAL NOT NULL,
    date DATE NOT NULL,
    category TEXT,
    region TEXT
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    registration_date DATE,
    total_purchases REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER DEFAULT 0,
    category TEXT
);
