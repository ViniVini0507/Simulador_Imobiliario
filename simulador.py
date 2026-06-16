import streamlit as st
import pandas as pd
import numpy as np
import datetime
import math

# Configuração da Página
st.set_page_config(page_title="Simulador de Imóvel na Planta", page_icon="🏢", layout="wide")

st.title("🏢 Simulador de Compra de Imóvel na Planta")
st.markdown("Projete seu fluxo de caixa até a entrega das chaves e o financiamento pós-chaves.")
st.divider()

# --- 1. SELETOR DE PERFIL (Barra lateral) ---
st.sidebar.header("Configurações Gerais")
perfil = st.sidebar.radio(
    "👤 Selecione o Perfil de Simulação", 
    ["Cenário Vinicius & Ju", "Cenário João & Mari"]
)

# Definindo os valores padrão de acordo com quem está usando o app
if perfil == "Cenário Vinicius & Ju":
    default_imovel = 630000.0
    default_entrada = 40000.0
    default_mensal_const = 1480.0  
    default_meses_chaves = 30      
    default_renda = 14868.0
    opcoes_amortizacao = ["SAC"]
else:
    default_imovel = 437000.0      
    default_entrada = 65000.0      # Atualizado para 65k (Recursos próprios)
    default_mensal_const = 0.0     # Será calculado automaticamente pelo motor
    default_meses_chaves = 39      
    default_renda = 7500.0
    opcoes_amortizacao = ["PRICE", "SAC"]

# --- 2. INPUTS NA TELA PRINCIPAL ---
st.header("1. Parâmetros do Negócio")
col1, col2, col3 = st.columns(3)

with col1:
    valor_imovel = st.number_input("Valor Total do Imóvel (R$)", min_value=0.0, value=default_imovel, step=10000.0)
    entrada_inicial = st.number_input("Valor da Entrada (Aporte Inicial) (R$)", min_value=0.0, value=default_entrada, step=1000.0)
    itbi_construtora = st.radio("ITBI + Registro pagos pela construtora?", ["Sim", "Não"])

with col2:
    mensal_construtora = st.number_input("Valor da Parcela Mensal (Pré-chaves)", min_value=0.0, value=default_mensal_const, step=100.0)
    anual_construtora = st.number_input("Valor da Parcela Anual", min_value=0.0, value=0.0, step=500.0)
    meses_ate_chaves = st.number_input("Meses até a Entrega das Chaves", min_value=1, value=default_meses_chaves, step=1)

with col3:
    renda_casal = st.number_input("Renda Líquida Mensal", min_value=0.0, value=default_renda, step=500.0)
    prazo_financiamento = st.number_input("Prazo do Financiamento (Meses)", min_value=1, value=308, step=12)
    taxa_juros_anual = st.number_input("Taxa de Juros Anual do Financiamento (%)", min_value=0.0, value=11.19, step=0.1)
    valor_condominio = st.number_input("Valor do Condomínio", min_value=0.0, value=0.0, step=50.0)

# Sistema de Pagamento 
sistema_amortizacao = st.sidebar.selectbox(
    "Sistema de Amortização",
    opcoes_amortizacao,
    help="SAC: parcelas decrescentes (amortização constante). PRICE: parcelas fixas no início."
)

if renda_casal <= 0:
    st.warning("⚠️ Insira a renda líquida mensal informada para calcular o comprometimento.")

st.markdown("---")
st.header("2. Análise do Financiamento e Obra")

# --- 3. MOTOR DE CÁLCULO INTERNO ---
taxa_mensal = (taxa_juros_anual / 100) / 12  
saldo_necessario = valor_imovel - entrada_inicial

if perfil == "Cenário João & Mari":
    if sistema_amortizacao == "PRICE":
        saldo_financiado = 298000.00
        # Valores cravados conforme aprovação real da Caixa (Crédito Associativo)
        parcela_banco_inicial = 2135.00 
        ultima_parcela_banco = 2135.00
    else: 
        saldo_financiado = 250000.00 # Teto se insistirem na SAC
        amortizacao = saldo_financiado / prazo_financiamento
        parcela_banco_inicial = amortizacao + (saldo_financiado * taxa_mensal)
        ultima_parcela_banco = amortizacao + (amortizacao * taxa_mensal) # Aproximação
        
    gap_construtora = valor_imovel - entrada_inicial - saldo_financiado
    mensal_construtora_calculada = gap_construtora / meses_ate_chaves
    teto_obra = parcela_banco_inicial
    obra_inicial = 100.00 
    
