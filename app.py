"""
Sistema de Gestão Financeira para Casal
=======================================
Aplicação Streamlit para controle de finanças pessoais

Funcionalidades:
- Dashboard com métricas em tempo real
- Gestão de entradas (salários e rendas extras)
- Gestão de saídas (despesas categorizadas)
- Controle de dívidas (em acordo e negativadas)
- Persistência local em CSV

Como executar:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from pathlib import Path

# Importar streamlit-shadcn-ui se disponível
try:
    from streamlit_shadcn_ui import card, badge, button
    SHADCN_AVAILABLE = True
except ImportError:
    SHADCN_AVAILABLE = False

# ============================================
# CONFIGURAÇÃO INICIAL
# ============================================

st.set_page_config(
    page_title="Gestão Financeira",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

ENTRADAS_FILE = DATA_DIR / "entradas.csv"
SAIDAS_FILE = DATA_DIR / "saidas.csv"
DIVIDAS_FILE = DATA_DIR / "dividas.csv"

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def format_currency(value: float) -> str:
    """Formata valor monetário no padrão brasileiro."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def init_csv_files():
    """Inicializa os arquivos CSV se não existirem"""
    if not ENTRADAS_FILE.exists():
        pd.DataFrame(columns=['data', 'tipo', 'parceiro', 'valor', 'descricao']).to_csv(ENTRADAS_FILE, index=False)
    if not SAIDAS_FILE.exists():
        pd.DataFrame(columns=['data', 'categoria', 'valor', 'descricao']).to_csv(SAIDAS_FILE, index=False)
    if not DIVIDAS_FILE.exists():
        pd.DataFrame(columns=['credor', 'valor_total', 'valor_pago', 'status', 'data_inicio', 'descricao']).to_csv(DIVIDAS_FILE, index=False)

def load_data(file_path):
    """Carrega dados de um arquivo CSV com conversão segura de datas."""
    if file_path.exists():
        df = pd.read_csv(file_path)
        # Converter colunas de data
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
        if 'data_inicio' in df.columns:
            df['data_inicio'] = pd.to_datetime(df['data_inicio'], errors='coerce')
        return df
    return pd.DataFrame()

def save_data(df, file_path):
    """Salva dados em um arquivo CSV"""
    df.to_csv(file_path, index=False)

# ============================================
# FUNÇÕES DE ADIÇÃO E EXCLUSÃO (CORRIGIDAS)
# ============================================

def add_entrada(data, tipo, parceiro, valor, descricao):
    df = load_data(ENTRADAS_FILE)
    nova_entrada = pd.DataFrame([{
        'data': data.strftime('%Y-%m-%d'),
        'tipo': tipo,
        'parceiro': parceiro,
        'valor': valor,
        'descricao': descricao
    }])
    df = pd.concat([df, nova_entrada], ignore_index=True)
    save_data(df, ENTRADAS_FILE)

def add_saida(data, categoria, valor, descricao):
    df = load_data(SAIDAS_FILE)
    nova_saida = pd.DataFrame([{
        'data': data.strftime('%Y-%m-%d'),
        'categoria': categoria,
        'valor': valor,
        'descricao': descricao
    }])
    df = pd.concat([df, nova_saida], ignore_index=True)
    save_data(df, SAIDAS_FILE)

def add_divida(credor, valor_total, valor_pago, status, data_inicio, descricao):
    df = load_data(DIVIDAS_FILE)
    nova_divida = pd.DataFrame([{
        'credor': credor,
        'valor_total': valor_total,
        'valor_pago': valor_pago,
        'status': status,
        'data_inicio': data_inicio.strftime('%Y-%m-%d'),
        'descricao': descricao
    }])
    df = pd.concat([df, nova_divida], ignore_index=True)
    save_data(df, DIVIDAS_FILE)

def delete_entrada(original_index):
    df = load_data(ENTRADAS_FILE)
    if original_index in df.index:
        df = df.drop(original_index).reset_index(drop=True)
        save_data(df, ENTRADAS_FILE)

def delete_saida(original_index):
    df = load_data(SAIDAS_FILE)
    if original_index in df.index:
        df = df.drop(original_index).reset_index(drop=True)
        save_data(df, SAIDAS_FILE)

