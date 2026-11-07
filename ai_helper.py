import os
from openai import OpenAI
from dotenv import load_dotenv

# Мүмкіндіктерді жүктеу
load_dotenv()

class AIQueryTranslator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key)
        
    def generate_sql_from_natural_language(self, question, schema_info, sample_data):
        """
        Табиғи тілдегі сұрақты SQL сұранысына аудару
        
        Args:
            question: Пайдаланушы сұрағы
            schema_info: Кестелер схемасы
            sample_data: Әр кесте үшін үлгі деректер
        
        Returns:
            SQL сұранысы
        """
        # Схема және үлгі деректерді мәтінге түрлендіру
        schema_text = self._format_schema_info(schema_info)
        sample_text = self._format_sample_data(sample_data)
        
        prompt = f"""
        Сіз SQL сұраныстарын генерациялауға арналған көмекшісіз. 
        Келесі сұрақты SQLite SQL сұранысына аударыңыз.
        
        Кестелер схемасы:
        {schema_text}
        
        Әр кесте үшін үлгі деректер:
        {sample_text}
        
        Пайдаланушы сұрағы: {question}
        
        Ережелер:
        1. Тек SQL кодты қайтарыңыз, түсіндірмесіз
        2. Тек SELECT, INSERT, UPDATE, DELETE сұраныстарын қолданыңыз
        3. SQLite синтаксисін қолданыңыз
        4. Қателерді тексеру үшін сипатталған кестелер мен бағандарды ғана қолданыңыз
        5. Жауап ретінде тек SQL кодты беріңіз
        
        SQL сұранысы:
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Сіз табиғи тілді SQL сұраныстарына дәл аударатын көмекшісіз."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Жауапта тек SQL коды болуы керек
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:-3].strip()
            elif sql_query.startswith("```"):
                sql_query = sql_query[3:-3].strip()
            
            return sql_query
            
        except Exception as e:
            return f"Қате: {str(e)}"
    
    def _format_schema_info(self, schema_info):
        """Схема ақпаратын мәтінге түрлендіру"""
        result = []
        for table_name, columns in schema_info.items():
            col_info = []
            for col in columns:
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                col_info.append(f"  {col['name']} ({col['type']}) {nullable}")
            
            result.append(f"{table_name} кестесі:\n" + "\n".join(col_info))
        
        return "\n\n".join(result)
    
    def _format_sample_data(self, sample_data):
        """Өрнектелген деректерді мәтінге түрлендіру"""
        result = []
        for table_name, df in sample_data.items():
            if not df.empty:
                result.append(f"{table_name} кестесі үшін үлгі деректер:\n{df.to_string(index=False)}")
        
        return "\n\n".join(result)


# OpenAI API ключі жоқ болса, жергілікті модельді қолдану
class LocalAIQueryTranslator(AIQueryTranslator):
    def __init__(self):
        super().__init__(api_key="dummy_key")
    
    def generate_sql_from_natural_language(self, question, schema_info, sample_data):
        """
        OpenAI API жоқ болса, қарапайым қағидалар арқылы SQL генерациялау
        """
        # Қарапайым сұрақтарды тану және аудару
        question_lower = question.lower()
        
        # Әртүрлі сұрақ үлгілері
        patterns = {
            r'.*барлық.*сатылым.*': "SELECT * FROM sales",
            r'.*соңғы.*(\d+).*күн.*сатылым.*': 
                lambda x: f"SELECT * FROM sales WHERE date >= DATE('now', '-{self._extract_number(x)} days')",
            r'.*орташа.*сатылым.*': "SELECT AVG(amount) as average_sales FROM sales",
            r'.*жалпы.*сатылым.*': "SELECT SUM(amount) as total_sales FROM sales",
            r'.*сатылым.*саны.*': "SELECT COUNT(*) as sales_count FROM sales",
            r'.*категория.*бойынша.*сатылым.*': 
                "SELECT category, SUM(amount) as total FROM sales GROUP BY category",
            r'.*өнім.*тізімі.*': "SELECT * FROM products",
            r'.*тұтынушы.*тізімі.*': "SELECT * FROM customers",
            r'.*қоры.*аз.*өнім.*': "SELECT * FROM products WHERE stock < 10",
        }
        
        for pattern, sql_template in patterns.items():
            import re
            if re.match(pattern, question_lower, re.IGNORECASE):
                if callable(sql_template):
                    return sql_template(question_lower)
                return sql_template
        
        # Әдеттегі сұрақ болмаса, қарапайым SELECT сұранысын қайтару
        return "SELECT * FROM sales LIMIT 10"
    
    def _extract_number(self, text):
        """Мәтіннен санды шығару"""
        import re
        numbers = re.findall(r'\d+', text)
        return numbers[0] if numbers else 7