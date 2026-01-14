import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- CONFIGURAÇÃO ---
DB_URL = st.secrets.get("DB_URL", "sqlite:///finance.db")
SYSTEM_PASSWORD = "blabla123##"

def get_connection():
    return create_engine(DB_URL)

def init_db():
    engine = get_connection()
    with engine.connect() as conn:
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

# --- NOVAS FUNÇÕES DE EDIÇÃO/EXCLUSÃO ---
def update_transaction(id_transacao, cheque, data, valor, valor_pago, juros, gerson, maneca):
    engine = get_connection()
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE transactions 
            SET cheque=:cheque, data=:data, valor=:valor, valor_pago=:valor_pago, 
                juros=:juros, gerson=:gerson, maneca=:maneca
            WHERE id=:id
        """), {
            "cheque": cheque, "data": data, "valor": valor, 
            "valor_pago": valor_pago, "juros": juros, "gerson": gerson, 
            "maneca": maneca, "id": id_transacao
        })
        conn.commit()

def delete_transaction(id_transacao):
    engine = get_connection()
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM transactions WHERE id=:id"), {"id": id_transacao})
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
    st.stop() 

# --- APLICAÇÃO PRINCIPAL ---
st.title("📒 Controle Financeiro")
init_db()

# Carrega dados para exibir e para preencher os seletores
df = load_data()

# ---------------------------------------------------------
# 1. TABELA PRINCIPAL (Visualização)
# ---------------------------------------------------------
st.subheader("Extrato")
if not df.empty:
    df['data'] = pd.to_datetime(df['data'])
    df = df.sort_values(by='data').reset_index(drop=True)
    
    df['Total Gerson'] = df['gerson'].cumsum()
    df['Total Maneca'] = df['maneca'].cumsum()

    # Mostramos o ID agora para facilitar a identificação
    colunas_exibicao = ['id', 'cheque', 'data', 'valor', 'valor_pago', 'juros', 'gerson', 'maneca', 'Total Gerson', 'Total Maneca']
    
    st.dataframe(
        df[colunas_exibicao], 
        use_container_width=True,
        hide_index=True, # Esconde o índice numérico do Pandas (0,1,2) para não confundir com o ID do banco
        column_config={
            "id": st.column_config.NumberColumn("ID", format="%d"),
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
    st.info("Nenhum dado cadastrado.")

st.divider()

# ---------------------------------------------------------
# 2. ÁREA DE GERENCIAMENTO (Abas: Novo | Editar)
# ---------------------------------------------------------
tab_novo, tab_editar = st.tabs(["➕ Adicionar Novo", "✏️ Editar Existente"])

# --- ABA 1: ADICIONAR ---
with tab_novo:
    with st.form("entry_form"):
        c1, c2, c3, c4 = st.columns(4)
        cheque = c1.text_input("Cheque")
        data = c2.date_input("Data", datetime.today())
        valor = c3.number_input("Valor Original", min_value=0.0, step=0.01)
        valor_pago = c4.number_input("Valor Pago", min_value=0.0, step=0.01)
        
        c5, c6, c7 = st.columns(3)
        juros = c5.number_input("Juros", min_value=0.0, step=0.01)
        gerson = c6.number_input("Gerson (Valor)", step=0.01)
        maneca = c7.number_input("Maneca (Valor)", step=0.01)
        
        if st.form_submit_button("Salvar Transação"):
            save_transaction(cheque, data, valor, valor_pago, juros, gerson, maneca)
            st.success("Salvo com sucesso!")
            st.rerun()

# --- ABA 2: EDITAR / EXCLUIR ---
with tab_editar:
    if df.empty:
        st.warning("Não há transações para editar.")
    else:
        # Cria uma lista formatada para o Selectbox: "ID - Cheque (Valor)"
        # Isso ajuda o usuário a escolher a linha certa
        opcoes = df.apply(lambda x: f"{x['id']} - {x['cheque']} (R$ {x['valor']:.2f})", axis=1)
        
        # Selectbox para escolher qual editar
        selecao = st.selectbox("Selecione a transação para editar:", options=opcoes)
        
        # Pega o ID da string selecionada (ex: "5 - Cheque X..." -> pega 5)
        id_selecionado = int(selecao.split(" - ")[0])
        
        # Filtra o DataFrame para pegar os dados atuais dessa linha
        dados_atuais = df[df['id'] == id_selecionado].iloc[0]

        st.markdown(f"**Editando ID: {id_selecionado}**")
        
        with st.form("edit_form"):
            ec1, ec2, ec3, ec4 = st.columns(4)
            # Preenchemos os campos (value=...) com os dados atuais do banco
            e_cheque = ec1.text_input("Cheque", value=dados_atuais['cheque'])
            
            # Conversão segura de data
            data_atual = dados_atuais['data']
            if isinstance(data_atual, str):
                data_atual = datetime.strptime(data_atual, '%Y-%m-%d') # Ajuste conforme necessário se der erro de formato
            
            e_data = ec2.date_input("Data", value=data_atual)
            e_valor = ec3.number_input("Valor Original", value=float(dados_atuais['valor']), step=0.01)
            e_valor_pago = ec4.number_input("Valor Pago", value=float(dados_atuais['valor_pago']), step=0.01)
            
            ec5, ec6, ec7 = st.columns(3)
            e_juros = ec5.number_input("Juros", value=float(dados_atuais['juros']), step=0.01)
            e_gerson = ec6.number_input("Gerson", value=float(dados_atuais['gerson']), step=0.01)
            e_maneca = ec7.number_input("Maneca", value=float(dados_atuais['maneca']), step=0.01)
            
            col_btn1, col_btn2 = st.columns([1, 4])
            
            atualizar = col_btn1.form_submit_button("💾 Atualizar")
            excluir = col_btn2.form_submit_button("❌ Excluir Transação", type="primary")

            if atualizar:
                update_transaction(id_selecionado, e_cheque, e_data, e_valor, e_valor_pago, e_juros, e_gerson, e_maneca)
                st.success("Atualizado!")
                st.rerun()
            
            if excluir:
                delete_transaction(id_selecionado)
                st.warning("Excluído!")
                st.rerun()
