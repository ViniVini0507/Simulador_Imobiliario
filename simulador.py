import streamlit as st
import pandas as pd
import numpy as np

# Configuração da Página
st.set_page_config(page_title="Simulador de Imóvel na Planta", page_icon="🏢", layout="wide")

st.title("🏢 Simulador de Compra de Imóvel na Planta")
st.markdown("Projete seu fluxo de caixa até a entrega das chaves e o financiamento pós-chaves.")
st.divider()

# 1. Entradas de Dados (Sidebar ou Colunas)
st.header("1. Parâmetros do Negócio")
col1, col2, col3 = st.columns(3)

with col1:
    valor_imovel = st.number_input("Valor Total do Imóvel (R$)", min_value=0.0, value=0.0, step=10000.0)
    entrada_inicial = st.number_input("Valor da Entrada (Aporte Inicial) (R$)", min_value=0.0, value=0.0, step=1000.0)
    itbi_construtora = st.radio("ITBI + Registro pagos pela construtora?", ["Sim", "Não"])

with col2:
    mensal_construtora = st.number_input("Valor da Parcela Mensal (Pré-chaves)", min_value=0.0, value=0.0, step=100.0)
    anual_construtora = st.number_input("Valor da Parcela Anual", min_value=0.0, value=0.0, step=500.0)
    meses_ate_chaves = st.number_input("Meses até a Entrega das Chaves", min_value=1, value=24, step=1)

with col3:
    renda_casal = st.number_input("Renda Líquida Mensal do Casal", min_value=0.0, value=0.0, step=500.0)
    prazo_financiamento = st.number_input("Prazo do Financiamento (Meses)", min_value=1, value=308, step=12)
    taxa_juros_anual = st.number_input("Taxa de Juros Anual do Financiamento (%)", min_value=0.0, value=11.19, step=0.1)
    valor_condominio = st.number_input("Valor do Condomínio", min_value=0.0, value=0.0, step=50.0)

if renda_casal <= 0:
    st.warning("⚠️ Insira a renda líquida mensal do casal para calcular o comprometimento.")