else:
    # Cenário Vinicius & Ju
    saldo_financiado = saldo_necessario
    amortizacao = saldo_financiado / prazo_financiamento
    parcela_banco_inicial = amortizacao + (saldo_financiado * taxa_mensal)
    ultima_parcela_banco = amortizacao + (amortizacao * taxa_mensal)
    
    mensal_construtora_calculada = mensal_construtora 
    teto_obra = parcela_banco_inicial
    obra_inicial = 1480.52 

# Variável fundamental destravada para as próximas seções
saldo_devedor_chaves = saldo_financiado

# Exibe o diagnóstico na tela
col_res1, col_res2, col_res3 = st.columns(3)
col_res1.metric("Saldo Financiado (Banco)", f"R$ {saldo_financiado:,.2f}")

if perfil == "Cenário João & Mari":
    col_res2.metric("GAP Construtora (Buraco)", f"R$ {gap_construtora:,.2f}")
    col_res3.metric("Nova Parcela Const. (Sem INCC)", f"R$ {mensal_construtora_calculada:,.2f}")
else:
    col_res2.metric("Parcela Construtora", f"R$ {mensal_construtora_calculada:,.2f}")
    col_res3.metric("Teto Evolução Obra", f"R$ {teto_obra:,.2f}")
    
st.info(f"💡 A 1ª parcela do financiamento na entrega das chaves ({sistema_amortizacao}) será de **R$ {parcela_banco_inicial:,.2f}**.")

# --- NOVO: CONSTRUTOR DO DATAFRAME PRÉ-CHAVES ---
meses_array = np.arange(1, int(meses_ate_chaves) + 1)
evolucao_obra_array = np.linspace(obra_inicial, teto_obra, len(meses_array))
parcela_const_array = np.full(len(meses_array), mensal_construtora_calculada)

df_pre_chaves = pd.DataFrame({
    'Mês': meses_array,
    'Evolução de Obra (R$)': evolucao_obra_array,
    'Parcela Construtora (R$)': parcela_const_array,
    'Custo Total Mensal (R$)': evolucao_obra_array + parcela_const_array
})

# --- 4. FINANCIAMENTO PÓS-CHAVES ---
st.header(f"3. Financiamento Pós-Chaves ({sistema_amortizacao})")

col4, col5, col6 = st.columns(3)
col4.metric("Saldo Devedor a Financiar (R$)", f"R$ {saldo_devedor_chaves:,.2f}")
col5.metric("Primeira Parcela (Exata/Aprovada)", f"R$ {parcela_banco_inicial:,.2f}")
col6.metric("Última Parcela (Estimada)", f"R$ {ultima_parcela_banco:,.2f}")

if renda_casal > 0:
    comprometimento_renda = (parcela_banco_inicial / renda_casal) * 100
    if comprometimento_renda > 30:
        st.warning(f"⚠️ A primeira parcela compromete {comprometimento_renda:.1f}% da renda informada. O limite dos bancos é 30% da renda bruta.")
    else:
        st.success(f"✅ Comprometimento de renda em {comprometimento_renda:.1f}%.")

st.divider()

# --- 5. AMORTIZAÇÃO EXTRAORDINÁRIA ---
st.header("4. Planejamento de Amortização Extraordinária")

meta_amortizacao = st.slider("Quanto abater do saldo devedor nas chaves? (R$)", min_value=0, max_value=int(saldo_devedor_chaves), step=5000, value=50000)

if meta_amortizacao > 0:
    if sistema_amortizacao == "SAC":
        amortizacao_mensal = saldo_devedor_chaves / prazo_financiamento
        taxa_juros_mensal = 0.009521 
        reducao_parcela = (meta_amortizacao / prazo_financiamento) + (meta_amortizacao * taxa_juros_mensal)
        nova_primeira_parcela = parcela_banco_inicial - reducao_parcela
        
        st.success(f"📉 **Alternativa - Reduzir Valor:** A parcela cai de R$ {parcela_banco_inicial:,.2f} para **R$ {nova_primeira_parcela:,.2f}**.")
        
        if amortizacao_mensal > 0:
            parcelas_reduzidas = int(meta_amortizacao / amortizacao_mensal)
            anos_reduzidos = parcelas_reduzidas / 12
            st.success(f"⏳ **Alternativa - Reduzir Prazo:** Quita aproximadamente **{parcelas_reduzidas} parcelas** (redução de **{anos_reduzidos:.1f} anos**).")
    else:
        st.info("ℹ️ Na Tabela PRICE, a amortização extraordinária (lance extra com FGTS ou dinheiro) vai inteiramente para abater o Saldo Devedor. A melhor estratégia é optar por reduzir o prazo, eliminando o peso gigantesco dos juros compostos que existem no final do contrato.")
        
