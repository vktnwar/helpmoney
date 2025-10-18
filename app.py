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
import plotly.graph_objects as go
from datetime import datetime, date
from pathlib import Path
import os

# Importar apenas os componentes que existem
try:
    from streamlit_shadcn_ui import card, badges
    SHADCN_AVAILABLE = True
except:
    SHADCN_AVAILABLE = False

# ============================================
# CONFIGURAÇÃO INICIAL
# ============================================

# Configuração da página
st.set_page_config(
    page_title="Gestão Financeira",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Diretório para armazenar os dados
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Arquivos CSV
ENTRADAS_FILE = DATA_DIR / "entradas.csv"
SAIDAS_FILE = DATA_DIR / "saidas.csv"
DIVIDAS_FILE = DATA_DIR / "dividas.csv"

# ============================================
# FUNÇÕES DE GERENCIAMENTO DE DADOS
# ============================================

def init_csv_files():
    """Inicializa os arquivos CSV se não existirem"""
    
    # Entradas
    if not ENTRADAS_FILE.exists():
        df = pd.DataFrame(columns=['data', 'tipo', 'parceiro', 'valor', 'descricao'])
        df.to_csv(ENTRADAS_FILE, index=False)
    
    # Saídas
    if not SAIDAS_FILE.exists():
        df = pd.DataFrame(columns=['data', 'categoria', 'valor', 'descricao'])
        df.to_csv(SAIDAS_FILE, index=False)
    
    # Dívidas
    if not DIVIDAS_FILE.exists():
        df = pd.DataFrame(columns=['credor', 'valor_total', 'valor_pago', 'status', 'data_inicio', 'descricao'])
        df.to_csv(DIVIDAS_FILE, index=False)

def load_data(file_path):
    """Carrega dados de um arquivo CSV"""
    if file_path.exists():
        df = pd.read_csv(file_path)
        return df
    return pd.DataFrame()

def save_data(df, file_path):
    """Salva dados em um arquivo CSV"""
    df.to_csv(file_path, index=False)

def add_entrada(data, tipo, parceiro, valor, descricao):
    """Adiciona uma nova entrada"""
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
    """Adiciona uma nova saída"""
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
    """Adiciona uma nova dívida"""
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

def update_divida(index, valor_pago):
    """Atualiza o valor pago de uma dívida"""
    df = load_data(DIVIDAS_FILE)
    if index < len(df):
        df.loc[index, 'valor_pago'] = valor_pago
        save_data(df, DIVIDAS_FILE)

def delete_divida(index):
    """Remove uma dívida"""
    df = load_data(DIVIDAS_FILE)
    if index < len(df):
        df = df.drop(index).reset_index(drop=True)
        save_data(df, DIVIDAS_FILE)

def delete_entrada(index):
    """Remove uma entrada"""
    df = load_data(ENTRADAS_FILE)
    if index < len(df):
        df = df.drop(index).reset_index(drop=True)
        save_data(df, ENTRADAS_FILE)

def delete_saida(index):
    """Remove uma saída"""
    df = load_data(SAIDAS_FILE)
    if index < len(df):
        df = df.drop(index).reset_index(drop=True)
        save_data(df, SAIDAS_FILE)

# ============================================
# FUNÇÕES DE CÁLCULO E MÉTRICAS
# ============================================

def get_mes_vigente():
    """Retorna o mês e ano atual"""
    hoje = datetime.now()
    return hoje.month, hoje.year

def filter_by_month(df, mes, ano, date_column='data'):
    """Filtra dataframe por mês e ano"""
    if df.empty:
        return df
    df[date_column] = pd.to_datetime(df[date_column])
    return df[(df[date_column].dt.month == mes) & (df[date_column].dt.year == ano)]

def calcular_metricas(mes, ano):
    """Calcula todas as métricas financeiras"""
    
    # Carregar dados
    entradas_df = load_data(ENTRADAS_FILE)
    saidas_df = load_data(SAIDAS_FILE)
    dividas_df = load_data(DIVIDAS_FILE)
    
    # Filtrar por mês
    entradas_mes = filter_by_month(entradas_df, mes, ano)
    saidas_mes = filter_by_month(saidas_df, mes, ano)
    
    # Total de entradas
    total_entradas = entradas_mes['valor'].sum() if not entradas_mes.empty else 0
    
    # Total de saídas
    total_saidas = saidas_mes['valor'].sum() if not saidas_mes.empty else 0
    
    # Saldo em conta
    saldo = total_entradas - total_saidas
    
    # Entradas por tipo
    entradas_por_tipo = {}
    if not entradas_mes.empty:
        for _, row in entradas_mes.iterrows():
            key = f"{row['tipo']} - {row['parceiro']}"
            entradas_por_tipo[key] = entradas_por_tipo.get(key, 0) + row['valor']
    
    # Saídas por categoria
    saidas_por_categoria = {}
    if not saidas_mes.empty:
        saidas_por_categoria = saidas_mes.groupby('categoria')['valor'].sum().to_dict()
    
    # Dívidas
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
# COMPONENTES DA INTERFACE
# ============================================

def render_dashboard(mes, ano):
    """Renderiza o dashboard principal"""
    
    st.title("💰 Dashboard Financeiro")
    st.info(f"📅 Período: {mes:02d}/{ano}")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Calcular métricas
    metricas = calcular_metricas(mes, ano)
    
    # Linha 1: Métricas principais
    st.markdown("### 💵 Visão Geral")
    cols = st.columns(3)
    
    with cols[0]:
        saldo_emoji = "📈" if metricas['saldo'] >= 0 else "📉"
        if SHADCN_AVAILABLE:
            with card(key="card_saldo"):
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>{saldo_emoji} Saldo em Conta</h4>", unsafe_allow_html=True)
                saldo_color = "#10b981" if metricas['saldo'] >= 0 else "#ef4444"
                st.markdown(f"<h1 style='margin:10px 0;color:{saldo_color};'>R$ {metricas['saldo']:,.2f}</h1>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                st.caption("Entradas - Saídas do mês")
        else:
            st.metric("💵 Saldo em Conta", f"R$ {metricas['saldo']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    with cols[1]:
        if SHADCN_AVAILABLE:
            with card(key="card_entradas"):
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>📈 Total de Entradas</h4>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='margin:10px 0;color:#10b981;'>R$ {metricas['total_entradas']:,.2f}</h1>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                st.caption("Receitas do mês")
        else:
            st.metric("📈 Total de Entradas", f"R$ {metricas['total_entradas']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    with cols[2]:
        if SHADCN_AVAILABLE:
            with card(key="card_saidas"):
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>📉 Total de Saídas</h4>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='margin:10px 0;color:#ef4444;'>R$ {metricas['total_saidas']:,.2f}</h1>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                st.caption("Despesas do mês")
        else:
            st.metric("📉 Total de Saídas", f"R$ {metricas['total_saidas']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Linha 2: Dívidas
    st.markdown("### 💳 Situação de Dívidas")
    cols = st.columns(4)
    
    with cols[0]:
        if SHADCN_AVAILABLE:
            with card(key="card_dividas_acordo"):
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>🤝 Dívidas em Acordo</h4>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='margin:10px 0;color:#f59e0b;'>R$ {metricas['total_dividas_acordo']:,.2f}</h2>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                badges(badge_list=[("warning", f"{metricas['qtd_dividas_acordo']} dívida(s)")], key="badge_acordo")
        else:
            st.metric("🤝 Dívidas em Acordo", f"R$ {metricas['total_dividas_acordo']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), f"{metricas['qtd_dividas_acordo']} dívida(s)")
    
    with cols[1]:
        if SHADCN_AVAILABLE:
            with card(key="card_dividas_negativadas"):
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>⚠️ Dívidas Negativadas</h4>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='margin:10px 0;color:#ef4444;'>R$ {metricas['total_dividas_negativadas']:,.2f}</h2>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                badges(badge_list=[("destructive", f"{metricas['qtd_dividas_negativadas']} dívida(s)")], key="badge_negativadas")
        else:
            st.metric("⚠️ Dívidas Negativadas", f"R$ {metricas['total_dividas_negativadas']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), f"{metricas['qtd_dividas_negativadas']} dívida(s)")
    
    with cols[2]:
        total_dividas = metricas['total_dividas_acordo'] + metricas['total_dividas_negativadas']
        if SHADCN_AVAILABLE:
            with card(key="card_total_dividas"):
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>💰 Total de Dívidas</h4>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='margin:10px 0;color:#8b5cf6;'>R$ {total_dividas:,.2f}</h2>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                badges(badge_list=[("secondary", f"{metricas['qtd_dividas_acordo'] + metricas['qtd_dividas_negativadas']} dívida(s)")], key="badge_total")
        else:
            st.metric("💰 Total de Dívidas", f"R$ {total_dividas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    with cols[3]:
        patrimonio_liquido = metricas['saldo'] - total_dividas
        if SHADCN_AVAILABLE:
            with card(key="card_patrimonio"):
                st.markdown(f"<h4 style='margin:0;color:#64748b;'>📊 Patrimônio Líquido</h4>", unsafe_allow_html=True)
                patrimonio_color = "#10b981" if patrimonio_liquido >= 0 else "#ef4444"
                st.markdown(f"<h2 style='margin:10px 0;color:{patrimonio_color};'>R$ {patrimonio_liquido:,.2f}</h2>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                st.caption("Saldo - Dívidas")
        else:
            st.metric("📊 Patrimônio Líquido", f"R$ {patrimonio_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráficos
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
    """Renderiza a página de entradas"""
    
    st.title("📈 Gerenciar Entradas")
    
    # Formulário de adição
    with st.expander("➕ Adicionar Nova Entrada", expanded=False):
        with st.form("form_entrada"):
            col1, col2 = st.columns(2)
            
            with col1:
                data = st.date_input("Data", value=date.today())
                tipo = st.selectbox("Tipo", ["Salário", "Renda Extra"])
                parceiro = st.selectbox("Parceiro", ["Parceiro A", "Parceiro B"])
            
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
    
    # Listagem de entradas
    st.subheader("📋 Histórico de Entradas")
    
    df = load_data(ENTRADAS_FILE)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df = df.sort_values('data', ascending=False)
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            meses = df['data'].dt.month.unique()
            mes_filter = st.selectbox("Filtrar por Mês", ["Todos"] + sorted(meses.tolist()))
        with col2:
            anos = df['data'].dt.year.unique()
            ano_filter = st.selectbox("Filtrar por Ano", ["Todos"] + sorted(anos.tolist(), reverse=True))
        with col3:
            parceiros = df['parceiro'].unique()
            parceiro_filter = st.selectbox("Filtrar por Parceiro", ["Todos"] + sorted(parceiros.tolist()))
        
        # Aplicar filtros
        df_filtered = df.copy()
        if mes_filter != "Todos":
            df_filtered = df_filtered[df_filtered['data'].dt.month == mes_filter]
        if ano_filter != "Todos":
            df_filtered = df_filtered[df_filtered['data'].dt.year == ano_filter]
        if parceiro_filter != "Todos":
            df_filtered = df_filtered[df_filtered['parceiro'] == parceiro_filter]
        
        # Exibir dados
        if not df_filtered.empty:
            total = df_filtered['valor'].sum()
            if SHADCN_AVAILABLE:
                with card(key="card_total_entradas"):
                    st.markdown(f"<h3 style='color:#10b981;margin:0;'>💰 Total do período: R$ {total:,.2f}</h3>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
            else:
                st.success(f"💰 Total do período: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Formatar para exibição
            df_display = df_filtered.copy()
            df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
            df_display['valor'] = df_display['valor'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            # Mostrar tabela
            for idx, row in df_display.iterrows():
                if SHADCN_AVAILABLE:
                    with card(key=f"entrada_card_{idx}"):
                        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 3, 1])
                        col1.markdown(f"**📅 {row['data']}**")
                        col2.write(row['tipo'])
                        col3.write(row['parceiro'])
                        col4.markdown(f"**{row['valor']}**")
                        col5.write(row['descricao'])
                        if col6.button("🗑️", key=f"del_entrada_{idx}"):
                            delete_entrada(idx)
                            st.rerun()
                else:
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 3, 1])
                    col1.write(row['data'])
                    col2.write(row['tipo'])
                    col3.write(row['parceiro'])
                    col4.write(row['valor'])
                    col5.write(row['descricao'])
                    if col6.button("🗑️", key=f"del_entrada_{idx}"):
                        delete_entrada(idx)
                        st.rerun()
        else:
            st.info("Nenhuma entrada encontrada com os filtros aplicados")
    else:
        st.info("📭 Nenhuma entrada registrada ainda. Comece adicionando sua primeira entrada!")

def render_saidas():
    """Renderiza a página de saídas"""
    
    st.title("📉 Gerenciar Saídas")
    
    # Formulário de adição
    with st.expander("➕ Adicionar Nova Saída", expanded=False):
        with st.form("form_saida"):
            col1, col2 = st.columns(2)
            
            with col1:
                data = st.date_input("Data", value=date.today())
                categoria = st.selectbox(
                    "Categoria",
                    ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", 
                     "Educação", "Vestuário", "Serviços", "Outros"]
                )
            
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
    
    # Listagem de saídas
    st.subheader("📋 Histórico de Saídas")
    
    df = load_data(SAIDAS_FILE)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df = df.sort_values('data', ascending=False)
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            meses = df['data'].dt.month.unique()
            mes_filter = st.selectbox("Filtrar por Mês", ["Todos"] + sorted(meses.tolist()))
        with col2:
            anos = df['data'].dt.year.unique()
            ano_filter = st.selectbox("Filtrar por Ano", ["Todos"] + sorted(anos.tolist(), reverse=True))
        with col3:
            categorias = df['categoria'].unique()
            categoria_filter = st.selectbox("Filtrar por Categoria", ["Todos"] + sorted(categorias.tolist()))
        
        # Aplicar filtros
        df_filtered = df.copy()
        if mes_filter != "Todos":
            df_filtered = df_filtered[df_filtered['data'].dt.month == mes_filter]
        if ano_filter != "Todos":
            df_filtered = df_filtered[df_filtered['data'].dt.year == ano_filter]
        if categoria_filter != "Todos":
            df_filtered = df_filtered[df_filtered['categoria'] == categoria_filter]
        
        # Exibir dados
        if not df_filtered.empty:
            total = df_filtered['valor'].sum()
            if SHADCN_AVAILABLE:
                with card(key="card_total_saidas"):
                    st.markdown(f"<h3 style='color:#ef4444;margin:0;'>💰 Total do período: R$ {total:,.2f}</h3>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
            else:
                st.error(f"💰 Total do período: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Formatar para exibição
            df_display = df_filtered.copy()
            df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
            df_display['valor'] = df_display['valor'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            # Mostrar tabela
            for idx, row in df_display.iterrows():
                if SHADCN_AVAILABLE:
                    with card(key=f"saida_card_{idx}"):
                        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 1])
                        col1.markdown(f"**📅 {row['data']}**")
                        col2.write(row['categoria'])
                        col3.markdown(f"**{row['valor']}**")
                        col4.write(row['descricao'])
                        if col5.button("🗑️", key=f"del_saida_{idx}"):
                            delete_saida(idx)
                            st.rerun()
                else:
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 1])
                    col1.write(row['data'])
                    col2.write(row['categoria'])
                    col3.write(row['valor'])
                    col4.write(row['descricao'])
                    if col5.button("🗑️", key=f"del_saida_{idx}"):
                        delete_saida(idx)
                        st.rerun()
        else:
            st.info("Nenhuma saída encontrada com os filtros aplicados")
    else:
        st.info("📭 Nenhuma saída registrada ainda. Comece adicionando sua primeira saída!")

def render_dividas():
    """Renderiza a página de dívidas"""
    
    st.title("💳 Gerenciar Dívidas")
    
    # Formulário de adição
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
                if valor_total > 0 and credor:
                    if valor_pago <= valor_total:
                        add_divida(credor, valor_total, valor_pago, status, data_inicio, descricao)
                        st.success("✅ Dívida adicionada com sucesso!")
                        st.rerun()
                    else:
                        st.error("⚠️ O valor pago não pode ser maior que o valor total")
                else:
                    st.error("⚠️ Preencha todos os campos obrigatórios")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Listagem de dívidas
    st.subheader("📋 Dívidas Cadastradas")
    
    df = load_data(DIVIDAS_FILE)
    
    if not df.empty:
        df['data_inicio'] = pd.to_datetime(df['data_inicio'])
        df['saldo_devedor'] = df['valor_total'] - df['valor_pago']
        df['percentual_pago'] = (df['valor_pago'] / df['valor_total'] * 100).round(1)
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filtrar por Status", ["Todos", "Em acordo", "Negativada"])
        with col2:
            ordenar = st.selectbox("Ordenar por", ["Saldo Devedor (Maior)", "Saldo Devedor (Menor)", "Data (Mais Recente)"])
        
        # Aplicar filtros
        df_filtered = df.copy()
        if status_filter != "Todos":
            df_filtered = df_filtered[df_filtered['status'] == status_filter]
        
        # Ordenar
        if ordenar == "Saldo Devedor (Maior)":
            df_filtered = df_filtered.sort_values('saldo_devedor', ascending=False)
        elif ordenar == "Saldo Devedor (Menor)":
            df_filtered = df_filtered.sort_values('saldo_devedor', ascending=True)
        else:
            df_filtered = df_filtered.sort_values('data_inicio', ascending=False)
        
        # Exibir dados
        if not df_filtered.empty:
            total_saldo = df_filtered['saldo_devedor'].sum()
            if SHADCN_AVAILABLE:
                with card(key="card_saldo_total_dividas"):
                    st.markdown(f"<h3 style='color:#8b5cf6;margin:0;'>💰 Saldo devedor total: R$ {total_saldo:,.2f}</h3>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
            else:
                st.info(f"💰 Saldo devedor total: R$ {total_saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Mostrar cada dívida em um card
            for idx, row in df_filtered.iterrows():
                if SHADCN_AVAILABLE:
                    with card(key=f"divida_card_{idx}"):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            status_icon = "🤝" if row['status'] == "Em acordo" else "⚠️"
                            status_color = "warning" if row['status'] == "Em acordo" else "destructive"
                            st.markdown(f"### {status_icon} {row['credor']}")
                            badges(badge_list=[(status_color, row['status'])], key=f"badge_status_{idx}")
                            st.caption(f"📅 Início: {row['data_inicio'].strftime('%d/%m/%Y')}")
                            if row['descricao']:
                                st.text(row['descricao'])
                        
                        with col2:
                            st.markdown("**Valor Total**")
                            st.markdown(f"<h3 style='color:#64748b;margin:0;'>R$ {row['valor_total']:,.2f}</h3>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                            st.markdown("**Valor Pago**")
                            st.markdown(f"<h3 style='color:#10b981;margin:0;'>R$ {row['valor_pago']:,.2f}</h3>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                        
                        with col3:
                            st.markdown("**Saldo Devedor**")
                            st.markdown(f"<h3 style='color:#ef4444;margin:0;'>R$ {row['saldo_devedor']:,.2f}</h3>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                            st.progress(row['percentual_pago'] / 100)
                            st.caption(f"✅ {row['percentual_pago']:.1f}% pago")
                        
                        # Ações
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("💰 Registrar Pagamento", key=f"pag_{idx}", use_container_width=True):
                                st.session_state[f'show_payment_{idx}'] = True
                        with col2:
                            if st.button("🗑️ Excluir Dívida", key=f"del_{idx}", use_container_width=True, type="secondary"):
                                delete_divida(idx)
                                st.rerun()
                        
                        # Modal de pagamento
                        if st.session_state.get(f'show_payment_{idx}', False):
                            st.markdown("---")
                            with st.form(key=f"form_pag_{idx}"):
                                st.markdown("### 💰 Registrar Pagamento")
                                valor_adicional = st.number_input(
                                    "Valor do Pagamento (R$)",
                                    min_value=0.01,
                                    max_value=float(row['saldo_devedor']),
                                    step=0.01,
                                    format="%.2f"
                                )
                                col1, col2 = st.columns(2)
                                if col1.form_submit_button("✅ Confirmar", use_container_width=True, type="primary"):
                                    novo_valor_pago = row['valor_pago'] + valor_adicional
                                    update_divida(idx, novo_valor_pago)
                                    st.session_state[f'show_payment_{idx}'] = False
                                    st.success("Pagamento registrado!")
                                    st.rerun()
                                if col2.form_submit_button("❌ Cancelar", use_container_width=True):
                                    st.session_state[f'show_payment_{idx}'] = False
                                    st.rerun()
                else:
                    # Versão sem shadcn-ui
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            status_icon = "🤝" if row['status'] == "Em acordo" else "⚠️"
                            st.markdown(f"### {status_icon} {row['credor']}")
                            st.caption(f"Status: {row['status']}")
                            st.caption(f"📅 Início: {row['data_inicio'].strftime('%d/%m/%Y')}")
                            if row['descricao']:
                                st.text(row['descricao'])
                        
                        with col2:
                            st.metric("Valor Total", f"R$ {row['valor_total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                            st.metric("Valor Pago", f"R$ {row['valor_pago']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        
                        with col3:
                            st.metric("Saldo Devedor", f"R$ {row['saldo_devedor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                            st.progress(row['percentual_pago'] / 100)
                            st.caption(f"✅ {row['percentual_pago']:.1f}% pago")
                        
                        # Ações
                        col1, col2, col3 = st.columns([2, 2, 6])
                        with col1:
                            if st.button("💰 Registrar Pagamento", key=f"pag_{idx}"):
                                st.session_state[f'show_payment_{idx}'] = True
                        with col2:
                            if st.button("🗑️ Excluir", key=f"del_{idx}"):
                                delete_divida(idx)
                                st.rerun()
                        
                        # Modal de pagamento
                        if st.session_state.get(f'show_payment_{idx}', False):
                            with st.form(key=f"form_pag_{idx}"):
                                valor_adicional = st.number_input(
                                    "Valor do Pagamento (R$)",
                                    min_value=0.01,
                                    max_value=float(row['saldo_devedor']),
                                    step=0.01,
                                    format="%.2f"
                                )
                                col1, col2 = st.columns(2)
                                if col1.form_submit_button("✅ Confirmar"):
                                    novo_valor_pago = row['valor_pago'] + valor_adicional
                                    update_divida(idx, novo_valor_pago)
                                    st.session_state[f'show_payment_{idx}'] = False
                                    st.success("Pagamento registrado!")
                                    st.rerun()
                                if col2.form_submit_button("❌ Cancelar"):
                                    st.session_state[f'show_payment_{idx}'] = False
                                    st.rerun()
                        
                        st.divider()
        else:
            st.info("Nenhuma dívida encontrada com os filtros aplicados")
    else:
        st.info("📭 Nenhuma dívida registrada ainda. Você está com as finanças em dia!")

# ============================================
# APLICAÇÃO PRINCIPAL
# ============================================

def main():
    """Função principal da aplicação"""
    
    # Inicializar arquivos CSV
    init_csv_files()
    
    # Inicializar session state
    if 'mes_selecionado' not in st.session_state:
        st.session_state.mes_selecionado, st.session_state.ano_selecionado = get_mes_vigente()
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/money-bag.png", width=80)
        st.title("Gestão Financeira")
        st.markdown("---")
        
        # Seletor de período
        st.subheader("📅 Período")
        col1, col2 = st.columns(2)
        with col1:
            mes = st.selectbox("Mês", range(1, 13), index=st.session_state.mes_selecionado - 1)
        with col2:
            ano = st.number_input("Ano", min_value=2020, max_value=2030, value=st.session_state.ano_selecionado)
        
        st.session_state.mes_selecionado = mes
        st.session_state.ano_selecionado = ano
        
        st.markdown("---")
        
        # Menu de navegação
        st.subheader("📱 Menu")
        opcao = st.radio(
            "Navegação",
            ["🏠 Dashboard", "📈 Entradas", "📉 Saídas", "💳 Dívidas"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Informações
        st.caption("💡 **Dica:** Use o Dashboard para ter uma visão geral das suas finanças!")
        st.caption("📊 Sistema de Gestão Financeira v1.0")
    
    # Conteúdo principal
    if opcao == "🏠 Dashboard":
        render_dashboard(st.session_state.mes_selecionado, st.session_state.ano_selecionado)
    elif opcao == "📈 Entradas":
        render_entradas()
    elif opcao == "📉 Saídas":
        render_saidas()
    elif opcao == "💳 Dívidas":
        render_dividas()

if __name__ == "__main__":
    main()