# Cálculos Base O saldo devedor congela no momento do financiamento (assumindo financiamento na planta/crédito associativo)
total_pago_construtora = entrada_inicial + (mensal_construtora * meses_ate_chaves) + (anual_construtora * (meses_ate_chaves // 12))
saldo_devedor_chaves = valor_imovel - total_pago_construtora

# Ajuste cirúrgico: use uma taxa que reflita o custo efetivo total (CET)
# A Caixa costuma aplicar o CET. Se os juros nominais são 9.5%, o CET é maior.
taxa_juros_mensal = (1 + (taxa_juros_anual / 100)) ** (1/12) - 1
# Multiplique por um fator de ajuste (ex: 1.15) para incluir seguros (MIP/DFI) e taxas
taxa_juros_mensal = taxa_juros_mensal * 1.15
juros_maximo_obra = saldo_devedor_chaves * taxa_juros_mensal

# 2. Fluxo de Caixa Pré-Chaves
st.header("2. Fluxo de Caixa Pré-Chaves")

# Teto Conservador = 100% da 1ª Parcela SAC
taxa_ajustada_cet = 0.009521
taxas_fixas_cet = 422.13
amort_mensal_previa = saldo_devedor_chaves / prazo_financiamento
teto_conservador_obra = amort_mensal_previa + (saldo_devedor_chaves * taxa_ajustada_cet) + taxas_fixas_cet

# Ajuste Cirúrgico: Evolução de obra iniciando em Agosto com o valor estimado da sua planilha (R$ 1.479,06)
obra_inicial = 1479.06 
meses = np.arange(1, meses_ate_chaves + 1)

# Inicializa o array de evolução de obra com zeros (Junho e Julho zerados)
evolucao_obra = np.zeros(meses_ate_chaves)

# Preenche com a linha de evolução linear a partir de Agosto (Mês 3)
if meses_ate_chaves > 2:
    evolucao_obra[2:] = np.linspace(obra_inicial, teto_conservador_obra, meses_ate_chaves - 2)

parcelas_mensais = np.full(meses_ate_chaves, mensal_construtora)

# Anual diluída
valor_anual_diluido = anual_construtora / 12
parcelas_anuais_diluidas = np.full(meses_ate_chaves, valor_anual_diluido)

df_pre_chaves = pd.DataFrame({
    'Mês': meses,
    'Parcela Mensal Const. (R$)': parcelas_mensais,
    'Parcela Anual Diluída (R$)': parcelas_anuais_diluidas,
    'Evolução de Obra (R$)': evolucao_obra
}).set_index('Mês')

df_pre_chaves['Custo Total Mensal (R$)'] = df_pre_chaves.sum(axis=1)

st.bar_chart(df_pre_chaves[['Parcela Mensal Const. (R$)', 'Evolução de Obra (R$)', 'Parcela Anual Diluída (R$)']])

col_metric1, col_metric2 = st.columns(2)
col_metric1.metric("Maior parcela na fase de obras (R$)", f"R$ {df_pre_chaves['Custo Total Mensal (R$)'].max():,.2f}")
if itbi_construtora == "Não":
    custo_documentacao = valor_imovel * 0.05 # Estimativa de 5%
    col_metric2.metric("Reserva Extra para Documentação (Estimativa 5%)", f"R$ {custo_documentacao:,.2f}")
else:
    col_metric2.metric("Reserva Extra para Documentação", "Isento (Pago pela Construtora)")

st.divider()

# 3. Projeção SAC Pós-Chaves e Saldo Devedor
st.header("3. Financiamento Pós-Chaves (Tabela SAC)")

amortizacao_mensal = saldo_devedor_chaves / prazo_financiamento
# Dentro do Bloco 3, antes do cálculo da parcela:
custos_fixos_mensais = 25.00 # Taxa de administração média
seguros_estimados = (saldo_devedor_chaves * 0.0005) # Estimativa de custo de seguro sobre saldo

# Ajuste cirúrgico: Cálculo exato da engenharia reversa da Caixa
amortizacao_mensal = saldo_devedor_chaves / prazo_financiamento

taxa_ajustada = 0.009521 # Juros puros da Caixa (aprox. 0.952% a.m.)
taxas_e_seguros_fixos = 422.13 # Valor embutido de Seguros (MIP/DFI) e Taxa de Adm

primeira_parcela_sac = amortizacao_mensal + (saldo_devedor_chaves * taxa_ajustada) + taxas_e_seguros_fixos
ultima_parcela_sac = amortizacao_mensal + (amortizacao_mensal * taxa_ajustada) + taxas_e_seguros_fixos

# Ajuste: Evita divisão por zero se a renda não for preenchida
if renda_casal > 0:
    comprometimento_renda = (primeira_parcela_sac / renda_casal) * 100
else:
    comprometimento_renda = 0
col4, col5, col6 = st.columns(3)
col4.metric("Saldo Devedor a Financiar (R$)", f"R$ {saldo_devedor_chaves:,.2f}")
col5.metric("Primeira Parcela SAC (Aprox.)", f"R$ {primeira_parcela_sac:,.2f}", f"Compromete {comprometimento_renda:.1f}% da renda", delta_color="off")
col6.metric("Última Parcela SAC (Aprox.)", f"R$ {ultima_parcela_sac:,.2f}")

if comprometimento_renda > 30:
    st.warning("⚠️ A primeira parcela compromete mais de 30% da renda líquida informada.")

st.divider()

# 4. Planejamento de Amortização Extraordinária
st.header("4. Planejamento de Amortização Extraordinária")
meta_amortizacao = st.slider("Quanto você deseja abater do saldo devedor nas chaves? (R$)", min_value=0, max_value=int(saldo_devedor_chaves), step=5000, value=50000)

if meta_amortizacao > 0:
    poupanca_mensal_necessaria = meta_amortizacao / meses_ate_chaves
    novo_saldo_devedor = saldo_devedor_chaves - meta_amortizacao
    nova_primeira_parcela = (novo_saldo_devedor / prazo_financiamento) + (novo_saldo_devedor * taxa_juros_mensal)
    
    # Cálculo: Maior parcela de gasto (Mensal + Evolução Máxima) + Poupança
    # Usamos o 'max' para projetar o pior cenário de desembolso mensal durante a obra
    pior_cenario_mensal_obra = df_pre_chaves['Custo Total Mensal (R$)'].max()
    desembolso_maximo_sem_condominio = poupanca_mensal_necessaria + pior_cenario_mensal_obra
    
    st.info(f"💡 Poupança mensal necessária: **R$ {poupanca_mensal_necessaria:,.2f}**")
    
    # Exibição da Parcela Máxima de Gasto (Dívida)
    st.metric("Parcela Máxima de Gasto (Dívida Obra + Poupança)", f"R$ {desembolso_maximo_sem_condominio:,.2f}")
        
    # Alternativa 1: Reduzir Valor da Parcela
    st.success(f"📉 **Alternativa - Reduzir Valor:** Sua primeira parcela SAC cairá de R$ {primeira_parcela_sac:,.2f} para **R$ {nova_primeira_parcela:,.2f}** (mantendo o prazo original).")
    
    # Alternativa 2: Reduzir Prazo
    if amortizacao_mensal > 0:
        parcelas_reduzidas = int(meta_amortizacao / amortizacao_mensal)
        anos_reduzidos = parcelas_reduzidas / 12
        st.success(f"⏳ **Alternativa - Reduzir Prazo:** Esse valor quita aproximadamente **{parcelas_reduzidas} parcelas** (redução de cerca de **{anos_reduzidos:.1f} anos**).")


st.divider()

# 5. Simulação de Orçamento: O 'Squeeze' da Obra
st.divider()
st.subheader("5. Simulação de Orçamento: O 'Squeeze' da Obra")
st.markdown("Estabeleça o teto de gastos do mês. Conforme a evolução de obra 'esmaga' sua margem de poupança, o sistema aumenta automaticamente seu desembolso para garantir a reserva mínima estipulada.")

col7, col8 = st.columns(2)
with col7:
    orcamento_alvo = st.number_input("Orçamento Fixo Mensal (R$)", min_value=1000.0, value=6000.0, step=500.0)
with col8:
    poupanca_minima = st.number_input("Piso Obrigatório de Poupança (R$)", min_value=0.0, value=1500.0, step=100.0)

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
total_gasto_geral = df_pre_chaves['Custo Total Mensal (R$)'].sum()

col_tot1.metric("Total Acumulado (Poupança)", f"R$ {total_poupanca_geral:,.2f}")
col_tot2.metric("Total de Evolução de Obra (EO)", f"R$ {total_eo_geral:,.2f}")
col_tot3.metric("Total Gasto (Obrigações)", f"R$ {total_gasto_geral:,.2f}")