st.divider()

# --- 6. ORÇAMENTO Mensal ---
st.subheader("5. Simulação de Orçamento: Poupança x Obra")

col7, col8 = st.columns(2)
with col7:
    orcamento_alvo = st.number_input("Orçamento Fixo Mensal (R$)", min_value=1000.0, value=6000.0, step=500.0)
with col8:
    poupanca_minima = st.number_input("Piso Obrigatório de Poupança (R$)", min_value=0.0, value=1000.0, step=100.0)

lista_poupanca = []
lista_desembolso_real = []

for custo in df_pre_chaves['Custo Total Mensal (R$)']:
    poupanca_projetada = orcamento_alvo - custo
    
    if poupanca_projetada < poupanca_minima:
        poupanca_real = poupanca_minima
        desembolso_mensal = custo + poupanca_minima
    else:
        poupanca_real = poupanca_projetada
        desembolso_mensal = orcamento_alvo
        
    lista_poupanca.append(poupanca_real)
    lista_desembolso_real.append(desembolso_mensal)

df_pre_chaves['Poupança Gerada (R$)'] = lista_poupanca
df_pre_chaves['Desembolso Real do Mês (R$)'] = lista_desembolso_real

st.bar_chart(df_pre_chaves[['Custo Total Mensal (R$)', 'Poupança Gerada (R$)']])
st.divider()

# --- 7. VISÃO DINÂMICA CONSOLIDADA ---
st.subheader("6. Visão Dinâmica Consolidada (Matriz Anual)")

data_inicio = datetime.date(2026, 6, 1)
datas_reais = [data_inicio + pd.DateOffset(months=i) for i in range(int(meses_ate_chaves))]

df_pre_chaves['Data Real'] = datas_reais
df_pre_chaves['Ano'] = df_pre_chaves['Data Real'].dt.year

meses_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
            7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
df_pre_chaves['Mês Nome'] = df_pre_chaves['Data Real'].dt.month.map(meses_pt)

df_visao = df_pre_chaves[['Ano', 'Mês Nome', 'Poupança Gerada (R$)', 'Evolução de Obra (R$)', 'Custo Total Mensal (R$)']]

anos_unicos = df_visao['Ano'].unique()
abas = st.tabs([f"📅 {ano}" for ano in anos_unicos])

for i, ano in enumerate(anos_unicos):
    with abas[i]:
        df_ano = df_visao[df_visao['Ano'] == ano].copy()
        df_ano = df_ano.set_index('Mês Nome')
        df_ano = df_ano.drop(columns=['Ano'])
        
        df_ano.loc['TOTAL DO ANO'] = df_ano.sum()
        
        st.dataframe(
            df_ano.style.format("R$ {:,.2f}")
                        .map(lambda _: 'font-weight: bold; background-color: #1E1E1E;', subset=pd.IndexSlice[['TOTAL DO ANO'], :]),
            use_container_width=True
        )

# --- 8. RESUMO EXECUTIVO ---
st.markdown("---")
st.subheader("📊 Resumo Consolidado do Período de Obras")
col_tot1, col_tot2, col_tot3 = st.columns(3)

total_poupanca_geral = df_pre_chaves['Poupança Gerada (R$)'].sum()
total_eo_geral = df_pre_chaves['Evolução de Obra (R$)'].sum()
total_esforco_caixa = df_pre_chaves['Desembolso Real do Mês (R$)'].sum()

col_tot1.metric("Total Acumulado (Poupança)", f"R$ {total_poupanca_geral:,.2f}")
col_tot2.metric("Total de Evolução de Obra (EO)", f"R$ {total_eo_geral:,.2f}")
col_tot3.metric("Esforço Total de Caixa (Gasto + Poupança)", f"R$ {total_esforco_caixa:,.2f}")