def delete_divida(original_index):
    df = load_data(DIVIDAS_FILE)
    if original_index in df.index:
        df = df.drop(original_index).reset_index(drop=True)
        save_data(df, DIVIDAS_FILE)

def update_divida(original_index, valor_pago):
    df = load_data(DIVIDAS_FILE)
    if original_index in df.index:
        df.loc[original_index, 'valor_pago'] = valor_pago
        save_data(df, DIVIDAS_FILE)

# ============================================
# CÁLCULOS
# ============================================

def get_mes_vigente():
    hoje = datetime.now()
    return hoje.month, hoje.year

def filter_by_month(df, mes, ano, date_column='data'):
    if df.empty or date_column not in df.columns:
        return df
    df_filtered = df.copy()
    df_filtered[date_column] = pd.to_datetime(df_filtered[date_column], errors='coerce')
    return df_filtered[
        (df_filtered[date_column].dt.month == mes) &
        (df_filtered[date_column].dt.year == ano)
    ]

def calcular_metricas(mes, ano):
    entradas_df = load_data(ENTRADAS_FILE)
    saidas_df = load_data(SAIDAS_FILE)
    dividas_df = load_data(DIVIDAS_FILE)

    entradas_mes = filter_by_month(entradas_df, mes, ano)
    saidas_mes = filter_by_month(saidas_df, mes, ano)

    total_entradas = entradas_mes['valor'].sum() if not entradas_mes.empty else 0
    total_saidas = saidas_mes['valor'].sum() if not saidas_mes.empty else 0
    saldo = total_entradas - total_saidas

    entradas_por_tipo = {}
    if not entradas_mes.empty:
        for _, row in entradas_mes.iterrows():
            key = f"{row['tipo']} - {row['parceiro']}"
            entradas_por_tipo[key] = entradas_por_tipo.get(key, 0) + row['valor']

    saidas_por_categoria = {}
    if not saidas_mes.empty:
        saidas_por_categoria = saidas_mes.groupby('categoria')['valor'].sum().to_dict()

    dividas_acordo = dividas_df[dividas_df['status'] == 'Em acordo']
    dividas_negativadas = dividas_df[dividas_df['status'] == 'Negativada']

    total_dividas_acordo = (dividas_acordo['valor_total'] - dividas_acordo['valor_pago']).sum() if not dividas_acordo.empty else 0
    qtd_dividas_acordo = len(dividas_acordo)

    total_dividas_negativadas = (dividas_negativadas['valor_total'] - dividas_negativadas['valor_pago']).sum() if not dividas_negativadas.empty else 0
    qtd_dividas_negativadas = len(dividas_negativadas)

    return {
        'saldo': saldo,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'entradas_por_tipo': entradas_por_tipo,
        'saidas_por_categoria': saidas_por_categoria,
        'total_dividas_acordo': total_dividas_acordo,
        'qtd_dividas_acordo': qtd_dividas_acordo,
        'total_dividas_negativadas': total_dividas_negativadas,
        'qtd_dividas_negativadas': qtd_dividas_negativadas
    }

# ============================================
# PÁGINAS
# ============================================

