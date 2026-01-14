import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- CONFIGURATION ---
# For local testing, this creates a file 'finance.db' automatically.
# For production, replace this URL with your cloud database URL (e.g., Postgres).
DB_URL = st.secrets.get("DB_URL", "sqlite:///finance.db")


# Simple Password for Login
SYSTEM_PASSWORD = "blabla123##"


def get_connection():
    return create_engine(DB_URL)


def init_db():
    engine = get_connection()
    with engine.connect() as conn:
        conn.execute(text("""
                          CREATE TABLE IF NOT EXISTS transactions
                          (
                              id
                              INTEGER
                              PRIMARY
                              KEY
                              AUTOINCREMENT,
                              cheque
                              TEXT,
                              data
                              TEXT,
                              valor
                              REAL,
                              valor_pago
                              REAL,
                              juros
                              REAL,
                              gerson
                              REAL,
                              maneca
                              REAL
                          )
                          """))
        conn.commit()


def load_data():
    engine = get_connection()
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


# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔒 Login Required")
    pwd = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pwd == SYSTEM_PASSWORD:
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()  # Stop execution here if not logged in

# --- MAIN APP ---
st.title("📒 Finance Control")
init_db()

# 1. Input Section
with st.expander("➕ Add New Line", expanded=True):
    with st.form("entry_form"):
        c1, c2, c3, c4 = st.columns(4)
        cheque = c1.text_input("Cheque")
        data = c2.date_input("Data", datetime.today())
        valor = c3.number_input("Valor", min_value=0.0, step=0.01)
        valor_pago = c4.number_input("Valor Pago", min_value=0.0, step=0.01)

        c5, c6, c7 = st.columns(3)
        juros = c5.number_input("Juros", min_value=0.0, step=0.01)
        gerson = c6.number_input("Gerson (Value)", step=0.01)
        maneca = c7.number_input("Maneca (Value)", step=0.01)

        submitted = st.form_submit_button("Save Transaction")
        if submitted:
            save_transaction(cheque, data, valor, valor_pago, juros, gerson, maneca)
            st.success("Saved!")
            st.rerun()

# 2. Data & Calculation Section
df = load_data()

if not df.empty:
    # Calculate Cumulative Sums
    df['Total Gerson'] = df['gerson'].cumsum()
    df['Total Maneca'] = df['maneca'].cumsum()

    # Formatting columns for display (Optional)
    display_df = df[
        ['cheque', 'data', 'valor', 'valor_pago', 'juros', 'gerson', 'maneca', 'Total Gerson', 'Total Maneca']]

    st.dataframe(display_df, use_container_width=True)
else:
    st.info("No data found. Add a transaction above.")
