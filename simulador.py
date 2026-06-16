import streamlit as st
import pandas as pd
import numpy as np

# Configuração da Página
st.set_page_config(page_title="Simulador de Imóvel na Planta", page_icon="🏢", layout="wide")

st.title("🏢 Simulador de Compra de Imóvel na Planta")
st.markdown("Projete seu fluxo de caixa até a entrega das chaves e o financiamento pós-chaves.")
st.divider()

# --- NOVO: SELETOR DE PERFIL (Fica na barra lateral) ---
st.sidebar.header("Configurações Gerais")
perfil = st.sidebar.radio(
    "👤 Selecione o Perfil de Simulação", 
    ["Cenário Vinicius & Ju", "Cenário João & Mari"]
)

# Definindo os valores padrão de acordo com quem está usando o app
if perfil == "Cenário Vinicius & Ju":
    default_imovel = 630000.0
    default_entrada = 40000.0
    default_mensal_const = 1480.0  # Parcela base que você tinha antes
    default_meses_chaves = 30      # Prazo aproximado até o fim de 2028
    default_renda = 14868.0
    opcoes_amortizacao = ["SAC"]
else:
    default_imovel = 437000.0
    default_entrada = 62000.0      # 55k da entrada + 7k de FGTS
    default_mensal_const = 3538.0  # Parcela seca diluindo o GAP de 138k
    default_meses_chaves = 39      # Prazo da obra dele
    default_renda = 7500.0
    opcoes_amortizacao = ["PRICE", "SAC"]

# --- O SEU LAYOUT MANTIDO (Apenas com o 'value' atualizado) ---
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

# Sistema de Pagamento (Dinâmico conforme o perfil)
sistema_amortizacao = st.sidebar.selectbox(
    "Sistema de Amortização",
    opcoes_amortizacao,
    help="SAC: parcelas decrescentes (amortização constante). PRICE: parcelas fixas no início."
)

if renda_casal <= 0:
    st.warning("⚠️ Insira a renda líquida mensal do casal para calcular o comprometimento.")

st.markdown("---")
st.header("2. Análise do Financiamento e Obra")

# --- 3. MOTOR DE CÁLCULO INTERNO ---
taxa_mensal = (taxa_juros_anual / 100) / 12  
saldo_necessario = valor_imovel - entrada_inicial

# Definindo os tetos e a matemática de acordo com o perfil
if perfil == "Cenário João Pedro":
    if sistema_amortizacao == "PRICE":
        saldo_financiado = 298000.00
        # Fórmula PRICE: Parcela Fixa
        parcela_banco_inicial = saldo_financiado * (taxa_mensal * (1 + taxa_mensal)**prazo_financiamento) / ((1 + taxa_mensal)**prazo_financiamento - 1)
    else: 
        # SAC João Pedro
        saldo_financiado = 250000.00
        amortizacao = saldo_financiado / prazo_financiamento
        parcela_banco_inicial = amortizacao + (saldo_financiado * taxa_mensal)
        
    # O João Pedro tem um "Buraco" (GAP) com a construtora que precisa ser diluído nos meses de obra
    gap_construtora = valor_imovel - entrada_inicial - saldo_financiado
    mensal_construtora_calculada = gap_construtora / meses_ate_chaves
    teto_obra = parcela_banco_inicial
    obra_inicial = 100.00 # A EO começa pequena no primeiro mês
    
else:
    # Cenário Vinicius & Ju
    saldo_financiado = saldo_necessario
    amortizacao = saldo_financiado / prazo_financiamento
    parcela_banco_inicial = amortizacao + (saldo_financiado * taxa_mensal)
    
    # Mantém os valores que vocês já preencheram no input
    mensal_construtora_calculada = mensal_construtora 
    teto_obra = parcela_banco_inicial
    obra_inicial = 1480.52 # O valor inicial que já estava na sua tabela

# Exibe o diagnóstico executivo na tela antes do gráfico
col_res1, col_res2, col_res3 = st.columns(3)
col_res1.metric("Saldo Financiado (Banco)", f"R$ {saldo_financiado:,.2f}")

if perfil == "Cenário João Pedro":
    col_res2.metric("GAP Construtora (Buraco)", f"R$ {gap_construtora:,.2f}")
    col_res3.metric("Nova Parcela Const. (Sem INCC)", f"R$ {mensal_construtora_calculada:,.2f}")
else:
    col_res2.metric("Parcela Construtora", f"R$ {mensal_construtora_calculada:,.2f}")
    col_res3.metric("Teto Evolução Obra", f"R$ {teto_obra:,.2f}")
    
st.info(f"💡 A 1ª parcela do financiamento na entrega das chaves ({sistema_amortizacao}) será de **R$ {parcela_banco_inicial:,.2f}**.")

# 3. Financiamento Pós-Chaves (Tabela SAC)
st.header("3. Financiamento Pós-Chaves (Tabela SAC)")