def render_dashboard(mes, ano):
    st.title("💰 Dashboard Financeiro")
    st.info(f"📅 Período: {mes:02d}/{ano}")
    st.markdown("<br>", unsafe_allow_html=True)

    metricas = calcular_metricas(mes, ano)

    st.markdown("### 💵 Visão Geral")
    cols = st.columns(3)

    with cols[0]:
        saldo_emoji = "📈" if metricas['saldo'] >= 0 else "📉"
        if SHADCN_AVAILABLE:
            with card():
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>{saldo_emoji} Saldo em Conta</h4>", unsafe_allow_html=True)
                saldo_color = "#10b981" if metricas['saldo'] >= 0 else "#ef4444"
                st.markdown(f"<h1 style='margin:10px 0;color:{saldo_color};'>{format_currency(metricas['saldo'])}</h1>", unsafe_allow_html=True)
                st.caption("Entradas - Saídas do mês")
        else:
            st.metric("💵 Saldo em Conta", format_currency(metricas['saldo']))

    with cols[1]:
        if SHADCN_AVAILABLE:
            with card():
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>📈 Total de Entradas</h4>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='margin:10px 0;color:#10b981;'>{format_currency(metricas['total_entradas'])}</h1>", unsafe_allow_html=True)
                st.caption("Receitas do mês")
        else:
            st.metric("📈 Total de Entradas", format_currency(metricas['total_entradas']))

    with cols[2]:
        if SHADCN_AVAILABLE:
            with card():
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>📉 Total de Saídas</h4>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='margin:10px 0;color:#ef4444;'>{format_currency(metricas['total_saidas'])}</h1>", unsafe_allow_html=True)
                st.caption("Despesas do mês")
        else:
            st.metric("📉 Total de Saídas", format_currency(metricas['total_saidas']))

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 💳 Situação de Dívidas")
    cols = st.columns(4)

    total_dividas = metricas['total_dividas_acordo'] + metricas['total_dividas_negativadas']
    patrimonio_liquido = metricas['saldo'] - total_dividas

    with cols[0]:
        if SHADCN_AVAILABLE:
            with card():
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>🤝 Dívidas em Acordo</h4>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='margin:10px 0;color:#f59e0b;'>{format_currency(metricas['total_dividas_acordo'])}</h2>", unsafe_allow_html=True)
                badge("warning", f"{metricas['qtd_dividas_acordo']} dívida(s)")
        else:
            st.metric("🤝 Dívidas em Acordo", format_currency(metricas['total_dividas_acordo']), f"{metricas['qtd_dividas_acordo']} dívida(s)")

    with cols[1]:
        if SHADCN_AVAILABLE:
            with card():
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>⚠️ Dívidas Negativadas</h4>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='margin:10px 0;color:#ef4444;'>{format_currency(metricas['total_dividas_negativadas'])}</h2>", unsafe_allow_html=True)
                badge("destructive", f"{metricas['qtd_dividas_negativadas']} dívida(s)")
        else:
            st.metric("⚠️ Dívidas Negativadas", format_currency(metricas['total_dividas_negativadas']), f"{metricas['qtd_dividas_negativadas']} dívida(s)")

    with cols[2]:
        if SHADCN_AVAILABLE:
            with card():
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>💰 Total de Dívidas</h4>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='margin:10px 0;color:#8b5cf6;'>{format_currency(total_dividas)}</h2>", unsafe_allow_html=True)
                badge("secondary", f"{metricas['qtd_dividas_acordo'] + metricas['qtd_dividas_negativadas']} dívida(s)")
        else:
            st.metric("💰 Total de Dívidas", format_currency(total_dividas))

    with cols[3]:
        if SHADCN_AVAILABLE:
            with card():
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>📊 Patrimônio Líquido</h4>", unsafe_allow_html=True)
                patrimonio_color = "#10b981" if patrimonio_liquido >= 0 else "#ef4444"
                st.markdown(f"<h2 style='margin:10px 0;color:{patrimonio_color};'>{format_currency(patrimonio_liquido)}</h2>", unsafe_allow_html=True)
                st.caption("Saldo - Dívidas")
        else:
            st.metric("📊 Patrimônio Líquido", format_currency(patrimonio_liquido))

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 📊 Análise Detalhada")
    tab1, tab2 = st.tabs(["📈 Entradas por Fonte", "📉 Saídas por Categoria"])

    with tab1:
        if metricas['entradas_por_tipo']:
            fig = px.pie(
                values=list(metricas['entradas_por_tipo'].values()),
                names=list(metricas['entradas_por_tipo'].keys()),
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Greens_r
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma entrada registrada no período")

    with tab2:
        if metricas['saidas_por_categoria']:
            fig = px.pie(
                values=list(metricas['saidas_por_categoria'].values()),
                names=list(metricas['saidas_por_categoria'].keys()),
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Reds_r
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma saída registrada no período")

def render_entradas():
    st.title("📈 Gerenciar Entradas")

    with st.expander("➕ Adicionar Nova Entrada", expanded=False):
        with st.form("form_entrada"):
            col1, col2 = st.columns(2)
            with col1:
                data = st.date_input("Data", value=date.today())
                tipo = st.selectbox("Tipo", ["Salário", "Renda Extra"])
                parceiro = st.selectbox("Parceiro", ["Lorena", "Victor"])
            with col2:
                valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
                descricao = st.text_input("Descrição")
            submitted = st.form_submit_button("💾 Salvar Entrada", use_container_width=True, type="primary")
            if submitted:
                if valor > 0:
                    add_entrada(data, tipo, parceiro, valor, descricao)
                    st.success("✅ Entrada adicionada com sucesso!")
                    st.rerun()
                else:
                    st.error("⚠️ O valor deve ser maior que zero")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Histórico de Entradas")

    df = load_data(ENTRADAS_FILE)
    if df.empty:
        st.info("📭 Nenhuma entrada registrada ainda.")
        return

    df = df.sort_values('data', ascending=False)

    col1, col2, col3 = st.columns(3)
    with col1:
        meses = sorted(df['data'].dt.month.dropna().unique())
        mes_filter = st.selectbox("Mês", ["Todos"] + meses)
    with col2:
        anos = sorted(df['data'].dt.year.dropna().unique(), reverse=True)
        ano_filter = st.selectbox("Ano", ["Todos"] + anos)
    with col3:
        parceiros = sorted(df['parceiro'].dropna().unique())
        parceiro_filter = st.selectbox("Parceiro", ["Todos"] + parceiros)

    df_filtered = df.copy()
    if mes_filter != "Todos":
        df_filtered = df_filtered[df_filtered['data'].dt.month == mes_filter]
    if ano_filter != "Todos":
        df_filtered = df_filtered[df_filtered['data'].dt.year == ano_filter]
    if parceiro_filter != "Todos":
        df_filtered = df_filtered[df_filtered['parceiro'] == parceiro_filter]

    if df_filtered.empty:
        st.info("Nenhuma entrada com os filtros aplicados.")
        return

    total = df_filtered['valor'].sum()
    if SHADCN_AVAILABLE:
        with card():
            st.markdown(f"<h3 style='color:#10b981;margin:0;'>💰 Total do período: {format_currency(total)}</h3>", unsafe_allow_html=True)
    else:
        st.success(f"💰 Total do período: {format_currency(total)}")

    st.markdown("<br>", unsafe_allow_html=True)

    df_display = df_filtered.copy()
    df_display['data_fmt'] = df_display['data'].dt.strftime('%d/%m/%Y')
    df_display['valor_fmt'] = df_display['valor'].apply(format_currency)

    # Reset index to access original index
    df_display = df_display.reset_index()

    for _, row in df_display.iterrows():
        original_idx = row['index']
        if SHADCN_AVAILABLE:
            with card():
                cols = st.columns([2, 2, 2, 2, 3, 1])
                cols[0].markdown(f"**📅 {row['data_fmt']}**")
                cols[1].write(row['tipo'])
                cols[2].write(row['parceiro'])
                cols[3].markdown(f"**{row['valor_fmt']}**")
                cols[4].write(row['descricao'] if pd.notna(row['descricao']) else "")
                if cols[5].button("🗑️", key=f"del_ent_{original_idx}"):
                    delete_entrada(original_idx)
                    st.rerun()
        else:
            cols = st.columns([2, 2, 2, 2, 3, 1])
            cols[0].write(row['data_fmt'])
            cols[1].write(row['tipo'])
            cols[2].write(row['parceiro'])
            cols[3].write(row['valor_fmt'])
            cols[4].write(row['descricao'] if pd.notna(row['descricao']) else "")
            if cols[5].button("🗑️", key=f"del_ent_{original_idx}"):
                delete_entrada(original_idx)
                st.rerun()

def render_saidas():
    st.title("📉 Gerenciar Saídas")

    with st.expander("➕ Adicionar Nova Saída", expanded=False):
        with st.form("form_saida"):
            col1, col2 = st.columns(2)
            with col1:
                data = st.date_input("Data", value=date.today())
                categoria = st.selectbox("Categoria", [
                    "Alimentação", "Moradia", "Transporte", "Saúde", "Lazer",
                    "Educação", "Vestuário", "Serviços", "Dívida", "Outros"
                ])
            with col2:
                valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
                descricao = st.text_input("Descrição")
            submitted = st.form_submit_button("💾 Salvar Saída", use_container_width=True, type="primary")
            if submitted:
                if valor > 0:
                    add_saida(data, categoria, valor, descricao)
                    st.success("✅ Saída adicionada com sucesso!")
                    st.rerun()
                else:
                    st.error("⚠️ O valor deve ser maior que zero")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Histórico de Saídas")

    df = load_data(SAIDAS_FILE)
    if df.empty:
        st.info("📭 Nenhuma saída registrada ainda.")
        return

    df = df.sort_values('data', ascending=False)

    col1, col2, col3 = st.columns(3)
    with col1:
        meses = sorted(df['data'].dt.month.dropna().unique())
        mes_filter = st.selectbox("Mês", ["Todos"] + meses)
    with col2:
        anos = sorted(df['data'].dt.year.dropna().unique(), reverse=True)
        ano_filter = st.selectbox("Ano", ["Todos"] + anos)
    with col3:
        categorias = sorted(df['categoria'].dropna().unique())
        categoria_filter = st.selectbox("Categoria", ["Todos"] + categorias)

    df_filtered = df.copy()
    if mes_filter != "Todos":
        df_filtered = df_filtered[df_filtered['data'].dt.month == mes_filter]
    if ano_filter != "Todos":
        df_filtered = df_filtered[df_filtered['data'].dt.year == ano_filter]
    if categoria_filter != "Todos":
        df_filtered = df_filtered[df_filtered['categoria'] == categoria_filter]

    if df_filtered.empty:
        st.info("Nenhuma saída com os filtros aplicados.")
        return

    total = df_filtered['valor'].sum()
    if SHADCN_AVAILABLE:
        with card():
            st.markdown(f"<h3 style='color:#ef4444;margin:0;'>💰 Total do período: {format_currency(total)}</h3>", unsafe_allow_html=True)
    else:
        st.error(f"💰 Total do período: {format_currency(total)}")

    st.markdown("<br>", unsafe_allow_html=True)

    df_display = df_filtered.copy()
    df_display['data_fmt'] = df_display['data'].dt.strftime('%d/%m/%Y')
    df_display['valor_fmt'] = df_display['valor'].apply(format_currency)

    df_display = df_display.reset_index()

    for _, row in df_display.iterrows():
        original_idx = row['index']
        if SHADCN_AVAILABLE:
            with card():
                cols = st.columns([2, 2, 2, 3, 1])
                cols[0].markdown(f"**📅 {row['data_fmt']}**")
                cols[1].write(row['categoria'])
                cols[2].markdown(f"**{row['valor_fmt']}**")
                cols[3].write(row['descricao'] if pd.notna(row['descricao']) else "")
                if cols[4].button("🗑️", key=f"del_sai_{original_idx}"):
                    delete_saida(original_idx)
                    st.rerun()
        else:
            cols = st.columns([2, 2, 2, 3, 1])
            cols[0].write(row['data_fmt'])
            cols[1].write(row['categoria'])
            cols[2].write(row['valor_fmt'])
            cols[3].write(row['descricao'] if pd.notna(row['descricao']) else "")
            if cols[4].button("🗑️", key=f"del_sai_{original_idx}"):
                delete_saida(original_idx)
                st.rerun()

def render_dividas():
    st.title("💳 Gerenciar Dívidas")

    with st.expander("➕ Adicionar Nova Dívida", expanded=False):
        with st.form("form_divida"):
            col1, col2 = st.columns(2)
            with col1:
                credor = st.text_input("Credor")
                valor_total = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01, format="%.2f")
                valor_pago = st.number_input("Valor Já Pago (R$)", min_value=0.0, step=0.01, format="%.2f")
            with col2:
                status = st.selectbox("Status", ["Em acordo", "Negativada"])
                data_inicio = st.date_input("Data de Início", value=date.today())
                descricao = st.text_area("Descrição/Observações")
            submitted = st.form_submit_button("💾 Salvar Dívida", use_container_width=True, type="primary")
            if submitted:
                if valor_total > 0 and credor.strip():
                    if valor_pago <= valor_total:
                        add_divida(credor, valor_total, valor_pago, status, data_inicio, descricao)
                        st.success("✅ Dívida adicionada com sucesso!")
                        st.rerun()
                    else:
                        st.error("⚠️ Valor pago não pode exceder o total.")
                else:
                    st.error("⚠️ Preencha credor e valor total.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Dívidas Cadastradas")

    df = load_data(DIVIDAS_FILE)
    if df.empty:
        st.info("📭 Nenhuma dívida registrada.")
        return

    df['saldo_devedor'] = df['valor_total'] - df['valor_pago']
    df['percentual_pago'] = (df['valor_pago'] / df['valor_total'] * 100).round(1)
    df = df.sort_values('data_inicio', ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["Todos", "Em acordo", "Negativada"])
    with col2:
        ordenar = st.selectbox("Ordenar por", ["Saldo Devedor (Maior)", "Saldo Devedor (Menor)", "Data (Mais Recente)"])

    df_filtered = df if status_filter == "Todos" else df[df['status'] == status_filter]

    if ordenar == "Saldo Devedor (Maior)":
        df_filtered = df_filtered.sort_values('saldo_devedor', ascending=False)
    elif ordenar == "Saldo Devedor (Menor)":
        df_filtered = df_filtered.sort_values('saldo_devedor', ascending=True)
    else:
        df_filtered = df_filtered.sort_values('data_inicio', ascending=False)

    if df_filtered.empty:
        st.info("Nenhuma dívida com os filtros aplicados.")
        return

    total_saldo = df_filtered['saldo_devedor'].sum()
    if SHADCN_AVAILABLE:
        with card():
            st.markdown(f"<h3 style='color:#8b5cf6;margin:0;'>💰 Saldo devedor total: {format_currency(total_saldo)}</h3>", unsafe_allow_html=True)
    else:
        st.info(f"💰 Saldo devedor total: {format_currency(total_saldo)}")

    st.markdown("<br>", unsafe_allow_html=True)

    df_filtered = df_filtered.reset_index()

    for _, row in df_filtered.iterrows():
        original_idx = row['index']
        status_icon = "🤝" if row['status'] == "Em acordo" else "⚠️"
        status_color = "warning" if row['status'] == "Em acordo" else "destructive"

        if SHADCN_AVAILABLE:
            with card():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"### {status_icon} {row['credor']}")
                    badge(status_color, row['status'])
                    st.caption(f"📅 Início: {row['data_inicio'].strftime('%d/%m/%Y')}")
                    if pd.notna(row['descricao']):
                        st.text(row['descricao'])
                with col2:
                    st.markdown("**Valor Total**")
                    st.markdown(f"<h4 style='color:#64748b;'>{format_currency(row['valor_total'])}</h4>", unsafe_allow_html=True)
                    st.markdown("**Valor Pago**")
                    st.markdown(f"<h4 style='color:#10b981;'>{format_currency(row['valor_pago'])}</h4>", unsafe_allow_html=True)
                with col3:
                    st.markdown("**Saldo Devedor**")
                    st.markdown(f"<h4 style='color:#ef4444;'>{format_currency(row['saldo_devedor'])}</h4>", unsafe_allow_html=True)
                    st.progress(min(1.0, row['percentual_pago'] / 100))
                    st.caption(f"✅ {row['percentual_pago']:.1f}% pago")

                colA, colB = st.columns(2)
                if colA.button("💰 Registrar Pagamento", key=f"pay_{original_idx}", use_container_width=True):
                    st.session_state[f'show_payment_{original_idx}'] = True
                if colB.button("🗑️ Excluir", key=f"del_div_{original_idx}", use_container_width=True):
                    delete_divida(original_idx)
                    st.rerun()

                if st.session_state.get(f'show_payment_{original_idx}', False):
                    st.markdown("---")
                    with st.form(key=f"pay_form_{original_idx}"):
                        st.markdown("### 💰 Registrar Pagamento")
                        saldo = row['saldo_devedor']
                        valor_adicional = st.number_input(
                            "Valor (R$)",
                            min_value=0.01,
                            max_value=float(saldo),
                            step=0.01,
                            format="%.2f"
                        )
                        c1, c2 = st.columns(2)
                        if c1.form_submit_button("✅ Confirmar", use_container_width=True, type="primary"):
                            novo_pago = row['valor_pago'] + valor_adicional
                            update_divida(original_idx, novo_pago)
                            st.session_state[f'show_payment_{original_idx}'] = False
                            st.success("Pagamento registrado!")
                            st.rerun()
                        if c2.form_submit_button("❌ Cancelar", use_container_width=True):
                            st.session_state[f'show_payment_{original_idx}'] = False
                            st.rerun()
        else:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"### {status_icon} {row['credor']}")
                    st.caption(f"Status: {row['status']}")
                    st.caption(f"📅 Início: {row['data_inicio'].strftime('%d/%m/%Y')}")
                    if pd.notna(row['descricao']):
                        st.text(row['descricao'])
                with col2:
                    st.metric("Total", format_currency(row['valor_total']))
                    st.metric("Pago", format_currency(row['valor_pago']))
                with col3:
                    st.metric("Saldo", format_currency(row['saldo_devedor']))
                    st.progress(min(1.0, row['percentual_pago'] / 100))
                    st.caption(f"✅ {row['percentual_pago']:.1f}% pago")

                colA, colB = st.columns(2)
                if colA.button("💰 Pagar", key=f"pay_{original_idx}"):
                    st.session_state[f'show_payment_{original_idx}'] = True
                if colB.button("🗑️ Excluir", key=f"del_div_{original_idx}"):
                    delete_divida(original_idx)
                    st.rerun()

                if st.session_state.get(f'show_payment_{original_idx}', False):
                    with st.form(key=f"pay_form_{original_idx}"):
                        valor_adicional = st.number_input(
                            "Valor (R$)",
                            min_value=0.01,
                            max_value=float(row['saldo_devedor']),
                            step=0.01,
                            format="%.2f"
                        )
                        c1, c2 = st.columns(2)
                        if c1.form_submit_button("✅ Confirmar"):
                            novo_pago = row['valor_pago'] + valor_adicional
                            update_divida(original_idx, novo_pago)
                            st.session_state[f'show_payment_{original_idx}'] = False
                            st.success("Pagamento registrado!")
                            st.rerun()
                        if c2.form_submit_button("❌ Cancelar"):
                            st.session_state[f'show_payment_{original_idx}'] = False
                            st.rerun()
                st.divider()

