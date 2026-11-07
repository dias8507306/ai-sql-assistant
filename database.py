import os
import sqlite3
import pandas as pd
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path='data/sample_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Деректер қазынасын бастапқы инициализациялау"""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        with self.get_connection() as conn:
            with open('schema.sql', 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Деректер қазынасы байланысын алу"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def execute_query(self, sql_query):
        """SQL сұранысын орындау"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query)
                
                # SELECT сұраныстары үшін
                if sql_query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    columns = [description[0] for description in cursor.description]
                    return pd.DataFrame(results, columns=columns)
                else:
                    # INSERT, UPDATE, DELETE үшін
                    affected_rows = cursor.rowcount
                    return f"Сәтті орындалды. Өзгертілген жолдар: {affected_rows}"
        except sqlite3.Error as e:
            return f"Қате: {str(e)}"
    
    def get_schema_info(self):
        """Кестелер схемасын алу"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Барлық кестелерді алу
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            schema_info = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                schema_info[table_name] = [
                    {"name": col[1], "type": col[2], "nullable": not col[3]}
                    for col in columns
                ]
            
            return schema_info
    
    def get_sample_data(self, table_name, limit=3):
        """Кесте үшін үлгі деректерді алу"""
        try:
            df = self.execute_query(f"SELECT * FROM {table_name} LIMIT {limit}")
            return df
        except:
            return pd.DataFrame()