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
    st.warning("⚠️ Por favor, insira a renda líquida mensal do casal para calcular o comprometimento.")

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

# Ajuste: Evolução de obra começando em 15% (R$ 1.223)
obra_inicial = 1223.0
meses = np.arange(1, meses_ate_chaves + 1)
evolucao_obra = np.linspace(obra_inicial, juros_maximo_obra, meses_ate_chaves)
parcelas_mensais = np.full(meses_ate_chaves, mensal_construtora)

# Ajuste: Anual diluída mensalmente (valor total anual / 12) distribuída em todos os meses
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
    st.warning("⚠️ A primeira parcela compromete mais de 30% da renda líquida informada. O banco pode exigir uma entrada maior ou aprovar um valor menor de financiamento.")

st.divider()

# 4. Meta de Poupança para Amortização Extraordinária
st.header("4. Planejamento de Amortização Extraordinária")
st.markdown("Crie um fundo de reserva durante o período de obras para reduzir o saldo devedor logo após a entrega das chaves.")

meta_amortizacao = st.slider("Quanto você deseja abater do saldo devedor nas chaves? (R$)", min_value=0, max_value=int(saldo_devedor_chaves), step=5000, value=50000)

if meta_amortizacao > 0:
    poupanca_mensal_necessaria = meta_amortizacao / meses_ate_chaves
    novo_saldo_devedor = saldo_devedor_chaves - meta_amortizacao
    nova_primeira_parcela = (novo_saldo_devedor / prazo_financiamento) + (novo_saldo_devedor * taxa_juros_mensal)

    # Cálculo da média de desembolso
    # Ajuste: inclusão do " (R$)" no nome da coluna
    media_gasto_obrigatorio = df_pre_chaves['Custo Total Mensal (R$)'].mean()
    desembolso_mensal_total = poupanca_mensal_necessaria + media_gasto_obrigatorio + valor_condominio

    st.info(f"💡 Poupança mensal necessária: **R$ {poupanca_mensal_necessaria:,.2f}**")

    # Exibição da nova média
    st.metric("Desembolso Mensal Médio (Gasto Obrigatório + Poupança + Condomínio)", f"R$ {desembolso_mensal_total:,.2f}")

    st.success(f"📉 Impacto: Sua primeira parcela SAC cairá de R$ {primeira_parcela_sac:,.2f} para R$ {nova_primeira_parcela:,.2f} com este aporte.")