# ============================================
# MENU LATERAL COM BOTÕES
# ============================================

def main():
    init_csv_files()

    if 'mes_selecionado' not in st.session_state:
        st.session_state.mes_selecionado, st.session_state.ano_selecionado = get_mes_vigente()
    if 'pagina' not in st.session_state:
        st.session_state.pagina = "Dashboard"

    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/money-bag.png", width=80)
        st.title("Gestão Financeira")
        st.markdown("---")
        
        # Período
        st.subheader("📅 Período")
        col1, col2 = st.columns(2)
        with col1:
            mes = st.selectbox("Mês", list(range(1, 13)), index=st.session_state.mes_selecionado - 1)
        with col2:
            ano = st.number_input("Ano", min_value=2020, max_value=2030, value=st.session_state.ano_selecionado)
        st.session_state.mes_selecionado = mes
        st.session_state.ano_selecionado = ano

        st.markdown("---")
        st.subheader("📱 Navegação")

        # Botões de navegação
        if SHADCN_AVAILABLE:
            if button("🏠 Dashboard", variant="outline", key="btn_dash"):
                st.session_state.pagina = "Dashboard"
            if button("📈 Entradas", variant="outline", key="btn_ent"):
                st.session_state.pagina = "Entradas"
            if button("📉 Saídas", variant="outline", key="btn_sai"):
                st.session_state.pagina = "Saídas"
            if button("💳 Dívidas", variant="outline", key="btn_div"):
                st.session_state.pagina = "Dívidas"
        else:
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.pagina = "Dashboard"
            if st.button("📈 Entradas", use_container_width=True):
                st.session_state.pagina = "Entradas"
            if st.button("📉 Saídas", use_container_width=True):
                st.session_state.pagina = "Saídas"
            if st.button("💳 Dívidas", use_container_width=True):
                st.session_state.pagina = "Dívidas"

        st.markdown("---")
        st.caption("💡 Use o Dashboard para visão geral!")
        st.caption("📊 Sistema v1.0")

    # Renderizar página selecionada
    pagina = st.session_state.pagina
    if pagina == "Dashboard":
        render_dashboard(st.session_state.mes_selecionado, st.session_state.ano_selecionado)
    elif pagina == "Entradas":
        render_entradas()
    elif pagina == "Saídas":
        render_saidas()
    elif pagina == "Dívidas":
        render_dividas()

if __name__ == "__main__":
    main()