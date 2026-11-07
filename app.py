import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import os

# Бет баптаулары
st.set_page_config(
    page_title="DataInsight",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Минималист дизайн (CSS)
st.markdown("""
<style>
    /* Негізгі стильдер */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header стильдері */
    .main-header {
        padding: 2rem 0 1.5rem 0;
        text-align: center;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 2rem;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 300;
        color: #1e293b;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        font-size: 1rem;
        color: #64748b;
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.5;
    }
    
    /* Карточкалар */
    .custom-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
        height: 100%;
    }
    
    .custom-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Кіру өрістері */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        padding: 0.75rem;
        font-size: 0.95rem;
    }
    
    /* Кнопкалар */
    .stButton > button {
        border-radius: 8px;
        border: none;
        background: #3b82f6;
        color: white;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: #2563eb;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
    }
    
    /* Кеңейткіштер */
    .streamlit-expanderHeader {
        background: white;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        font-weight: 500;
    }
    
    /* Сүзгілер */
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 1px solid #cbd5e1;
    }
    
    /* Кестелер */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }
    
    /* Статус аймағы */
    [data-testid="stStatusWidget"] {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    
    /* Кішкене экрандар үшін */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        .custom-card {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Деректер қорымен жұмыс
def upload_to_sql(df, table_name="uploaded_data"):
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql(table_name, conn, index=False, if_exists='replace')
    return conn

# Жақсартылған SQL генераторы
def generate_sql_dynamic(question, df, table_name="uploaded_data"):
    question = question.lower()
    cols = df.columns.tolist()
    
    # Сандық және мәтін бағандарын бөлу
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    text_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Негізгі шаблондар
    if any(word in question for word in ["барлық", "көрсет", "толық"]):
        return f"SELECT * FROM {table_name} LIMIT 100"
    
    if "сипаттама" in question or "statistics" in question:
        return f"""
            SELECT 
                COUNT(*) as total_rows,
                {', '.join([f'AVG([{col}]) as avg_{col}' for col in numeric_cols[:3]])}
            FROM {table_name}
        """
    
    # Сандық бағандарға сұрақтар
    for col in cols:
        col_lower = col.lower()
        if col_lower in question:
            # Орташа мән
            if any(word in question for word in ["орташа", "average", "mean"]):
                if col in numeric_cols:
                    return f"SELECT AVG([{col}]) as average_{col} FROM {table_name}"
            
            # Қосынды
            if any(word in question for word in ["қосынды", "жалпы", "сумма", "total", "sum"]):
                if col in numeric_cols:
                    return f"SELECT SUM([{col}]) as total_{col} FROM {table_name}"
            
            # Максимум/Минимум
            if any(word in question for word in ["ең үлкен", "maximum", "максимум"]):
                if col in numeric_cols:
                    return f"SELECT MAX([{col}]) as max_{col} FROM {table_name}"
            
            if any(word in question for word in ["ең кіші", "minimum", "минимум"]):
                if col in numeric_cols:
                    return f"SELECT MIN([{col}]) as min_{col} FROM {table_name}"
    
    # Топтастыру
    if any(word in question for word in ["топтастыр", "бойынша", "group", "категория"]):
        if text_cols and numeric_cols:
            return f"""
                SELECT [{text_cols[0]}], 
                       COUNT(*) as count,
                       {f'SUM([{numeric_cols[0]}]) as sum_{numeric_cols[0]}' if numeric_cols else ''}
                FROM {table_name}
                GROUP BY [{text_cols[0]}]
                ORDER BY count DESC
                LIMIT 10
            """
    
    return f"SELECT * FROM {table_name} LIMIT 20"

# Деректерді қолмен енгізу функциясы
def create_manual_data():
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("📝 Деректерді қолмен енгізу")
    
    # Бағандарды құру
    col_count = st.slider("Бағандар саны", 2, 6, 3)
    
    cols = st.columns(col_count)
    column_names = []
    column_types = []
    sample_data = []
    
    for i in range(col_count):
        with cols[i]:
            col_name = st.text_input(f"Баған аты {i+1}", value=f"Баған_{i+1}")
            col_type = st.selectbox(f"Тип {i+1}", ["Сан", "Мәтін", "Күн"], key=f"type_{i}")
            
            if col_type == "Сан":
                sample_val = st.number_input(f"Мысал мән {i+1}", value=float(i*10), key=f"val_{i}")
            elif col_type == "Мәтін":
                sample_val = st.text_input(f"Мысал мән {i+1}", value=f"Мән_{i}", key=f"val_{i}")
            else:
                sample_val = st.date_input(f"Мысал мән {i+1}", key=f"val_{i}")
            
            column_names.append(col_name)
            column_types.append(col_type)
            sample_data.append(sample_val)
    
    # Жолдар саны
    row_count = st.slider("Жолдар саны", 5, 50, 10)
    
    # Деректерді генерациялау
    if st.button("Деректерді жасау", key="generate_data"):
        data = []
        for i in range(row_count):
            row = []
            for j in range(col_count):
                if column_types[j] == "Сан":
                    row.append(sample_data[j] + i * (j+1))
                elif column_types[j] == "Мәтін":
                    row.append(f"{sample_data[j]}_{i}")
                else:
                    # Күн үшін
                    row.append(pd.Timestamp(sample_data[j]) + pd.Timedelta(days=i))
            data.append(row)
        
        df = pd.DataFrame(data, columns=column_names)
        st.success(f"✅ {row_count} жолдан тұратын деректер жасалды")
        return df
    
    st.markdown('</div>', unsafe_allow_html=True)
    return None

# Негізгі функция
def main():
    # Header
    st.markdown("""
        <div class="main-header">
            <h1 class="main-title">DataInsight</h1>
            <p class="sub-title">Деректерді талдаудың минималистік құралы. Файл жүктеңіз немесе деректерді қолмен енгізіңіз.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Негізгі контейнер
    main_container = st.container()
    
    with main_container:
        # Екі негізгі опция
        option = st.radio(
            "Деректер көзі:",
            ["📁 Файл жүктеу", "✏️ Деректерді қолмен енгізу", "🧪 Демо деректер"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.divider()
        
        if option == "🧪 Демо деректер":
            # Кездейсоқ генерацияланған демо деректер (scripts/seed_db.py)
            demo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_sales.csv")
            if os.path.exists(demo_path):
                if st.session_state.get("data_source") != "demo":
                    st.session_state.df = pd.read_csv(demo_path)
                    st.session_state.data_source = "demo"
                st.info("Демо: data/sample_sales.csv (кездейсоқ деректер)")
            else:
                st.warning("data/sample_sales.csv табылмады. Іске қосыңыз: python scripts/seed_db.py")

        elif option == "✏️ Деректерді қолмен енгізу":
            df = create_manual_data()
            if df is not None:
                st.session_state.df = df
                st.session_state.data_source = "manual"
        
        else:
            # Файл жүктеу
            uploaded_file = st.file_uploader(
                "CSV немесе Excel файлын таңдаңыз",
                type=['csv', 'xlsx'],
                help="Файлдың көлемі 200MB-тан аспауы керек"
            )
            
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.session_state.df = df
                    st.session_state.data_source = "file"
                    st.success(f"✅ Файл сәтті жүктелді: {len(df)} жол, {len(df.columns)} баған")
                    
                except Exception as e:
                    st.error(f"Файлды оқу кезінде қате: {str(e)}")
                    return
        
        # Деректер бар болса
        if 'df' in st.session_state and st.session_state.df is not None:
            df = st.session_state.df
            
            # Деректерді SQL-ге дайындау
            conn = upload_to_sql(df)
            
            # Деректерді көрсету
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown('<div class="custom-card">', unsafe_allow_html=True)
                st.subheader("📋 Деректер алдын ала қарау")
                st.dataframe(df.head(10), use_container_width=True, height=350)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="custom-card">', unsafe_allow_html=True)
                st.subheader("📊 Статистика")
                st.metric("Жолдар", len(df))
                st.metric("Бағандар", len(df.columns))
                
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    st.metric("Сандық бағандар", len(numeric_cols))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="custom-card">', unsafe_allow_html=True)
                st.subheader("🔍 Іс-әрекеттер")
                
                if st.button("📈 Автоматты талдау", use_container_width=True):
                    st.session_state.auto_analyze = True
                
                if st.button("🔄 Деректерді тазарту", use_container_width=True):
                    # Жай ғана мысал
                    st.info("Жұмыс істеу үстінде...")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.divider()
            
            # Сұрақ қою бөлімі
            st.markdown("### 💭 Деректер бойынша сұрақ қойыңыз")
            
            question_col, button_col = st.columns([5, 1])
            
            with question_col:
                user_input = st.text_input(
                    "Сұрағыңызды енгізіңіз:",
                    placeholder="Мысалы: 'орташа бағаны есептеңіз' немесе 'категория бойынша топтастырыңыз'",
                    label_visibility="collapsed"
                )
            
            with button_col:
                analyze_btn = st.button("Талдау", use_container_width=True)
            
            if (user_input and analyze_btn) or ('auto_analyze' in st.session_state and st.session_state.auto_analyze):
                if 'auto_analyze' in st.session_state:
                    user_input = "негізгі статистика мен графиктерді көрсет"
                
                with st.status("Талдау жүргізілуде...", expanded=True) as status:
                    try:
                        # SQL сұрағын жасау
                        sql_query = generate_sql_dynamic(user_input, df)
                        
                        # Деректерді алу
                        result_df = pd.read_sql_query(sql_query, conn)
                        
                        # Нәтижені көрсету
                        st.subheader("📋 Нәтиже")
                        st.dataframe(result_df, use_container_width=True)
                        
                        # Автоматты визуализация
                        if len(result_df) > 0 and len(result_df.columns) >= 2:
                            st.subheader("📈 Визуализация")
                            
                            # График түрін таңдау
                            chart_options = ["Болмауы мүмкін", "Сызықтық", "Бағанды", "Дөңгелек"]
                            chart_type = st.selectbox("График түрін таңдаңыз:", chart_options)
                            
                            if chart_type != "Болмауы мүмкін":
                                try:
                                    fig = None
                                    
                                    if chart_type == "Сызықтық":
                                        fig = px.line(
                                            result_df,
                                            x=result_df.columns[0],
                                            y=result_df.columns[1] if len(result_df.columns) > 1 else result_df.columns[0],
                                            markers=True
                                        )
                                    elif chart_type == "Бағанды":
                                        fig = px.bar(
                                            result_df,
                                            x=result_df.columns[0],
                                            y=result_df.columns[1] if len(result_df.columns) > 1 else result_df.columns[0]
                                        )
                                    elif chart_type == "Дөңгелек":
                                        if len(result_df) <= 10:
                                            fig = px.pie(
                                                result_df,
                                                names=result_df.columns[0],
                                                values=result_df.columns[1] if len(result_df.columns) > 1 else result_df.columns[0]
                                            )
                                    
                                    if fig:
                                        fig.update_layout(
                                            plot_bgcolor='white',
                                            paper_bgcolor='white',
                                            font=dict(size=12),
                                            margin=dict(t=30, b=30, l=30, r=30)
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                except Exception as e:
                                    st.info("Бұл деректер үшін график салу мүмкін емес")
                        
                        status.update(label="Талдау аяқталды!", state="complete")
                        
                        if 'auto_analyze' in st.session_state:
                            del st.session_state.auto_analyze
                            
                    except Exception as e:
                        st.error(f"Талдау кезінде қате: {str(e)}")
                        status.update(label="Қате орын алды", state="error")
            
            # Дополнительные инструменты
            with st.expander("⚙️ Қосымша құралдар"):
                tab1, tab2, tab3 = st.tabs(["📥 Деректерді экспорттау", "🔧 Трансформация", "ℹ️ Ақпарат"])
                
                with tab1:
                    export_format = st.selectbox("Формат", ["CSV", "Excel"])
                    if st.button("Экспорттау"):
                        buffer = io.BytesIO()
                        if export_format == "CSV":
                            df.to_csv(buffer, index=False)
                            buffer.seek(0)
                            st.download_button(
                                label="Файлды жүктеп алу",
                                data=buffer,
                                file_name="data_export.csv",
                                mime="text/csv"
                            )
                
                with tab2:
                    st.write("Деректерді өзгерту опциялары")
                    if st.button("Бос мәндерді жою"):
                        df_clean = df.dropna()
                        st.session_state.df = df_clean
                        st.success(f"{len(df) - len(df_clean)} бос жол жойылды")
                
                with tab3:
                    st.write("Баған типтері:")
                    for col in df.columns:
                        dtype = str(df[col].dtype)
                        st.text(f"• {col}: {dtype}")
        
        else:
            # Бастапқы экран
            st.markdown("""
                <div style='text-align: center; padding: 4rem 2rem;'>
                    <h3 style='color: #64748b; font-weight: 400;'>
                        Талдау үшін файл жүктеңіз немесе деректерді қолмен енгізіңіз
                    </h3>
                    <p style='color: #94a3b8; margin-top: 1rem;'>
                        Мысалдар: сатылымдар, демографиялық деректер, қаржылық көрсеткіштер
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            # Мысал деректер
            with st.expander("📚 Мысал деректерді көру"):
                sample_data = pd.DataFrame({
                    'Ай': ['Қаң', 'Ақп', 'Нау'],
                    'Сатылым': [120, 150, 180],
                    'Табыс': [12000, 15000, 18000],
                    'Клиенттер': [50, 60, 70]
                })
                st.dataframe(sample_data, use_container_width=True)

if __name__ == "__main__":
    main()