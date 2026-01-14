import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- CONFIGURAÇÃO ---
# Busca a URL no secrets. Se não achar, usa sqlite local.
DB_URL = st.secrets.get("DB_URL", "sqlite:///finance.db")

# Senha do Sistema
SYSTEM_PASSWORD = "blabla123##"

def get_connection():
    return create_engine(DB_URL)

def init_db():
    engine = get_connection()
    with engine.connect() as conn:
        # Tabela usando SERIAL para Postgres
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                cheque TEXT,
                data TEXT,
                valor REAL,
                valor_pago REAL,
                juros REAL,
                gerson REAL,
                maneca REAL
            )
        """))
        conn.commit()

def load_data():
    engine = get_connection()
    # Carrega os dados brutos
    df = pd.read_sql("SELECT * FROM transactions", engine)
    return df

def save_transaction(cheque, data, valor, valor_pago, juros, gerson, maneca):
    engine = get_connection()
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO transactions (cheque, data, valor, valor_pago, juros, gerson, maneca)
            VALUES (:cheque, :data, :valor, :valor_pago, :juros, :gerson, :maneca)
        """), {
            "cheque": cheque, "data": data, "valor": valor, 
            "valor_pago": valor_pago, "juros": juros, "gerson": gerson, "maneca": maneca
        })
        conn.commit()

# --- LÓGICA DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔒 Login Necessário")
    pwd = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if pwd == SYSTEM_PASSWORD:
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Senha incorreta")
    st.stop() # Para a execução aqui se não estiver logado

# --- APLICAÇÃO PRINCIPAL ---
st.title("📒 Controle Financeiro")
init_db()

# 1. Seção de Entrada
with st.expander("➕ Adicionar Nova Transação", expanded=True):
    with st.form("entry_form"):
        c1, c2, c3, c4 = st.columns(4)
        cheque = c1.text_input("Cheque")
        # Data padrão hoje
        data = c2.date_input("Data", datetime.today())
        valor = c3.number_input("Valor Original", min_value=0.0, step=0.01)
        valor_pago = c4.number_input("Valor Pago", min_value=0.0, step=0.01)
        
        c5, c6, c7 = st.columns(3)
        juros = c5.number_input("Juros", min_value=0.0, step=0.01)
        gerson = c6.number_input("Gerson (Valor)", step=0.01)
        maneca = c7.number_input("Maneca (Valor)", step=0.01)
        
        submitted = st.form_submit_button("Salvar Transação")
        if submitted:
            save_transaction(cheque, data, valor, valor_pago, juros, gerson, maneca)
            st.success("Salvo com sucesso!")
            st.rerun()

# 2. Seção de Dados e Cálculos
df = load_data()

if not df.empty:
    # --- ORDENAÇÃO POR DATA ---
    # Converte a coluna 'data' para datetime para garantir ordenação correta
    df['data'] = pd.to_datetime(df['data'])
    
    # Ordena do mais antigo para o mais recente
    df = df.sort_values(by='data').reset_index(drop=True)

    # --- SOMAS ACUMULADAS ---
    # Calculadas DEPOIS de ordenar, para o saldo refletir a linha do tempo
    df['Total Gerson'] = df['gerson'].cumsum()
    df['Total Maneca'] = df['maneca'].cumsum()

    # Formatação da tabela para exibição
    # Removemos a coluna 'data' original convertida e formatamos apenas para visualização se desejar
    # Mas o Streamlit lida bem com datetime.
    
    colunas_exibicao = ['cheque', 'data', 'valor', 'valor_pago', 'juros', 'gerson', 'maneca', 'Total Gerson', 'Total Maneca']
    display_df = df[colunas_exibicao]
    
    # Formatação opcional: deixar a data bonita (DD/MM/AAAA) visualmente
    # display_df['data'] = display_df['data'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        display_df, 
        use_container_width=True,
        column_config={
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            "valor_pago": st.column_config.NumberColumn("Valor Pago", format="R$ %.2f"),
            "juros": st.column_config.NumberColumn("Juros", format="R$ %.2f"),
            "gerson": st.column_config.NumberColumn("Gerson", format="R$ %.2f"),
            "maneca": st.column_config.NumberColumn("Maneca", format="R$ %.2f"),
            "Total Gerson": st.column_config.NumberColumn("Total Gerson", format="R$ %.2f"),
            "Total Maneca": st.column_config.NumberColumn("Total Maneca", format="R$ %.2f"),
        }
    )
else:
    st.info("Nenhum dado encontrado. Adicione uma transação acima.")