# Ajuste Cirúrgico: Valores exatos já aprovados pela Caixa
primeira_parcela_sac = 8225.12
ultima_parcela_sac = 2109.25

col4, col5, col6 = st.columns(3)
col4.metric("Saldo Devedor a Financiar (R$)", f"R$ {saldo_devedor_chaves:,.2f}")
# Atualizei as legendas para refletir que agora são valores exatos contratuais
col5.metric("Primeira Parcela SAC (Exata)", f"R$ {primeira_parcela_sac:,.2f}")
col6.metric("Última Parcela SAC (Exata)", f"R$ {ultima_parcela_sac:,.2f}")

# Proteção contra divisão por zero (que já havíamos implementado)
if renda_casal > 0:
    comprometimento_renda = (primeira_parcela_sac / renda_casal) * 100
    
    if comprometimento_renda > 30:
        st.warning(f"⚠️ A primeira parcela compromete {comprometimento_renda:.1f}% da renda líquida informada. O limite exigido pelos bancos é 30% da renda bruta.")
    else:
        st.success(f"✅ Comprometimento de renda em {comprometimento_renda:.1f}%.")
else:
    st.info("ℹ️ Insira a renda do casal na Seção 1 para visualizar o comprometimento.")

st.divider()

# 4. Planejamento de Amortização Extraordinária
st.header("4. Planejamento de Amortização Extraordinária")

# O slider usa o saldo devedor calculado na Seção 1
meta_amortizacao = st.slider("Quanto você deseja abater do saldo devedor nas chaves? (R$)", min_value=0, max_value=int(saldo_devedor_chaves), step=5000, value=50000)

if meta_amortizacao > 0:
    # Correção: Recriando a variável de amortização constante (SAC)
    amortizacao_mensal = saldo_devedor_chaves / prazo_financiamento
    
    # Recálculo preciso da nova parcela reduzida usando o valor cravado da Caixa
    taxa_juros_mensal = 0.009521 # Taxa de juros mensal aproximada (CET)
    reducao_parcela = (meta_amortizacao / prazo_financiamento) + (meta_amortizacao * taxa_juros_mensal)
    nova_primeira_parcela = primeira_parcela_sac - reducao_parcela
    
    # Alternativa 1: Reduzir Valor da Parcela
    st.success(f"📉 **Alternativa - Reduzir Valor:** Sua primeira parcela SAC cairá de R$ {primeira_parcela_sac:,.2f} para **R$ {nova_primeira_parcela:,.2f}** (mantendo o prazo original).")
    
    # Alternativa 2: Reduzir Prazo
    if amortizacao_mensal > 0:
        parcelas_reduzidas = int(meta_amortizacao / amortizacao_mensal)
        anos_reduzidos = parcelas_reduzidas / 12
        st.success(f"⏳ **Alternativa - Reduzir Prazo:** Esse valor quita aproximadamente **{parcelas_reduzidas} parcelas** (redução de cerca de **{anos_reduzidos:.1f} anos**).")
        
st.divider()

# 5. Simulação de Orçamento: Poupança x Obra
st.subheader("5. Simulação de Orçamento: Poupança x Obra")
st.markdown("Estabeleça o teto de gastos do mês. Conforme a evolução de obra 'esmaga' sua margem de poupança, o sistema aumenta automaticamente seu desembolso para garantir a reserva mínima estipulada.")

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

# 6. Visão Dinâmica Consolidada (Matriz Anual)
st.divider()
st.subheader("6. Visão Dinâmica Consolidada (Matriz Anual)")
st.markdown("Projeção de fluxo de caixa mês a mês agrupada por ano, espelhando o controle executivo.")

import datetime
data_inicio = datetime.date(2026, 6, 1)
datas_reais = [data_inicio + pd.DateOffset(months=i) for i in range(meses_ate_chaves)]

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

# Painel unificado com os 3 grandes totais acumulados do período
st.markdown("---")
st.subheader("📊 Resumo Consolidado do Período de Obras")
col_tot1, col_tot2, col_tot3 = st.columns(3)

total_poupanca_geral = df_pre_chaves['Poupança Gerada (R$)'].sum()
total_eo_geral = df_pre_chaves['Evolução de Obra (R$)'].sum()

# Ajuste Cirúrgico: Somando tudo para mostrar o Esforço Total de Caixa do período
total_esforco_caixa = df_pre_chaves['Desembolso Real do Mês (R$)'].sum()

col_tot1.metric("Total Acumulado (Poupança)", f"R$ {total_poupanca_geral:,.2f}")
col_tot2.metric("Total de Evolução de Obra (EO)", f"R$ {total_eo_geral:,.2f}")
col_tot3.metric("Esforço Total de Caixa (Gasto + Poupança)", f"R$ {total_esforco_caixa:,.2f}")




